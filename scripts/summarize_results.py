import json
import os
import pandas as pd

def summarize_results():
    base_dir = os.path.dirname(__file__)
    results_dir = os.getenv("FRAI_RESULTS_DIR") or os.path.join(base_dir, '../results/latest')
    results_path = os.path.join(results_dir, 'comparison.json')
    output_path = os.path.join(results_dir, 'summary.md')
    
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
    summary = df.groupby('model').agg(
        score=('score', 'mean'),
        score_std=('score', 'std'),
        passed=('passed', 'mean'),
        latency_ms=('latency_ms', 'mean'),
        results=('test_id', 'count'),
    ).reset_index()
    
    summary['passed'] = (summary['passed'] * 100).round(1).astype(str) + '%'
    summary['score'] = summary['score'].round(2)
    summary['score_std'] = summary['score_std'].fillna(0).round(2)
    summary['latency_ms'] = summary['latency_ms'].round(0).astype(int)
    
    summary = summary.sort_values('score', ascending=False)

    # Generate Markdown
    md = "# 📊 FRAI Benchmark Results\n\n"
    md += f"**Total Tests**: {len(df)}\n"
    md += f"**Models Evaluated**: {len(summary)}\n\n"
    
    md += "| Rank | Model | Score (0-10) | Std Dev | Pass Rate | Results | Avg Latency (ms) |\n"
    md += "|------|-------|--------------|---------|-----------|---------|------------------|\n"
    
    for rank_index, (_, row) in enumerate(summary.iterrows(), start=1):
        rank = "🥇" if rank_index == 1 else "🥈" if rank_index == 2 else "🥉" if rank_index == 3 else f"{rank_index}"
        md += f"| {rank} | **{row['model']}** | {row['score']} | {row['score_std']} | {row['passed']} | {row['results']} | {row['latency_ms']} |\n"

    with open(output_path, 'w') as f:
        f.write(md)
        
    print(f"✅ Summary saved to {output_path}")
    print(md)

if __name__ == "__main__":
    summarize_results()
