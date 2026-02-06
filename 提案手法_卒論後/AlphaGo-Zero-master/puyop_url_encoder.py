"""
Puyop URL Encoder (encode.h互換版/コントロールペア＆ガーベージ含む)
"""

class PuyopURLEncoder:
    CHAR = "0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ[]"

    def __init__(self):
        self.moves = []
        self.base_url = "http://www.puyop.com/s/_"
    
    def reset(self):
        self.moves = []

    def add_move(self, x, rotation, color1, color2):
        # 通常のペアを記録
        self.moves.append({
            'type': 'pair',
            'x': x,
            'rotation': rotation,
            'color1': color1,  # 1=RED, 2=GREEN, 3=BLUE, 4=YELLOW, 5=GARBAGE
            'color2': color2,
        })
    
    def add_garbage_columns(self, columns):
        # 複数同時降下
        if len(columns) == 0:
            return
        self.moves.append({
            'type': 'garbage',
            'columns': columns[:],  # 必ずコピー
        })

    def _encode_pair_move(self, x, rotation, color1, color2):
        # 色IDの変換
        c1 = self._get_cell_id(color1)
        c2 = self._get_cell_id(color2)
        pair_code = c1 * 5 + c2
        placement_code = ((x + 1) << 2) + rotation  # (x+1)*4 + rotation
        code = pair_code | (placement_code << 7)
        s1 = self.CHAR[code & 0x3F]
        s2 = self.CHAR[(code >> 6) & 0x3F]
        return s1 + s2

    def generate_url(self):
        encoded = self.base_url

        i = 0
        n = len(self.moves)
        while i < n:
            move = self.moves[i]
            # === ガーベージ降下のencode.hの振る舞い ===
            if move['type'] == 'garbage':
                cols = move['columns']
                # 連続ガーベージ降下をrunでまとめる
                counts = [0]*6
                for c in cols:
                    if c < 0: c = 0
                    if c > 5: c = 5
                    counts[c] += 1

                while any(counts):
                    mask = 0
                    for ci in range(6):
                        if counts[ci] > 0:
                            mask |= (1 << ci)
                    encoded += self.CHAR[mask & 0x3F] + 'U'
                    for ci in range(6):
                        if counts[ci] > 0:
                            counts[ci] -= 1
                i += 1
                continue

            # Safety: NONE→GARBAGE変換（C++ fallback）
            color1 = move['color1']
            color2 = move['color2']
            if color1 == 0 or color2 == 0:
                color1 = 5
                color2 = 5

            # ペア設置のencode（新しい関数を使用）
            code_str = self._encode_pair_move(move['x'], move['rotation'], color1, color2)
            encoded += code_str
            i += 1
        return encoded

    @staticmethod
    def _get_cell_id(cell):
        # encode.hのget_cell_id完全コピー
        if cell == 1:   # RED
            return 0
        elif cell == 2: # GREEN
            return 1
        elif cell == 3: # BLUE
            return 2
        elif cell == 4: # YELLOW
            return 3
        elif cell == 5 or cell == 6: # GARBAGE
            return 4
        else:
            return 4    # fallback: NONE or invalid→GARBAGE