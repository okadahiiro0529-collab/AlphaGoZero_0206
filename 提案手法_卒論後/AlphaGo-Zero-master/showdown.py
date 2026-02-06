import torch

import model
from mcts import MCTS
from xandos import xandos
from connect4 import Connect4


class ShowDown():

	def __init__(self, game, player1, player2):
		
		if game == 'connect4':
			self.game = Connect4(board_width=7, board_height=6, win_crit=4)
			self.nnet_class = model.C4Net_6x7
		elif game == 'connect3':
			self.game = Connect4(board_width=5, board_height=5, win_crit=3)
			self.nnet_class = model.C4Net_5x5
		else:
			self.game = Xandos()
			self.nnet_class = model.XandosNet

		game_name = game if game == 'Xandos' else 'Connect4'
		filepath = './models/{}_{}.pth.tar'

		player_type, player_idx = player1
		if player_type == 'human':
			self.player1 = self.human_player
		else:
			nnet1 = self.nnet_class(num_inputs=self.game.starting_board.size, num_actions=self.game.num_actions)
			nnet1.load_state_dict(torch.load(filepath.format(game_name, player_idx)))
			mcts = MCTS(game=self.game, net=nnet1)
			self.player1 = mcts.choose_action

		player_type, player_idx = player2
		if player_type == 'human':
			self.player2 = self.human_player
		else:
			nnet2 = self.nnet_class(num_inputs=self.game.starting_board.size, num_actions=self.game.num_actions)
			nnet2.load_state_dict(torch.load(filepath.format(game_name, player_idx)))
			mcts = MCTS(game=self.game, net=nnet2)
			self.player2 = mcts.choose_action

	def single_match(self):

		curr_player = self.player1
		curr_player_num = 1
		
		state = self.game.starting_board
		
		while True:
			
			print()
			self.game.print_board(state)
			action = curr_player(state)

			state, curr_player_num = self.game.next_state(state, action, curr_player_num)
			reward = self.game.reward(state)
			curr_player = self.player2 if curr_player == self.player1 else self.player1

			if reward != -999:
				print()
				self.game.print_board(state)
				if reward == 0:
					print('\nIt\'s a draw!')
				else:
					print('\nGame over! The loser is player ', curr_player_num)
				break

	
	def human_player(self, state):
		valid_moves = self.game.get_valid_moves(state)

		while True:
			move = input('Enter move: ')
			try:
				move = int(move)
			except ValueError:
				pass
			else:
				if valid_moves[move]:
					return move
			print('Invalid move, try again!')


if __name__ == "__main__":


	ai = ('ai', 11)
	hu = ('human', None)
	aa = ('ai', 3)
	game = 'connect4'

	showdown = ShowDown(game, ai, aa)
	while True:
		showdown.single_match()

		play_again = input('\nplay again?[y/n]')
		if play_again.lower() != 'y':
			break
