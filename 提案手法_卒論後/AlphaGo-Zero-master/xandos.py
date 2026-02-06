import numpy as np 


class xandos():

	def __init__(self):
		self._num_actions = 10
		self.num_actions = 9
		self._num_actions = 9
		self.starting_board = np.zeros((3, 3)) * -1
		self.board_width = 3
		self.board_height = 3

	def hash(self, board):
		return hash(board.tostring())

	def next_state(self, board, action=None, player=None):
		board = board.flatten()
		board[action] = 1
		player = 1 if player == 2 else 2
		return board.reshape((3, 3))*-1, player

	def _get_valid_moves(self, board):
		return np.isin(np.append(board.flatten(), 1), 0)

	def get_valid_moves(self, board):
		return np.isin(board.flatten(), 0)

	def print_board(self, board):
		print(( " {} | {} | {} \n"
				"-----------------\n"
				" {} | {} | {} \n"
				"-----------------\n"
				" {} | {} | {} \n\n").format(*board.flatten()))


	def get_symmetries_(self, board, pi):
		# use this if using a fully connected network
		boards_pis = []
		board = board.flatten()
		pass_bit = pi[-1]
		pi = pi[:-1]
		
		for _ in range(2):
			for _ in range(4):
				boards_pis.append((board, np.append(pi, pass_bit)))
				board = np.rot90(board.reshape((3, 3))).flatten()
				pi = np.rot90(pi.reshape((3, 3))).flatten()

			board = np.flip(board.reshape((3, 3)), 1).flatten()
			pi = np.flip(pi.reshape((3, 3)), 1).flatten()

		return boards_pis

	def get_symmetries(self, board, pi):
		boards_pis = []
		
		for _ in range(2):
			for _ in range(4):
				boards_pis.append((board, pi))
				board = np.rot90(board)
				pi = np.rot90(pi.reshape((3, 3))).flatten()

			board = np.flip(board, 1)
			pi = np.flip(pi.reshape((3, 3)), 1).flatten()

		return boards_pis


	def reward(self, board):
		test_board = board.reshape((3, 3))

		for _ in range(2):
			for row in test_board:
				if np.all(row == -1):
					return -1

			if np.all(np.diagonal(test_board) == -1):
				return -1

			test_board = np.rot90(test_board)
		
		if 0 not in test_board and -0 not in test_board:
			return 0

		return -999
