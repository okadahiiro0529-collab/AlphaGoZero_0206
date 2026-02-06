from collections import defaultdict

import numpy as np
import torch


class MCTS():

	def __init__(self, game=None, net=None, num_actions=None, num_sims=25, c_puct=1):
		self.game = game
		self.num_actions = self.game.num_actions
		self.N = defaultdict(lambda: defaultdict(int))
		self.Q = defaultdict(lambda: defaultdict(int))
		self.P = defaultdict(np.array)
		self.tree = []
		self.terminal_states = {}
		self.c_puct = c_puct
		self.num_sims = num_sims
		self.nnet = net
		self.max_depth = 50


	def get_action_probabilities(self, state, t=0):
		state_id = self.game.hash(state)
		counts = [self.N[state_id][action] for action in range(self.num_actions)]
		
		if t == 0:
			move_probs = np.zeros(self.num_actions)
			if sum(counts) > 0:
				move_probs[np.argmax(counts)] = 1.0
			else:
				move_probs = np.ones(self.num_actions) / self.num_actions
		else:
			counts_arr = np.array(counts, dtype=np.float64)
			if np.sum(counts_arr) > 0:
				powered = counts_arr ** (1.0 / t)
				sum_powered = np.sum(powered)
				if sum_powered > 0:
					move_probs = powered / sum_powered
				else:
					move_probs = np.ones(self.num_actions) / self.num_actions
			else:
				move_probs = np.ones(self.num_actions) / self.num_actions
		
		if np.any(np.isnan(move_probs)) or np.sum(move_probs) == 0:
			print(f"[WARNING] Invalid move_probs, using uniform distribution")
			move_probs = np.ones(self.num_actions) / self.num_actions

		return move_probs

	
	def choose_action(self, state):
		for _ in range(self.num_sims):
			self.search(state.copy())
		
		pi = self.get_action_probabilities(state)
		action = np.random.choice(self.num_actions, p=pi)
		
		return action


	def U(self, state_id, action):
		n_factor = np.sqrt(sum((b + 1e-8) for k, b in self.N[state_id].items())) / (self.N[state_id][action] + 1)
		return self.Q[state_id][action] + self.c_puct * self.P[state_id][action]*(n_factor)
		


	def search(self, state, depth=0):
		state_id = self.game.hash(state)

		if depth > self.max_depth:
			return 0.0
    
		##################
		# Terminal nodes #
		##################
		
		if state_id in self.terminal_states:
			return self.terminal_states[state_id]
		
		reward = self.game.reward_scalar(state)
		if reward != -999:
			self.terminal_states[state_id] = -reward
			return -reward
		
		##############
		# leaf nodes #
		##############
		
		if state_id not in self.tree:
			self.tree.append(state_id)
			{self.Q[state_id][action]:  0 for action in range(self.num_actions)}
			{self.N[state_id][action]: 0 for action in range(self.num_actions)}
			
			pi, v = self.nnet(torch.FloatTensor(state).view(1, 1, self.game.board_height, self.game.board_width))
			pi, v = pi.data.numpy()[0], v.data.numpy()[0][0]
			
			valid_moves = self.game.get_valid_moves(state)
			
			if not valid_moves.any():
				self.terminal_states[state_id] = -1.0
				return -1.0
			
			self.P[state_id] = pi * valid_moves
			
			if self.P[state_id].sum() > 0:
				self.P[state_id] = self.P[state_id] / self.P[state_id].sum()
			else:
				self.P[state_id] = valid_moves.astype(float) / valid_moves.sum()
			
			return -v
		
		##################
		# explored nodes #
		##################
		
		valid_moves = self.game.get_valid_moves(state)
		
		if not valid_moves.any():
			self.terminal_states[state_id] = -1.0
			return -1.0
		
		best_action = None
		best_ucb = -float('inf')
		
		for action in range(self.num_actions):
			if valid_moves[action]: 
				ucb = self.U(state_id, action)
				if ucb > best_ucb:
					best_ucb = ucb
					best_action = action
		
		if best_action is None:
			self.terminal_states[state_id] = -1.0
			return -1.0
		
		# ⭐ シミュレーションモードでnext_stateを呼ぶ
		next_state, _, _, _, _ = self.game.next_state(state.copy(), action=best_action, is_simulation=True)
		
		next_state_id = self.game.hash(next_state)
		if next_state_id == state_id:
			self.terminal_states[state_id] = -1.0
			return -1.0
		
		v = self.search(next_state, depth=depth+1)
		
		self.Q[state_id][best_action] = (
			self.N[state_id][best_action] * self.Q[state_id][best_action] + v
		) / (self.N[state_id][best_action] + 1)
		self.N[state_id][best_action] += 1
		
		return -v