"""
スコア計算の詳細を検証
"""
from puyopuyo_env_cpp import PuyoPuyoGame
import numpy as np

game = PuyoPuyoGame()

print("=" * 60)
print("スコア計算の検証")
print("=" * 60)

# テスト1: 4個の赤ぷよを縦に並べる（1連鎖）
print("\n[テスト1] 4個の赤ぷよを縦に並べる")
state = game.starting_board. copy()

# 列0に赤ぷよ×4を配置
for i in range(2):
    state, _, score, chain = game.next_state(state, action=0, current_pair=(1, 1))  # 赤-赤
    print(f"  {i+1}回目: スコア+{score}, 累積連鎖{chain}")

print(f"  期待:  4個消えて40点（4 × 10 × 1連鎖倍率0 = 基本点のみ）")

# テスト2: 2連鎖を作る
print("\n[テスト2] 2連鎖を作る")
state = game.reset()

# 階段状に配置
actions = [
    (0, (1, 1)),  # 列0に赤-赤
    (0, (1, 1)),  # 列0に赤-赤（4個で消える）
    (1, (2, 2)),  # 列1に緑-緑
    (1, (2, 2)),  # 列1に緑-緑（連鎖で消える）
]

total_score = 0
total_chains = 0

for i, (action, pair) in enumerate(actions):
    state, _, score, chain = game.next_state(state, action, current_pair=pair)
    total_score += score
    total_chains += chain
    print(f"  手{i+1}: action={action}, pair={pair}, スコア+{score}, 連鎖+{chain}")

print(f"  最終:  総スコア{total_score}, 総連鎖{total_chains}")

# テスト3: 実際のエピソードを1つ実行
print("\n[テスト3] 1エピソードを実行して詳細ログ")
state = game.reset()

move_details = []
total_score = 0
total_chains = 0

for move_num in range(20):
    # ランダムに有効な行動を選ぶ
    valid_moves = game.get_valid_moves(state)
    valid_actions = np.where(valid_moves)[0]
    
    if len(valid_actions) == 0:
        break
    
    action = np.random.choice(valid_actions)
    pair = (np.random.randint(1, 5), np.random.randint(1, 5))
    
    state, _, score, chain = game.next_state(state, action, current_pair=pair)
    
    total_score += score
    total_chains += chain
    
    if score > 0 or chain > 0:
        print(f"  手{move_num+1}: スコア+{score}, 連鎖+{chain} (累積:  {total_score}点, {total_chains}連鎖)")
        move_details.append({
            'move': move_num + 1,
            'score': score,
            'chain':  chain,
            'cumulative_score': total_score,
            'cumulative_chain': total_chains
        })
    
    if game.reward(state) != -999:
        print(f"  ゲームオーバー")
        break

print(f"\n最終結果: {move_num+1}手, {total_chains}連鎖, {total_score}点")

# 1連鎖あたりの平均スコア
if total_chains > 0:
    print(f"1連鎖あたり平均スコア:   {total_score / total_chains:.1f}点")