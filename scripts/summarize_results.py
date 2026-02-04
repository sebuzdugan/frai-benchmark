import json
import os
import pandas as pd

def summarize_results():
    base_dir = os.path.dirname(__file__)
    results_path = os.path.join(base_dir, '../results/latest/comparison.json')
    output_path = os.path.join(base_dir, '../results/latest/summary.md')
    
    if not os.path.exists(results_path):
        print("❌ No results found. Run benchmark first.")
        return

    with open(results_path, 'r') as f:
        data = json.load(f)

    df = pd.DataFrame(data)
    
    if df.empty:
        print("⚠️  Results file is empty.")
        return

    # Calculate stats
    summary = df.groupby('model').agg({
        'score': 'mean',
        'passed': 'mean',
        'latency_ms': 'mean'
    }).reset_index()
    
    summary['passed'] = (summary['passed'] * 100).round(1).astype(str) + '%'
    summary['score'] = summary['score'].round(2)
    summary['latency_ms'] = summary['latency_ms'].round(0).astype(int)
    
    summary = summary.sort_values('score', ascending=False)

    # Generate Markdown
    md = "# 📊 FRAI Benchmark Results\n\n"
    md += f"**Total Tests**: {len(df)}\n"
    md += f"**Models Evaluated**: {len(summary)}\n\n"
    
    md += "| Rank | Model | Score (0-10) | Pass Rate | Avg Latency (ms) |\n"
    md += "|------|-------|--------------|-----------|------------------|\n"
    
    for i, row in summary.iterrows():
        rank = "🥇" if i == 0 else "🥈" if i == 1 else "🥉" if i == 2 else f"{i+1}"
        md += f"| {rank} | **{row['model']}** | {row['score']} | {row['passed']} | {row['latency_ms']} |\n"

    with open(output_path, 'w') as f:
        f.write(md)
        
    print(f"✅ Summary saved to {output_path}")
    print(md)

if __name__ == "__main__":
    summarize_results()
