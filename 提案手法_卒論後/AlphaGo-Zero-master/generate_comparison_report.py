"""
AlphaZero vs ama AI の比較レポート生成
"""
import os
import glob
from datetime import datetime

def read_alphazero_results():
    """最新のAlphaZero評価結果を読む"""
    eval_dir = 'evaluation_results'
    files = sorted(glob.glob(os.path.join(eval_dir, 'eval_iter*.txt')))
    
    if not files: 
        return None
    
    latest_file = files[-1]
    
    with open(latest_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # イテレーション番号を抽出
    import re
    match = re.search(r'Iteration (\d+)', content)
    iteration = int(match.group(1)) if match else 0
    
    # 平均値を抽出
    avg_score = float(re.search(r'Average Score:\s+([\d.]+)', content).group(1))
    avg_chains = float(re.search(r'Average Max Chain:\s+([\d.]+)', content).group(1))
    avg_moves = float(re.search(r'Average Moves:\s+([\d.]+)', content).group(1))
    total_score = int(re.search(r'Total Score:\s+(\d+)', content).group(1))
    
    return {
        'iteration': iteration,
        'avg_score': avg_score,
        'avg_chains': avg_chains,
        'avg_moves': avg_moves,
        'total_score': total_score,
        'file': latest_file
    }

# ama AIの固定値（前回の結果）
ama_results = {
    'avg_score': 8002,
    'avg_chains': 2.9,
    'avg_moves':  59,
    'total_score': 80020
}

alphazero = read_alphazero_results()

if not alphazero:
    print("⚠️ AlphaZeroの評価結果がまだありません")
    exit(0)

# レポート生成
report_file = f"evaluation_results/comparison_iter{alphazero['iteration']:03d}.txt"

with open(report_file, 'w', encoding='utf-8') as f:
    f.write("=" * 70 + "\n")
    f.write("Performance Comparison Report\n")
    f.write("AlphaZero vs ama AI (Beam Search Baseline)\n")
    f.write("=" * 70 + "\n\n")
    
    f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
    f.write(f"AlphaZero Model:  Iteration {alphazero['iteration']}\n\n")
    
    f.write("-" * 70 + "\n")
    f.write("AlphaZero Results (10 games):\n")
    f.write("-" * 70 + "\n")
    f.write(f"  Average Score:      {alphazero['avg_score']: >10.1f}\n")
    f.write(f"  Average Max Chain:  {alphazero['avg_chains']:>10.1f}\n")
    f.write(f"  Average Moves:      {alphazero['avg_moves']:>10.1f}\n")
    f.write(f"  Total Score:        {alphazero['total_score']:>10}\n\n")
    
    f.write("-" * 70 + "\n")
    f.write("ama AI Results (10 games, baseline):\n")
    f.write("-" * 70 + "\n")
    f.write(f"  Average Score:      {ama_results['avg_score']:>10.1f}\n")
    f.write(f"  Average Max Chain:  {ama_results['avg_chains']:>10.1f}\n")
    f.write(f"  Average Moves:      {ama_results['avg_moves']:>10.1f}\n")
    f.write(f"  Total Score:        {ama_results['total_score']:>10}\n\n")
    
    f.write("=" * 70 + "\n")
    f.write("Comparison (AlphaZero vs ama AI):\n")
    f.write("=" * 70 + "\n")
    
    score_diff = alphazero['avg_score'] - ama_results['avg_score']
    chain_diff = alphazero['avg_chains'] - ama_results['avg_chains']
    moves_diff = alphazero['avg_moves'] - ama_results['avg_moves']
    
    f.write(f"  Score Difference:   {score_diff: >10.1f}  ")
    if score_diff > 0:
        f.write(f"(AlphaZero +{abs(score_diff):.1f})\n")
    else:
        f.write(f"(ama AI +{abs(score_diff):.1f})\n")
    
    f.write(f"  Chain Difference:   {chain_diff:>10.1f}  ")
    if chain_diff > 0:
        f.write(f"(AlphaZero +{abs(chain_diff):.1f})\n")
    else:
        f.write(f"(ama AI +{abs(chain_diff):.1f})\n")
    
    f.write(f"  Moves Difference:   {moves_diff:>10.1f}  ")
    if moves_diff > 0:
        f.write(f"(AlphaZero +{abs(moves_diff):.1f} longer survival)\n")
    else:
        f.write(f"(ama AI +{abs(moves_diff):.1f})\n")
    
    f.write("\n" + "-" * 70 + "\n")
    
    if alphazero['avg_score'] > ama_results['avg_score']:
        improvement = (alphazero['avg_score'] / ama_results['avg_score'] - 1) * 100
        f.write(f"🏆 Winner: AlphaZero!\n")
        f.write(f"   AlphaZero is {improvement:.1f}% better\n")
    elif alphazero['avg_score'] < ama_results['avg_score']:
        gap = (ama_results['avg_score'] / alphazero['avg_score'] - 1) * 100
        f.write(f"Winner: ama AI\n")
        f.write(f"   Gap: {gap:.1f}% (still training...)\n")
    else:
        f.write(f"Result:  Tie\n")
    
    f.write("-" * 70 + "\n")

print(f"✅ 比較レポートを生成: {report_file}")
print("\n" + open(report_file, 'r', encoding='utf-8').read())