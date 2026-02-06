"""
ぷよぷよ環境（シンプルなおじゃまスケジュール）
"""
import numpy as np
import subprocess
import os
import time 

class PuyoPuyoGame: 
    def __init__(self):
        self.board_height = 14
        self.board_width = 6
        self.num_actions = 24
        self.starting_board = np.zeros((self.board_height, self.board_width), dtype=np.int8)
        
        self.simulator_path = r"C:\Users\h.okada\OneDrive - NITech\ドキュメント\研究室\ama\提案手法\Alpha-ojyama\bin\puyop\puyop_simulator.exe"
        self.temp_dir = "C:/temp/puyo_sim"
        
        if os.path.exists(self.temp_dir):
            import shutil
            shutil.rmtree(self.temp_dir)
        os.makedirs(self.temp_dir, exist_ok=True)
        
        if not os.path.exists(self.simulator_path):
            raise FileNotFoundError(f"Simulator not found:   {self.simulator_path}")
        
        print(f"[INFO] C++ Simulator:   {self.simulator_path}")
        print(f"[INFO] Simulator found")
        
        self.garbage_schedule = []
        self.move_count = 0
    
    def reset_garbage_schedule(self):
        """おじゃまぷよスケジュールを初期化（最初の1つだけ）"""
        self.garbage_schedule = []
        self.move_count = 0
        
        init_delay = np.random.randint(3, 6)
        init_count = np.random.randint(1, 4)
        self.garbage_schedule.append({
            'due_move': init_delay,
            'count': init_count
        })
    
    def schedule_next_garbage(self):
        """
        次のおじゃまぷよをスケジュール（正確に「現在のmove_count+3～5」手後のみ」
        すでに同じmove_countにスケジュールが載っていれば追記しない
        """
        # 現在のmove_count基準で3-5手後に必ず入れる
        next_delay = np.random.randint(3, 6)  # 3,4,5
        next_due = self.move_count + next_delay

        # すでに同じdue_moveがあれば何もしない（重複防止）
        for s in self.garbage_schedule:
            if s['due_move'] == next_due:
                return
        if next_due < 100:
            next_count = np.random.randint(1, 4)
            self.garbage_schedule.append({
                'due_move': next_due,
                'count': next_count
            })
    
    def should_drop_garbage(self):
        """現在の手でおじゃまぷよを降らせるか判定"""
        for scheduled in self.garbage_schedule:
            if scheduled['due_move'] == self.move_count:
                return True, scheduled['count']
        return False, 0
    
    def hash(self, board):
        return hash(board.tobytes())
    
    def reset(self):
        """エピソード開始"""
        self.reset_garbage_schedule()
        return self.starting_board.copy()
    
    def get_valid_moves(self, board):
        valid = np.zeros(self.num_actions, dtype=bool)
        for x in range(6):
            height = self._get_column_height(board, x)
            # タテ置き
            if height <= 11: 
                valid[x + 0 * 6] = True     # rotation=0
                valid[x + 2 * 6] = True     # rotation=2
            # ヨコ置き（右回転：左側が下）
            if x < 5:
                right_height = self._get_column_height(board, x + 1)
                if height <= 11 and right_height <= 11:
                    valid[x + 1 * 6] = True  # rotation=1 (右回転)
            # ヨコ置き（左回転：右側が下）
            if x > 0:
                left_height = self._get_column_height(board, x - 1)
                if height <= 11 and left_height <= 11:
                    valid[x + 3 * 6] = True  # rotation=3 (左回転)
        # 物理的にはみ出す手を「絶対無効」に
        valid[0 + 3 * 6] = False  # x=0, rotation=3（左端＋左回転）
        valid[5 + 1 * 6] = False  # x=5, rotation=1（右端＋右回転）
        return valid
    
    def next_state(self, board, action, player=1, current_pair=None, is_simulation=False):
        """
        次の状態を計算
        
        Returns:
            next_board, player, score, chains, garbage_columns
        """
        x = action % 6
        r = action // 6
        
        if current_pair is None:
            current_pair = (np.random.randint(1, 5), np.random.randint(1, 5))
        
        pid = os.getpid()
        timestamp = int(time.time() * 1000000) + np.random.randint(0, 99999)
        
        input_file = os.path.join(self.temp_dir, f"input_{pid}_{timestamp}.txt")
        output_field_file = os.path.join(self.temp_dir, f"output_field_{pid}_{timestamp}.txt")
        output_result_file = os.path.join(self.temp_dir, f"output_result_{pid}_{timestamp}.txt")
        
        for f in [input_file, output_field_file, output_result_file]:
            if os.path.exists(f):
                os.remove(f)
        
        np.savetxt(input_file, board, fmt='%d', delimiter=',')
        
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
            subprocess.run(cmd, check=True, capture_output=True, timeout=5)
        except Exception as e:
            print(f"[ERROR] Simulator failed: {e}", flush=True)
            return board, 1, 0, 0, []
        
        max_wait = 100
        wait_count = 0
        while not os.path.exists(output_result_file) and wait_count < max_wait:
            time.sleep(0.01)
            wait_count += 1
        
        if not os.path.exists(output_result_file):
            print(f"[ERROR] Result file not created", flush=True)
            return board, 1, 0, 0, []
        
        try:
            next_board = np.loadtxt(output_field_file, delimiter=',', dtype=np.int8)
            
            with open(output_result_file, 'r') as f:
                lines = f.readlines()
                score = int(lines[0].strip())
                chain_count = int(lines[1].strip())

            # 1. ぷよ設置後に即ゲームオーバーかチェック
            center_height = self._get_column_height(next_board, 2)
            if center_height >= 12:
                # ゲームオーバーならおじゃまぷよ処理せず、即return
                try:
                    os.remove(input_file)
                    os.remove(output_field_file)
                    os.remove(output_result_file)
                except:
                    pass
                # garbage_columnsは空で返す
                return next_board, 1, score, chain_count, []
            
            # 2. ゲームオーバーでなければ、おじゃまぷよ処理を通常通り行う
            garbage_columns = []
            
            if not is_simulation:
                # "設置またはおじゃま降下"ごとにmove_count++にする必要あり
                self.move_count += 1
                
                should_drop, garbage_count = self.should_drop_garbage()
                if should_drop:
                    # 異なる列をランダムに選択
                    # garbageをここで降下させる
                    available_cols = list(range(6))
                    np.random.shuffle(available_cols)
                    
                    selected_cols = available_cols[:min(garbage_count, 6)]
                    
                    for col in selected_cols:
                        height = self._get_column_height(next_board, col)
                        if height < 13:
                            next_board[height, col] = 6
                            garbage_columns.append(col)
                    
                    # ⭐ move_count管理を全て「加算後」に
                    self.move_count += 1  # 「おじゃまが降りる」ごとにも +1
                    # 最新のmove_countでdue_move==move_countなら削除
                    self.garbage_schedule = [s for s in self.garbage_schedule if s['due_move'] != self.move_count]
                    # スケジューリングも今進んだmove_count基準に
                    self.schedule_next_garbage()
            
            try:
                os.remove(input_file)
                os.remove(output_field_file)
                os.remove(output_result_file)
            except:
                pass

            return next_board, 1, score, chain_count, garbage_columns
        except Exception as e:
            print(f"[ERROR] Failed to read result:  {e}", flush=True)
            return board, 1, 0, 0, []
    
    def reward(self, board, last_garbage_cols=None, placed_positions=None):
        """
        ゲームオーバー種別を返す
        Returns:
            - Tuple: (終局か, 自爆か, おじゃまか, 手数)
        """
        center_height = self._get_column_height(board, 2)
        if center_height >= 12:
            # おじゃま原因
            garbage_place = bool(last_garbage_cols and 2 in last_garbage_cols)
            # そのターンx=2, y>=11に設置した場合、自分設置扱い
            your_place = False
            if placed_positions is not None:
                for x, y in placed_positions:
                    if x == 2 and y >= 11:
                        your_place = True
                        break
            # 安全ガード
            if not garbage_place and not your_place:
                your_place = True
            return (-1, your_place, garbage_place, self.move_count)
        return (-999, False, False, self.move_count)
    
    def reward_scalar(self, board):
        """
        MCTS用：数値だけ返す（従来通りゲームオーバーで-1/継続で-999）
        """
        center_height = self._get_column_height(board, 2)
        if center_height >= 12:
            return -1
        return -999
    
    def get_symmetries(self, board, pi):
        """盤面の対称性を取得"""
        symmetries = [(board, pi)]
        
        board_flipped = np.fliplr(board)
        pi_flipped = np.zeros_like(pi)
        
        for action in range(self.num_actions):
            x = action % 6
            d = action // 6
            x_new = 5 - x
            
            if d == 1:
                d_new = 3
            elif d == 3:
                d_new = 1
            else:
                d_new = d
            
            action_new = x_new + d_new * 6
            pi_flipped[action_new] = pi[action]
        
        symmetries.append((board_flipped, pi_flipped))
        return symmetries
    
    def _get_column_height(self, board, x):
        """列の高さを計算"""
        for y in range(self.board_height - 1, -1, -1):
            if board[y, x] != 0:
                return y + 1
        return 0