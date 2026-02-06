"""
summary. csv生成スクリプト
"""
import sys
import pandas as pd
from datetime import datetime

def generate_summary(csv_file):
    df = pd.read_csv(csv_file)
    
    successes = df['success'].sum()
    attempts = len(df)
    errors = attempts - successes
    avg_score = df['total_score'].mean()
    avg_chain = df['max_chain'].mean()
    
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    summary = f"""
==================================================================================
Summary generated_at, successes, attempts, errors, avg_total_score, avg_max_chain
summary,"{timestamp}", {successes}, {attempts}, {errors}, {avg_score:. 2f}, {avg_chain:. 2f}
==================================================================================
"""
    
    print(summary)
    
    # summary_alphazero.csvに追記
    with open(csv_file. replace('.csv', '_summary.txt'), 'w') as f:
        f.write(summary)

if __name__ == "__main__": 
    if len(sys.argv) < 2:
        print("Usage: python generate_summary.py <csv_file>")
        sys.exit(1)
    
    generate_summary(sys.argv[1])