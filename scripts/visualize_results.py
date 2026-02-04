import json
import os
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
from datetime import datetime

# Set premium style
plt.style.use('dark_background')
sns.set_theme(style="dark", rc={"axes.facecolor": "#0f0f0f", "figure.facecolor": "#0f0f0f", "grid.color": "#333333"})

def visualize_results():
    results_dir = os.path.join(os.path.dirname(__file__), '../results/latest')
    output_path = os.path.join(results_dir, 'benchmark_leaderboard.png')
    data_path = os.path.join(results_dir, 'comparison.json')
    
    if not os.path.exists(data_path):
        print(f"No comparison data found at {data_path}")
        return

    with open(data_path, 'r') as f:
        data = json.load(f)

    df = pd.DataFrame(data)
    
    # 1. Overall Score
    overall_scores = df.groupby('model')['score'].mean().sort_values(ascending=False)
    
    # 2. Category Breakdown (Pivot Table)
    pivot = df.pivot_table(index='model', columns='category', values='score', aggfunc='mean')
    pivot['OVERALL'] = overall_scores
    pivot = pivot.sort_values('OVERALL', ascending=False)
    
    # Setup Figure
    plt.figure(figsize=(14, 8))
    
    # Create Heatmap
    # Use a premium diverging palette (e.g., 'vlag' or custom dark-to-green)
    cmap = sns.diverging_palette(10, 130, as_cmap=True, center="dark") 
    
    ax = sns.heatmap(
        pivot, 
        annot=True, 
        fmt=".1f", 
        cmap='RdYlGn', # Red to Green
        linewidths=0.5, 
        linecolor='#1e1e1e',
        cbar_kws={'label': 'Safety Score (0-10)'},
        vmin=0, vmax=10
    )
    
    # Styling
    ax.set_title('🏆 FRAI Benchmark Leaderboard', fontsize=24, pad=20, color='white', fontweight='bold', fontfamily='sans-serif')
    ax.set_xlabel('', fontsize=12)
    ax.set_ylabel('', fontsize=12)
    plt.yticks(rotation=0, fontsize=12, fontweight='bold', color='#dddddd')
    plt.xticks(rotation=45, ha='right', fontsize=11, color='#aaaaaa')
    
    # Highlight Overall Column
    # (Optional: specialized styling could go here, but heatmap handles it well)

    # Footer
    plt.figtext(0.98, 0.02, f"Benchmark Run: {datetime.now().strftime('%Y-%m-%d %H:%M')}", ha="right", fontsize=9, color='#555555')
    plt.figtext(0.02, 0.02, "Powered by FRAI Engine", ha="left", fontsize=9, color='#555555')

    plt.tight_layout()
    plt.savefig(output_path, dpi=300, bbox_inches='tight', facecolor='#0f0f0f')
    print(f"✅ Visualization saved to {output_path}")

if __name__ == "__main__":
    visualize_results()
