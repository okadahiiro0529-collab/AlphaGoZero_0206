"""
学習済みモデルの評価
"""
import torch
from model import PuyoNet
from puyopuyo_env_cpp import PuyoPuyoGame
from mcts import MCTS
import numpy as np

game = PuyoPuyoGame()
net = PuyoNet(board_height=14, board_width=6, num_actions=24)

# 最終モデルをロード
net.load_state_dict(torch.load('models/puyo_alphazero_final.pth', map_location='cpu'))
net.eval()

print("=== 評価エピソード実行 ===")
mcts = MCTS(game=game, net=net, num_sims=100)

scores = []
moves_list = []

for ep in range(10):
    state = game.reset()
    num_moves = 0
    
    while True:
        reward = game.reward(state)
        if reward != -999 or num_moves >= 100:
            break
        
        action = mcts.choose_action(state)
        state, _ = game.next_state(state, action)
        num_moves += 1
    
    scores.append(game.current_score)
    moves_list.append(num_moves)
    print(f"Episode {ep+1}: {num_moves}手、スコア{game. current_score}")

print(f"\n平均:  {np.mean(moves_list):.1f}手、スコア{np.mean(scores):.0f}")