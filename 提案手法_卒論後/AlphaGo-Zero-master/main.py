"""
AlphaGo Zero 自動評価付き学習スクリプト（評価指標修正版）
"""
import torch
from model import PuyoNet
from puyopuyo_env_cpp import PuyoPuyoGame
from solver import Solver
import os
import numpy as np
from datetime import datetime
import csv


def train_alphazero(
    num_iterations=200,
    num_episodes=30,
    num_sims=50,
    model_dir='./models_mc_reward/'
):
    os.makedirs(model_dir, exist_ok=True)
    summary_file = os.path.join(model_dir, 'training_progress.csv')  # 出力先
    
    game = PuyoPuyoGame()
    net = PuyoNet(board_height=14, board_width=6, num_actions=24)
    
    resume_iter = 50  # ← 再開したいイテレーション番号
    if resume_iter > 0:
        model_path = os.path.join(model_dir, f'puyo_alphazero_iter{resume_iter:03d}.pth')
        net.load_state_dict(torch.load(model_path, map_location='cpu'))
        print(f"モデル {model_path} から再開", flush=True)
    else:
        print("事前学習モデルなし。ランダム初期化から開始", flush=True)

    if torch.cuda.is_available():
        net = net.cuda()
        print("GPU利用可能", flush=True)
    else:
        print("CPU学習モード", flush=True)
    
    solver = Solver(game=game, net=net, num_sims=num_sims)
    
    print("=" * 60, flush=True)
    print("AlphaGo Zero ぷよぷよ学習開始（おじゃまぷよあり）", flush=True)
    print(f"総イテレーション:   {num_iterations}", flush=True)
    print(f"評価間隔:  1イテレーションごと", flush=True)
    print("=" * 60, flush=True)
    
    for iteration in range(resume_iter, num_iterations):
        print(f"\n{'='*60}", flush=True)
        print(f"Iteration {iteration + 1}/{num_iterations}", flush=True)
        print(f"{'='*60}", flush=True)
        
        print(f"ステップ1: 自己対戦（{num_episodes}エピソード）", flush=True)
        examples = []
        results = []  # ← 各episodeのスコア、連鎖などを貯める
        for ep in range(num_episodes):
            print(f"エピソード {ep + 1}/{num_episodes}", flush=True)
            episode_examples, episode_result = solver.execute_episode(net)
            examples.extend(episode_examples)
            results.append(episode_result)

        # --- 統計出力 ----
        scores = [r['score'] for r in results]
        all_chain_events = [c for r in results for c in r['chain_events']]
        if all_chain_events:
            avg_chain_per_event = sum(all_chain_events) / len(all_chain_events)
        else:
            avg_chain_per_event = 0.0

        avg_chains = [r['avg_chain'] for r in results]
        no_chain_count = sum(1 for c in avg_chains if c == 0.0)
        no_chain_rate = no_chain_count / len(avg_chains)  # 割合（0.0-1.0）

        max_chains = [r['max_chain'] for r in results]
        ave_max_chain = np.mean(max_chains) if max_chains else 0.0    # ★新規追加（エピソードごとの最大連鎖数の平均）
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
        print(f"最大連鎖の平均: {ave_max_chain:.2f}")           # ★ ave_max_chainを表示
        print(f"最大連鎖: {max_chain_overall}")
        print(f"連鎖なし率: {no_chain_rate:.2%}")
        print(f"平均手数: {avg_moves:.2f}")
        print("="*60)
        # -----------------
        
        print(f"データ収集完了:  {len(examples)} samples", flush=True)

        # --- CSV出力 ---
        file_exists = os.path.exists(summary_file)
        with open(summary_file, 'a', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            if not file_exists:
                writer.writerow([
                    'iteration',
                    'avg_score',
                    'avg_chain_per_event',
                    'ave_max_chain',         # ★追加
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
                f"{ave_max_chain:.2f}",     # ★追加
                max_chain_overall,
                f"{no_chain_rate:.2%}",
                f"{avg_moves:.2f}",
                total_score,
                total_moves,
                timestamp
            ])
        # ----------------

        print(f"ステップ2: ニューラルネットワーク学習", flush=True)
        solver.train(examples, epochs=10)
        
        if (iteration + 1) % 1 == 0:
            model_path = os.path.join(model_dir, f'puyo_alphazero_iter{iteration+1:03d}.pth')
            torch.save(net.state_dict(), model_path)
            print(f"モデル保存:   {model_path}", flush=True)
            
            if torch.cuda.is_available():
                net = net.cuda()
    
    final_path = os.path.join(model_dir, 'puyo_alphazero_final.pth')
    torch.save(net.state_dict(), final_path)
    print(f"\n{'='*60}", flush=True)
    print(f"学習完了！最終モデル:   {final_path}", flush=True)
    print(f"{'='*60}", flush=True)

if __name__ == "__main__":
    train_alphazero(
        num_iterations=150,
        num_episodes=1,
        num_sims=120
    )