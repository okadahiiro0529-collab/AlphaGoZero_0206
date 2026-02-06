import torch
from model import PuyoNet
from puyopuyo_env_cpp import PuyoPuyoGame
from solver import Solver
import os
import numpy as np
from datetime import datetime
import csv

def evaluate_fixed_model(
    num_iterations=100,            # ←評価イテレーション数を100回に
    num_episodes=1,
    num_sims=120,
    model_dir='./models_mc_reward/',
    fixed_model_iter=38            # ←ずっとこのiterの重みで評価
):
    os.makedirs(model_dir, exist_ok=True)
    summary_file = os.path.join(model_dir, 'evaluation_progress.csv')

    game = PuyoPuyoGame()
    net = PuyoNet(board_height=14, board_width=6, num_actions=24)
    model_path = os.path.join(model_dir, f'puyo_alphazero_iter{fixed_model_iter:03d}.pth')
    net.load_state_dict(torch.load(model_path, map_location='cpu'))
    print(f"固定モデル {model_path} で全エピソードを評価", flush=True)

    if torch.cuda.is_available():
        net = net.cuda()
        print("GPU利用可能", flush=True)
    else:
        print("CPU検証モード", flush=True)

    solver = Solver(game=game, net=net, num_sims=num_sims)

    print("=" * 60, flush=True)
    print("AlphaGo Zero ぷよぷよ評価開始", flush=True)
    print(f"評価イテレーション数:   {num_iterations}", flush=True)
    print(f"1イテレーションあたり {num_episodes} エピソード", flush=True)
    print("=" * 60, flush=True)

    for iteration in range(num_iterations):
        print(f"\n{'='*60}", flush=True)
        print(f"Iteration {iteration + 1}/{num_iterations}", flush=True)
        print(f"{'='*60}", flush=True)

        print(f"ステップ1: 固定モデルで {num_episodes} エピソード評価", flush=True)
        results = []
        examples = []  # 使わないが互換用
        for ep in range(num_episodes):
            print(f"エピソード {ep + 1}/{num_episodes}", flush=True)
            episode_examples, episode_result = solver.execute_episode(net)
            examples.extend(episode_examples)
            results.append(episode_result)

        # ---- 統計値計算はもとのまま ----
        scores = [r['score'] for r in results]
        all_chain_events = [c for r in results for c in r['chain_events']]
        avg_chain_per_event = sum(all_chain_events) / len(all_chain_events) if all_chain_events else 0.0
        avg_chains = [r['avg_chain'] for r in results]
        no_chain_count = sum(1 for c in avg_chains if c == 0.0)
        no_chain_rate = no_chain_count / len(avg_chains)
        max_chains = [r['max_chain'] for r in results]
        ave_max_chain = np.mean(max_chains) if max_chains else 0.0
        max_chain_overall = max(max_chains) if max_chains else 0
        moves = [r['moves'] for r in results]
        total_score = sum(scores)
        total_moves = sum(moves)
        avg_score = np.mean(scores)
        avg_moves = np.mean(moves)
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

        print("="*20 + f" Iteration {iteration+1} Summary " + "="*20)
        print(f"平均スコア: {avg_score:.2f}")
        print(f"平均連鎖/イベント: {avg_chain_per_event:.2f}")
        print(f"最大連鎖の平均: {ave_max_chain:.2f}")
        print(f"最大連鎖: {max_chain_overall}")
        print(f"連鎖なし率: {no_chain_rate:.2%}")
        print(f"平均手数: {avg_moves:.2f}")
        print("="*60)

        # --- CSV 追記保存 ---
        file_exists = os.path.exists(summary_file)
        with open(summary_file, 'a', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            if not file_exists:
                writer.writerow([
                    'iteration',
                    'avg_score',
                    'avg_chain_per_event',
                    'ave_max_chain',
                    'max_chain',
                    'no_chain_rate',
                    'avg_moves',
                    'total_score',
                    'total_moves',
                    'timestamp'
                ])
            writer.writerow([
                iteration+1,
                f"{avg_score:.2f}",
                f"{avg_chain_per_event:.2f}",
                f"{ave_max_chain:.2f}",
                max_chain_overall,
                f"{no_chain_rate:.2%}",
                f"{avg_moves:.2f}",
                total_score,
                total_moves,
                timestamp
            ])

        # 学習しない・モデル保存もしない！
        print(f"（学習も重み変更もせず、固定モデルのまま評価のみ）", flush=True)

    print("\n評価完了！", flush=True)


if __name__ == "__main__":
    evaluate_fixed_model(
        num_iterations=100,     # ←回す回数
        num_episodes=1,         # 毎回1つのテストエピソード
        num_sims=120,
        model_dir='./models_mc_reward/',
        fixed_model_iter=38     # 50番重みだけ使う
    )