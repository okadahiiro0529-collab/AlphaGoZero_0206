"""
ぷよぷよ環境（C++バックエンド版）
ama AIと同じC++エンジンを使用
"""
import numpy as np
import subprocess
import os

class PuyoPuyoGame:
    def __init__(self):
        self.board_height = 14
        self.board_width = 6
        self.num_actions = 24  # 6列 × 4方向
        self.starting_board = np.zeros((self.board_height, self.board_width), dtype=np.int8)
        self.current_score = 0
        
        # C++シミュレータのパス
        self.simulator_path = os.path.abspath("../Alpha-ojyama/bin/puyop/puyop_simulator.exe")
        
        # 一時ファイル用ディレクトリ
        self.temp_dir = "C:/temp/puyo_sim"
        os.makedirs(self.temp_dir, exist_ok=True)
        
        print(f"[INFO] C++ Simulator:  {self.simulator_path}")
        print(f"[INFO] Exists: {os.path.exists(self.simulator_path)}")
    
    def hash(self, board):
        """盤面のハッシュ値を返す"""
        return hash(board.tobytes())
    
    def reset(self):
        """ゲームをリセット"""
        self.current_score = 0
        return self.starting_board.copy()
    
    def get_valid_moves(self, board):
        """有効な手のマスクを返す"""
        valid = np.zeros(self.num_actions, dtype=bool)
        
        for x in range(6):
            height = self._get_column_height(board, x)
            
            # UP, DOWN:  高さが12以下
            if height <= 11:
                valid[x + 0 * 6] = True  # UP
                valid[x + 2 * 6] = True  # DOWN
            
            # RIGHT:  右隣も確認
            if x < 5 and height <= 11:
                right_height = self._get_column_height(board, x + 1)
                if right_height <= 11:
                    valid[x + 1 * 6] = True
            
            # LEFT:   左隣も確認
            if x > 0 and height <= 11:
                left_height = self._get_column_height(board, x - 1)
                if left_height <= 11:
                    valid[x + 3 * 6] = True
        
        return valid
    
    def next_state(self, board, action, player=1, current_pair=None):
        """
        C++シミュレータを使って次の状態を計算
        """
        # actionを(x, direction)に変換
        x = action % 6
        r = action // 6
        
        # ぷよペアがなければランダム生成
        if current_pair is None:
            # 1=RED, 2=GREEN, 3=BLUE, 4=YELLOW
            current_pair = (np.random.randint(1, 5), np.random.randint(1, 5))
        
        # 一時ファイルパス
        input_file = os.path.join(self.temp_dir, f"input_{os.getpid()}.txt")
        output_field_file = os.path.join(self.temp_dir, f"output_field_{os.getpid()}.txt")
        output_result_file = os.path.join(self.temp_dir, f"output_result_{os.getpid()}.txt")
        
        # 盤面を保存
        np.savetxt(input_file, board, fmt='%d', delimiter=',')
        
        # C++シミュレータを呼び出し
        cmd = [
            self.simulator_path,
            input_file,
            str(x),
            str(r),
            str(current_pair[0]),
            str(current_pair[1]),
            output_field_file,
            output_result_file
        ]
        
        try:
            result = subprocess.run(cmd, check=True, capture_output=True, timeout=5)
        except subprocess.TimeoutExpired:
            print(f"[ERROR] C++ Simulator timeout")
            return board, 1
        except Exception as e:
            print(f"[ERROR] C++ Simulator failed: {e}")
            return board, 1
        
        # 結果を読み込み
        try:
            next_board = np.loadtxt(output_field_file, delimiter=',', dtype=np.int8)
            
            with open(output_result_file, 'r') as f:
                lines = f.readlines()
                score = int(lines[0].strip())
                chain_count = int(lines[1].strip())
                game_over = int(lines[2].strip())
            
            self.current_score += score
            
            # クリーンアップ
            os. remove(input_file)
            os.remove(output_field_file)
            os.remove(output_result_file)
            
            return next_board, 1
        except Exception as e:
            print(f"[ERROR] Failed to read result: {e}")
            return board, 1
    
    def reward(self, board):
        """
        ゲーム終了判定
        
        返り値:  
            -999:   ゲーム継続中
            その他: ゲーム終了
        """
        center_height = self._get_column_height(board, 2)
        if center_height > 11:
            return -1  # ゲームオーバー
        
        return -999  # 継続
    
    def get_symmetries(self, board, pi):
        """データ拡張:    左右反転"""
        symmetries = [(board, pi)]
        
        # 左右反転
        board_flipped = np.fliplr(board)
        pi_flipped = np.zeros_like(pi)
        
        for action in range(self.num_actions):
            x = action % 6
            d = action // 6
            
            x_new = 5 - x
            
            if d == 1:  # RIGHT → LEFT
                d_new = 3
            elif d == 3:  # LEFT → RIGHT
                d_new = 1
            else:  
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