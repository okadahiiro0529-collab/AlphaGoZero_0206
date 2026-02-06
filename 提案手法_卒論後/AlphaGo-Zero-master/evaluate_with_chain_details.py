"""
連鎖詳細付き評価関数
"""
import numpy as np
from mcts import MCTS

def evaluate_model(net, game, num_games=10, iteration=0):
    """
    連鎖詳細を記録しながらモデル評価
    """
    from datetime import datetime
    import os
    
    print(f"\n{'='*60}", flush=True)
    print(f"[EVAL] Iteration {iteration} 評価開始 ({num_games}ゲーム)", flush=True)
    print(f"{'='*60}", flush=True)
    
    mcts = MCTS(game=game, net=net, num_sims=100)
    
    results = []
    total_score = 0
    total_chains = 0
    total_moves = 0
    all_chain_events = []
    
    for game_num in range(num_games):
        state = game.reset()
        episode_score = 0
        episode_chains = 0
        num_moves = 0
        
        # ⭐ 連鎖イベント記録
        chain_events = []
        
        while True: 
            if game.reward(state) != -999 or num_moves >= 100:
                break
            
            for _ in range(100):
                mcts.search(state.copy())
            
            pi = mcts.get_action_probabilities(state, t=0)
            action = np.argmax(pi)
            
            pair = (np.random.randint(1, 5), np.random.randint(1, 5))
            state, _, score, chain = game.next_state(state, action, current_pair=pair)
            
            episode_score += score
            episode_chains += chain
            num_moves += 1
            
            # ⭐ 連鎖記録
            if chain > 0:
                chain_events.append(chain)
        
        # 連鎖詳細を整形
        if len(chain_events) == 0:
            chain_str = "なし"
        elif len(chain_events) <= 3:
            chain_str = ', '.join(map(str, chain_events))
        else:
            chain_str = f"{', '.join(map(str, chain_events[:3]))}...+{len(chain_events)-3}"
        
        results.append({
            'game':  game_num + 1,
            'score': episode_score,
            'chains': episode_chains,
            'moves': num_moves,
            'chain_events': chain_events
        })
        
        total_score += episode_score
        total_chains += episode_chains
        total_moves += num_moves
        all_chain_events.extend(chain_events)
        
        print(f"  Game {game_num+1}: Score={episode_score}, Chain=[{chain_str}] (計{episode_chains}), Moves={num_moves}", flush=True)
    
    avg_score = total_score / num_games
    avg_chains = total_chains / num_games
    avg_moves = total_moves / num_games
    
    # 結果をファイルに保存
    eval_dir = 'evaluation_results'
    os.makedirs(eval_dir, exist_ok=True)
    
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    result_file = os.path.join(eval_dir, f'eval_iter{iteration:03d}_{timestamp}.txt')
    
    with open(result_file, 'w', encoding='utf-8') as f:
        f.write("=" * 60 + "\n")
        f.write(f"AlphaZero Evaluation - Iteration {iteration}\n")
        f.write(f"Timestamp: {timestamp}\n")
        f.write("=" * 60 + "\n\n")
        
        f.write(f"[AlphaZero Performance] ({num_games} games)\n")
        for r in results:
            chain_detail = ', '.join(map(str, r['chain_events'])) if r['chain_events'] else "なし"
            f.write(f"  Game {r['game']}:  Score={r['score']}, Chain=[{chain_detail}] (計{r['chains']}), Moves={r['moves']}\n")
        
        f.write("\n" + "-" * 60 + "\n")
        f.write("Summary:\n")
        f.write(f"  Average Score:        {avg_score:.1f}\n")
        f.write(f"  Average Max Chain:   {avg_chains:.1f}\n")
        f.write(f"  Average Moves:       {avg_moves:.1f}\n")
        f.write(f"  Total Score:         {total_score}\n")
        f.write(f"  Total Chain Events:   {len(all_chain_events)}\n")
        
        # 連鎖分布
        if all_chain_events:
            from collections import Counter
            chain_dist = Counter(all_chain_events)
            f.write("\n連鎖分布:\n")
            for chain_len in sorted(chain_dist.keys()):
                f.write(f"  {chain_len}連鎖: {chain_dist[chain_len]}回\n")
        
        f.write("-" * 60 + "\n")
    
    print(f"\n[OK] 評価結果を保存:  {result_file}", flush=True)
    print(f"   平均スコア: {avg_score:.1f}, 平均連鎖:  {avg_chains:.1f}, 平均手数: {avg_moves:.1f}", flush=True)
    
    # サマリーファイルに追記
    summary_file = os.path.join(eval_dir, 'training_progress.csv')
    if not os.path.exists(summary_file):
        with open(summary_file, 'w') as f:
            f.write("iteration,avg_score,avg_chains,avg_moves,total_score,chain_events,timestamp\n")
    
    with open(summary_file, 'a') as f:
        f.write(f"{iteration},{avg_score:.1f},{avg_chains:.1f},{avg_moves:.1f},{total_score},{len(all_chain_events)},{timestamp}\n")
    
    return avg_score, avg_chains, avg_moves