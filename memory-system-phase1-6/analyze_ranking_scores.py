"""Analyze retrieval ranking scores"""
import json
from src.memory_system import MemorySystem

# Initialize
ms = MemorySystem('test_ranking_scores')
ms.clear_memories()

# Load and process
with open('evaluation/fixtures/distance_sweep_test.json') as f:
    data = json.load(f)

# Process all turns
for turn in data['turns']:
    if not turn.get('is_query'):
        ms.process_turn(turn['message'])

# Query and get ALL memories with scores
all_mems = ms.redis_store.get_all_memories()
current_turn = data['query_turn']

print(f"\nAll {len(all_mems)} memories in Redis:")
print(f"Query at turn {current_turn}\n")

# Manually calculate recency scores for comparison
import math
from src.config import RECENCY_DECAY_RATE

target_turns = [1000, 960, 910, 510, 10]
for mem in all_mems:
    mem_turn = int(mem.get('turn_number', 0))
    if mem_turn in target_turns:
        turns_ago = current_turn - mem_turn
        recency = math.exp(-RECENCY_DECAY_RATE * turns_ago)
        print(f"Turn {mem_turn:4d} ({turns_ago:4d} ago): recency_score={recency:.6f}")
        print(f"  Type: {mem.get('type'):12s} - {mem.get('value')[:50]}")
        print()

print("\n" + "="*60)
print("Recency decay analysis:")
print(f"RECENCY_DECAY_RATE = {RECENCY_DECAY_RATE}")
for distance in [10, 50, 100, 500, 1000]:
    score = math.exp(-RECENCY_DECAY_RATE * distance)
    print(f"  Distance {distance:4d}: recency_score = {score:.6f}")
