"""
C++から呼び出される推論スクリプト
"""
import sys
import os
import torch
import numpy as np

# Windows用のエンコーディング設定
if sys.platform == 'win32':
    import codecs
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')
    sys.stderr = codecs. getwriter('utf-8')(sys.stderr.buffer, 'strict')

# スクリプトのディレクトリを基準にパスを設定
script_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, script_dir)

from model import PuyoNet

def infer(state_file, output_file):
    """
    C++から渡された盤面で行動推論
    """
    # モデルパス（絶対パス）
    model_path = os.path.join(script_dir, 'models', 'puyo_model_cpp.pth')
    
    print(f"[DEBUG] Model path: {model_path}", file=sys.stderr)
    print(f"[DEBUG] Model exists: {os.path.exists(model_path)}", file=sys.stderr)
    
    try:
        if not os.path.exists(model_path):
            raise FileNotFoundError(f"Model not found: {model_path}")
        
        model = PuyoNet(board_height=14, board_width=6, num_actions=24)
        model.load_state_dict(torch.load(model_path, map_location='cpu'))
        model.eval()
        print("[DEBUG] Model loaded successfully", file=sys.stderr)
    except Exception as e:
        print(f"[WARN] Model load failed: {e}", file=sys.stderr)
        # フォールバック:  中央に縦置き
        with open(output_file, 'w') as f:
            f.write("2,0\n")
        return
    
    # 盤面読み込み
    try:
        board = np.loadtxt(state_file, delimiter=',', dtype=np.float32)
        print(f"[DEBUG] Board shape: {board.shape}", file=sys.stderr)
    except Exception as e:
        print(f"[ERROR] Failed to load board: {e}", file=sys.stderr)
        with open(output_file, 'w') as f:
            f.write("2,0\n")
        return
    
    # テンソルに変換
    state_tensor = torch.FloatTensor(board).unsqueeze(0).unsqueeze(0)  # (1, 1, 14, 6)
    
    # 推論
    with torch.no_grad():
        policy, value = model(state_tensor)
        policy = policy.cpu().numpy()[0]
    
    print(f"[DEBUG] Policy shape: {policy.shape}", file=sys.stderr)
    print(f"[DEBUG] Value:  {value.item():.4f}", file=sys.stderr)
    
    # 有効な手のマスク
    valid = get_valid_moves(board)
    policy = policy * valid
    
    if policy.sum() > 0:
        policy = policy / policy.sum()
        action = np.argmax(policy)
    else:
        action = 2  # デフォルト
    
    # actionを(x, r)に変換
    x = action % 6
    r = action // 6
    
    print(f"[DEBUG] Chosen action: x={x}, r={r} (action_id={action})", file=sys.stderr)
    
    # 結果出力
    with open(output_file, 'w') as f:
        f.write(f"{x},{r}\n")

def get_valid_moves(board):
    """簡易的な有効手判定"""
    valid = np.zeros(24, dtype=np.float32)
    
    for x in range(6):
        height = get_height(board, x)
        if height <= 11:
            valid[x + 0 * 6] = 1.0  # UP
            valid[x + 2 * 6] = 1.0  # DOWN
        if x < 5 and height <= 11:
            valid[x + 1 * 6] = 1.0  # RIGHT
        if x > 0 and height <= 11:
            valid[x + 3 * 6] = 1.0  # LEFT
    
    return valid

def get_height(board, x):
    """列の高さ取得"""
    for y in range(14):
        if board[y, x] != 0:
            return 14 - y
    return 0

if __name__ == "__main__":   
    if len(sys.argv) < 3:
        print("Usage: python inference_cpp.  py <state_file> <output_file>")
        sys.exit(1)
    
    infer(sys.argv[1], sys.argv[2])