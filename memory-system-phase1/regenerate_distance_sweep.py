"""
Regenerate distance sweep test with corrected turn placement
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

from evaluation.conversation_generator import ConversationGenerator

def main():
    print("🔄 Regenerating distance sweep test with FIX...")
    print("="*70)
    
    generator = ConversationGenerator()
    
    # Generate corrected distance sweep test
    distance_sweep = generator.generate_distance_sweep_conversation(
        target_distances=[10, 50, 100, 500, 1000]
    )
    
    # Save to file
    import json
    output_file = "evaluation/fixtures/distance_sweep_test.json"
    with open(output_file, 'w') as f:
        json.dump(distance_sweep, f, indent=2)
    
    print(f"\n✓ Saved corrected test to: {output_file}")
    print(f"\nQuery turn: {distance_sweep['query_turn']}")
    print("\nMemory placement:")
    print("-" * 70)
    
    for mem in distance_sweep['ground_truth_memories']:
        distance = mem['test_distance']
        turn = mem['turn']
        query_turn = distance_sweep['query_turn']
        turns_ago = query_turn - turn
        print(f"  Distance {distance:4d}: Memory at turn {turn:4d} "
              f"(query at {query_turn} = {turns_ago} turns ago) ✓")
    
    print("\n" + "="*70)
    print("✅ Distance sweep test regenerated correctly!\n")

if __name__ == "__main__":
    main()
