"""
Visual Comparison: Before vs After Recency Decay Fix
Shows the impact of adjusting RECENCY_DECAY_RATE on long-term memory recall
"""

import math
import matplotlib.pyplot as plt
import numpy as np

# Configuration
RANKING_WEIGHTS = {
    "semantic": 0.35,
    "type": 0.20,
    "recency": 0.20,
    "frequency": 0.15,
    "confidence": 0.10,
}

def calculate_scores(decay_rate, turns_range):
    """Calculate recency and retrieval scores"""
    recency_scores = []
    retrieval_scores = []
    
    for turns_ago in turns_range:
        # Recency score (exponential decay)
        recency = math.exp(-decay_rate * turns_ago)
        recency_scores.append(recency)
        
        # Best-case retrieval score (perfect semantic, type, frequency, confidence)
        retrieval = (
            RANKING_WEIGHTS['semantic'] * 1.0 +
            RANKING_WEIGHTS['type'] * 1.0 +
            RANKING_WEIGHTS['recency'] * recency +
            RANKING_WEIGHTS['frequency'] * 1.0 +
            RANKING_WEIGHTS['confidence'] * 1.0
        )
        retrieval_scores.append(retrieval)
    
    return recency_scores, retrieval_scores


def plot_comparison():
    """Create visualization comparing old vs new decay rates"""
    
    # Turn range to analyze
    turns = np.arange(0, 1001, 10)
    
    # Calculate scores for both configurations
    old_recency, old_retrieval = calculate_scores(0.1, turns)  # OLD
    new_recency, new_retrieval = calculate_scores(0.001, turns)  # NEW
    
    # Create figure with 2 subplots
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 6))
    
    # Plot 1: Recency Score Over Time
    ax1.plot(turns, old_recency, 'r-', linewidth=2, label='OLD (rate=0.1)', alpha=0.7)
    ax1.plot(turns, new_recency, 'g-', linewidth=2, label='NEW (rate=0.001)', alpha=0.7)
    ax1.axhline(y=0.1, color='gray', linestyle='--', alpha=0.5, label='10% threshold')
    ax1.set_xlabel('Turns Ago', fontsize=12)
    ax1.set_ylabel('Recency Score', fontsize=12)
    ax1.set_title('Recency Score Decay Over Time', fontsize=14, fontweight='bold')
    ax1.legend(fontsize=10)
    ax1.grid(True, alpha=0.3)
    ax1.set_xlim(0, 1000)
    ax1.set_ylim(0, 1.05)
    
    # Annotate key points
    ax1.annotate('OLD: Dead after 100 turns', 
                xy=(100, 0.00004), xytext=(200, 0.3),
                arrowprops=dict(arrowstyle='->', color='red', lw=1.5),
                fontsize=10, color='red')
    ax1.annotate('NEW: Still 37% at 1000 turns', 
                xy=(1000, 0.368), xytext=(700, 0.6),
                arrowprops=dict(arrowstyle='->', color='green', lw=1.5),
                fontsize=10, color='green')
    
    # Plot 2: Best-Case Retrieval Score
    ax2.plot(turns, old_retrieval, 'r-', linewidth=2, label='OLD (rate=0.1)', alpha=0.7)
    ax2.plot(turns, new_retrieval, 'g-', linewidth=2, label='NEW (rate=0.001)', alpha=0.7)
    ax2.axhline(y=0.8, color='gray', linestyle='--', alpha=0.5, label='80% threshold')
    ax2.set_xlabel('Turns Ago', fontsize=12)
    ax2.set_ylabel('Best-Case Retrieval Score', fontsize=12)
    ax2.set_title('Impact on Retrieval (Perfect Semantic/Type/Frequency/Confidence)', 
                 fontsize=14, fontweight='bold')
    ax2.legend(fontsize=10)
    ax2.grid(True, alpha=0.3)
    ax2.set_xlim(0, 1000)
    ax2.set_ylim(0.7, 1.05)
    
    # Annotate key points
    ax2.annotate('OLD: Plateaus at 0.80', 
                xy=(100, 0.8), xytext=(300, 0.85),
                arrowprops=dict(arrowstyle='->', color='red', lw=1.5),
                fontsize=10, color='red')
    ax2.annotate('NEW: Still 0.87 at 1000 turns', 
                xy=(1000, 0.874), xytext=(600, 0.95),
                arrowprops=dict(arrowstyle='->', color='green', lw=1.5),
                fontsize=10, color='green')
    
    plt.tight_layout()
    plt.savefig('evaluation/results/recency_decay_comparison.png', dpi=150, bbox_inches='tight')
    print("✓ Saved visualization to: evaluation/results/recency_decay_comparison.png")
    plt.show()


def print_score_table():
    """Print detailed score comparison table"""
    
    test_points = [10, 50, 100, 500, 1000, 2000, 5000]
    
    print("\n" + "="*80)
    print("DETAILED SCORE COMPARISON")
    print("="*80)
    print(f"\n{'Turns Ago':<12} {'OLD Recency':<15} {'NEW Recency':<15} {'OLD Total':<12} {'NEW Total':<12} {'Improvement'}")
    print("-"*80)
    
    for turns in test_points:
        old_r = math.exp(-0.1 * turns)
        new_r = math.exp(-0.001 * turns)
        
        old_total = 0.8 + 0.2 * old_r  # 0.8 from other signals + 0.2*recency
        new_total = 0.8 + 0.2 * new_r
        
        improvement = ((new_total - old_total) / old_total * 100) if old_total > 0 else float('inf')
        
        print(f"{turns:<12} {old_r:<15.6f} {new_r:<15.6f} {old_total:<12.6f} {new_total:<12.6f} {improvement:+.2f}%")
    
    print("="*80)
    
    print("\n💡 KEY INSIGHTS:")
    print("   • OLD config: Memories become unrecoverable after ~100 turns")
    print("   • NEW config: Memories remain retrievable even at 1000+ turns")
    print("   • At 1000 turns: +9.2% improvement in retrieval score")
    print("   • Long-term memories can now compete with recent ones if semantically relevant")


if __name__ == "__main__":
    print("\n📊 RECENCY DECAY FIX - VISUAL ANALYSIS\n")
    
    print_score_table()
    
    try:
        plot_comparison()
        print("\n✅ Visualization complete!\n")
    except Exception as e:
        print(f"\n⚠️  Could not create plot (matplotlib issue): {e}")
        print("    Detailed table above shows the same information.\n")
