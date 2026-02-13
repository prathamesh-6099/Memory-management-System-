"""Why was the fact retrieved but not the preference?"""
import json
from src.memory_system import MemorySystem

# Initialize
ms = MemorySystem('debug_preference_vs_fact')
ms.clear_memories()

# Load and process
with open('evaluation/fixtures/distance_sweep_test.json') as f:
    data = json.load(f)

# Process all turns
for turn in data['turns']:
    if not turn.get('is_query'):
        ms.process_turn(turn['message'])

query = "Tell me everything you remember about this user"

# Get both memories from turn 10
redis_mems = ms.redis_store.get_all_memories()
turn_10_mems = [m for m in redis_mems if int(m.get('turn_number', 0)) == 10]

print("="*70)
print("TURN 10 MEMORIES (1000 turns ago):")
print("="*70)
for mem in turn_10_mems:
    print(f"\n{mem['type'].upper()}: {mem['key']} = {mem['value']}")
    print(f"  Memory ID: {mem['memory_id']}")
    print(f"  Confidence: {mem['confidence']}")
    print(f"  Turn: {mem['turn_number']}")

# Check semantic scores for both
print(f"\n{'='*70}")
print("SEMANTIC SCORES:")
print("="*70)

semantic_results = ms.vector_store.search_similar(
    query=query,
    limit=100,
    min_score=0.0,
    user_id=ms.user_id
)

for mem in turn_10_mems:
    mem_id = mem['memory_id']
    found = [r for r in semantic_results if r['memory_id'] == mem_id]
    
    if found:
        score = found[0]['score']
        print(f"\n✓ {mem['type']}: {mem['value']}")
        print(f"  Semantic score: {score:.4f}")
    else:
        print(f"\n✗ {mem['type']}: {mem['value']}")
        print(f"  NOT in semantic search results (score too low)")

# Now check full ranking
print(f"\n{'='*70}")
print("FULL 5-SIGNAL RANKING:")
print("="*70)

import math
from src.config import (
    RANKING_WEIGHTS_5_SIGNAL,
    TYPE_PRIORITIES,
    RECENCY_DECAY_RATE,
    FREQUENCY_MAX_ACCESSES
)

current_turn = 1010
for mem in turn_10_mems:
    turns_ago = current_turn - int(mem['turn_number'])
    
    # Calculate scores
    recency = math.exp(-RECENCY_DECAY_RATE * turns_ago)
    type_score = TYPE_PRIORITIES.get(mem['type'], 0.5)
    confidence = float(mem.get('confidence', 0.5))
    access_count = int(mem.get('access_count', 0))
    freq_norm = min(access_count / FREQUENCY_MAX_ACCESSES, 1.0)
    
    # Get semantic score
    mem_id = mem['memory_id']
    semantic_result = [r for r in semantic_results if r['memory_id'] == mem_id]
    semantic_score = semantic_result[0]['score'] if semantic_result else 0.0
    
    # Calculate final score
    final_score = (
        semantic_score * RANKING_WEIGHTS_5_SIGNAL['semantic'] +
        type_score * RANKING_WEIGHTS_5_SIGNAL['type'] +
        recency * RANKING_WEIGHTS_5_SIGNAL['recency'] +
        freq_norm * RANKING_WEIGHTS_5_SIGNAL['frequency'] +
        confidence * RANKING_WEIGHTS_5_SIGNAL['confidence']
    )
    
    print(f"\n{mem['type'].upper()}: {mem['value']}")
    print(f"  Semantic:   {semantic_score:.4f} × {RANKING_WEIGHTS_5_SIGNAL['semantic']:.2f} = {semantic_score * RANKING_WEIGHTS_5_SIGNAL['semantic']:.4f}")
    print(f"  Type:       {type_score:.4f} × {RANKING_WEIGHTS_5_SIGNAL['type']:.2f} = {type_score * RANKING_WEIGHTS_5_SIGNAL['type']:.4f}")
    print(f"  Recency:    {recency:.4f} × {RANKING_WEIGHTS_5_SIGNAL['recency']:.2f} = {recency * RANKING_WEIGHTS_5_SIGNAL['recency']:.4f}")
    print(f"  Frequency:  {freq_norm:.4f} × {RANKING_WEIGHTS_5_SIGNAL['frequency']:.2f} = {freq_norm * RANKING_WEIGHTS_5_SIGNAL['frequency']:.4f}")
    print(f"  Confidence: {confidence:.4f} × {RANKING_WEIGHTS_5_SIGNAL['confidence']:.2f} = {confidence * RANKING_WEIGHTS_5_SIGNAL['confidence']:.4f}")
    print(f"  ─────────────────────────────────────────")
    print(f"  FINAL SCORE: {final_score:.4f}")

# Check what was actually retrieved
print(f"\n{'='*70}")
print("ACTUALLY RETRIEVED:")
print("="*70)

_, stats = ms.process_turn(query)
retrieved = stats.get('active_memories', [])

turn_10_retrieved_ids = [m['memory_id'] for m in retrieved if m.get('origin_turn', 0) == 10]

for mem in turn_10_mems:
    if mem['memory_id'] in turn_10_retrieved_ids:
        print(f"✓ {mem['type']}: {mem['value']}")
    else:
        print(f"✗ {mem['type']}: {mem['value']}")

print(f"\nTotal retrieved from turn 10: {len(turn_10_retrieved_ids)} of {len(turn_10_mems)}")
