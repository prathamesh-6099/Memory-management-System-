"""Detailed ranking score analysis"""
import json
import math
from src.memory_system import MemorySystem
from src.config import (
    RANKING_WEIGHTS_5_SIGNAL,
    RECENCY_DECAY_RATE,
    TYPE_PRIORITIES,
    FREQUENCY_DECAY_RATE,
    FREQUENCY_MAX_ACCESSES,
    ACCESS_RECENCY_WEIGHT
)

# Initialize
ms = MemorySystem('test_ranking_detail')
ms.clear_memories()

# Load and process
with open('evaluation/fixtures/distance_sweep_test.json') as f:
    data = json.load(f)

# Process all turns
for turn in data['turns']:
    if not turn.get('is_query'):
        ms.process_turn(turn['message'])

current_turn = data['query_turn']
query = "Tell me everything you remember"

# Get retrieval with stats
_, stats = ms.process_turn(query)
retrieved = stats.get('active_memories', [])

print(f"\n{'='*80}")
print(f"RANKING ANALYSIS - Query: '{query}'")
print(f"Current turn: {current_turn}")
print(f"{'='*80}\n")

print("🎯 Ranking Weights (5-Signal):")
for signal, weight in RANKING_WEIGHTS_5_SIGNAL.items():
    print(f"  {signal:12s}: {weight:.2f} ({weight*100:.0f}%)")

print(f"\n📊 Type Priorities:")
for mtype, priority in sorted(TYPE_PRIORITIES.items(), key=lambda x: -x[1]):
    print(f"  {mtype:12s}: {priority:.2f}")

# Get all memories and manually score them
all_mems = ms.redis_store.get_all_memories()
target_turns = [1000, 960, 910, 510, 10]
target_mems = [m for m in all_mems if int(m.get('turn_number', 0)) in target_turns]

print(f"\n\n{'='*80}")
print(f"TARGET MEMORIES AT TEST DISTANCES")
print(f"{'='*80}\n")

for mem in sorted(target_mems, key=lambda m: -int(m.get('turn_number', 0))):
    turn = int(mem.get('turn_number', 0))
    turns_ago = current_turn - turn
    mtype = mem.get('type', 'unknown')
    value = mem.get('value', '')[:50]
    confidence = float(mem.get('confidence', 0.5))
    access_count = int(mem.get('access_count', 0))
    
    # Calculate individual signal scores
    recency = math.exp(-RECENCY_DECAY_RATE * turns_ago)
    type_score = TYPE_PRIORITIES.get(mtype, 0.5)
    freq_norm = min(access_count / FREQUENCY_MAX_ACCESSES, 1.0)
    frequency = freq_norm  # Simplified
    
    # Check if retrieved
    was_retrieved = any(
        abs(int(r.get('origin_turn', 0)) - turn) <= 2 
        for r in retrieved
    )
    
    print(f"Turn {turn:4d} ({turns_ago:4d} turns ago) - {mtype:12s}")
    print(f"  Value: {value}")
    print(f"  Retrieved: {'✓ YES' if was_retrieved else '✗ NO'}")
    print(f"  Individual Scores:")
    print(f"    • Recency:    {recency:.4f} (weight: {RANKING_WEIGHTS_5_SIGNAL['recency']:.2f})")
    print(f"    • Type:       {type_score:.4f} (weight: {RANKING_WEIGHTS_5_SIGNAL['type']:.2f})")
    print(f"    • Frequency:  {frequency:.4f} (weight: {RANKING_WEIGHTS_5_SIGNAL['frequency']:.2f})")
    print(f"    • Confidence: {confidence:.4f} (weight: {RANKING_WEIGHTS_5_SIGNAL['confidence']:.2f})")
    print(f"    • Semantic:   [embed-based] (weight: {RANKING_WEIGHTS_5_SIGNAL['semantic']:.2f})")
    
    # Estimate minimum final score (without semantic component)
    min_score = (
        recency * RANKING_WEIGHTS_5_SIGNAL['recency'] +
        type_score * RANKING_WEIGHTS_5_SIGNAL['type'] +
        frequency * RANKING_WEIGHTS_5_SIGNAL['frequency'] +
        confidence * RANKING_WEIGHTS_5_SIGNAL['confidence']
    )
    print(f"  Minimum Score (no semantic): {min_score:.4f}")
    print(f"  Needs semantic > {(0.60 - min_score) / RANKING_WEIGHTS_5_SIGNAL['semantic']:.4f} to reach 0.60 total")
    print()

print(f"\n{'='*80}")
print(f"RETRIEVED MEMORIES: {len(retrieved)}")
print(f"{'='*80}\n")
for r in retrieved[:10]:
    turn = r.get('origin_turn', 0)
    mtype = r.get('type', 'unknown')
    content = r.get('content', '')[:60]
    print(f"  Turn {turn:4d}: {mtype:12s} - {content}")
