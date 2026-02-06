"""
ぷよぷよ環境（AlphaGo Zero用）
C++環境をPythonでラップして自己対戦を実現
"""
import numpy as np
import subprocess
import json
import os

class PuyoPuyoGame:
    def __init__(self):
        self.board_height = 14
        self.board_width = 6
        self.num_actions = 24  # 6列 × 4方向
        self.starting_board = np.zeros((self.board_height, self.board_width), dtype=np.int8)
        
        # C++実行ファイルのパス
        self.cpp_executable = "../Alpha-ojyama/build/puyop"
    
    def hash(self, board):
        """盤面のハッシュ値を返す"""
        return hash(board.tobytes())
    
    def get_valid_moves(self, board):
        """
        有効な手のマスクを返す
        C++のmove:: generate()と同等の処理
        """
        valid = np.zeros(self.num_actions, dtype=bool)
        
        # 簡易版: 各列の高さをチェック
        for x in range(6):
            height = self._get_column_height(board, x)
            
            # UP方向（縦置き）
            if height <= 11:
                valid[x + 0 * 6] = True
            
            # RIGHT方向（右に横置き）
            if x < 5 and height <= 11:
                valid[x + 1 * 6] = True
            
            # DOWN方向（上下逆）
            if height <= 11:
                valid[x + 2 * 6] = True
            
            # LEFT方向（左に横置き）
            if x > 0 and height <= 11:
                valid[x + 3 * 6] = True
        
        return valid
    
    def next_state(self, board, action, player=1, current_pair=None):
        """
        行動実行後の次の状態を返す
        
        引数: 
            board: 現在の盤面 (14, 6)
            action: 行動ID (0-23)
            player: プレイヤー番号（使用しない）
            current_pair: (color1, color2) のタプル
        
        返り値:
            next_board: 次の盤面
            next_player: 次のプレイヤー（常に1）
        """
        # actionを(x, direction)に変換
        x = action % 6
        direction = action // 6
        
        # 新しい盤面を作成
        next_board = board.copy()
        
        # ぷよを落とす（簡易シミュレーション）
        if current_pair is None:
            current_pair = (np.random.randint(1, 5), np.random.randint(1, 5))
        
        # 配置シミュレーション
        if direction == 0:  # UP（縦置き）
            y = self._find_drop_position(next_board, x)
            if y >= 1:
                next_board[y, x] = current_pair[0]
                next_board[y-1, x] = current_pair[1]
        elif direction == 1:  # RIGHT（右に横置き）
            if x < 5:
                y1 = self._find_drop_position(next_board, x)
                y2 = self._find_drop_position(next_board, x + 1)
                next_board[y1, x] = current_pair[0]
                next_board[y2, x + 1] = current_pair[1]
        elif direction == 2:  # DOWN（上下逆）
            y = self._find_drop_position(next_board, x)
            if y >= 1:
                next_board[y, x] = current_pair[1]
                next_board[y-1, x] = current_pair[0]
        elif direction == 3:  # LEFT（左に横置き）
            if x > 0:
                y1 = self._find_drop_position(next_board, x)
                y2 = self._find_drop_position(next_board, x - 1)
                next_board[y1, x] = current_pair[0]
                next_board[y2, x - 1] = current_pair[1]
        
        # 連鎖処理（簡易版）
        next_board = self._simple_chain(next_board)
        
        return next_board, 1
    
    def reward(self, board):
        """
        ゲーム終了判定と報酬
        
        返り値:
            -999: ゲーム継続中
            -1: ゲームオーバー（負け）
            1: （未使用、ぷよぷよは勝敗がないため）
        """
        # 中央列（x=2）の高さが12以上でゲームオーバー
        center_height = self._get_column_height(board, 2)
        if center_height > 11:
            return -1  # 負け
        
        return -999  # ゲーム継続
    
    def get_symmetries(self, board, pi):
        """
        データ拡張:  左右反転
        
        返り値:
            [(board, pi), (board_flipped, pi_flipped)]
        """
        symmetries = [(board, pi)]
        
        # 左右反転
        board_flipped = np.fliplr(board)
        pi_flipped = np.zeros_like(pi)
        
        for action in range(self.num_actions):
            x = action % 6
            d = action // 6
            
            # 列を反転
            x_new = 5 - x
            
            # LEFT↔RIGHT方向を入れ替え
            if d == 1:  # RIGHT → LEFT
                d_new = 3
            elif d == 3:  # LEFT → RIGHT
                d_new = 1
            else:  # UP, DOWNはそのまま
                d_new = d
            
            action_new = x_new + d_new * 6
            pi_flipped[action_new] = pi[action]
        
        symmetries.append((board_flipped, pi_flipped))
        return symmetries
    
    def _get_column_height(self, board, x):
        """列xの高さを返す"""
        for y in range(self.board_height):
            if board[y, x] != 0:
                return self.board_height - y
        return 0
    
    def _find_drop_position(self, board, x):
        """列xでぷよが落ちる位置を返す（下から見た高さ）"""
        for y in range(self.board_height - 1, -1, -1):
            if board[y, x] == 0:
                return y
        return -1
    
    def _simple_chain(self, board):
        """
        簡易連鎖処理
        4つ以上つながったぷよを消す
        
        ⚠️ 注意:  実際のC++実装（field.cpp）とは異なる簡易版
        正確な連鎖計算はC++側で行う
        """
        # TODO: 本格的な連鎖処理（後で実装）
        # 現状は簡易版のまま学習を進める
        return board