"""Verify 1000-turn recall failure"""
import json
from src.memory_system import MemorySystem

# Initialize
ms = MemorySystem('verify_1000_turn')
ms.clear_memories()

# Load and process
with open('evaluation/fixtures/distance_sweep_test.json') as f:
    data = json.load(f)

# Process all turns
for turn in data['turns']:
    if not turn.get('is_query'):
        ms.process_turn(turn['message'])

# Check what memories exist at turn 10
redis_mems = ms.redis_store.get_all_memories()
turn_10_mems = [m for m in redis_mems if int(m.get('turn_number', 0)) == 10]

print("="*70)
print("MEMORIES AT TURN 10 (1000 turns ago):")
print("="*70)
for mem in turn_10_mems:
    print(f"  Type: {mem['type']}")
    print(f"  Key: {mem['key']}")
    print(f"  Value: {mem['value']}")
    print(f"  Confidence: {mem['confidence']}")
    print()

# Now query and see what gets retrieved
query = "Tell me everything you remember about this user"
print(f"\nQuery: '{query}'\n")

_, stats = ms.process_turn(query)
retrieved = stats.get('active_memories', [])

print(f"Total retrieved: {len(retrieved)} memories")
print(f"Total in Redis: {len(redis_mems)} memories")
print()

# Check if turn 10 memories were retrieved
turn_10_retrieved = [m for m in retrieved if m.get('origin_turn', 0) == 10]

if turn_10_retrieved:
    print("✓ Turn 10 memories WERE retrieved:")
    for mem in turn_10_retrieved:
        print(f"  - {mem.get('type')}: {mem.get('content', '')[:50]}")
else:
    print("✗ Turn 10 memories were NOT retrieved")
    print("\nRetrieved turns:")
    for mem in retrieved:
        turn = mem.get('origin_turn', 0)
        mtype = mem.get('type', 'unknown')
        content = mem.get('content', '')[:40]
        print(f"  Turn {turn:4d}: {mtype:12s} - {content}")

# Check semantic search specifically
print(f"\n{'='*70}")
print("SEMANTIC SEARCH ANALYSIS:")
print("="*70)

semantic_results = ms.vector_store.search_similar(
    query=query,
    limit=100,
    min_score=0.0,
    user_id=ms.user_id
)

print(f"Semantic search returned {len(semantic_results)} of {len(redis_mems)} memories\n")

turn_10_in_semantic = [r for r in semantic_results if r['memory'].get('turn_number', 0) == 10]

if turn_10_in_semantic:
    print("✓ Turn 10 found in semantic search:")
    for r in turn_10_in_semantic:
        mem = r['memory']
        score = r['score']
        print(f"  Score: {score:.4f} - {mem.get('value', '')[:50]}")
else:
    print("✗ Turn 10 NOT found in semantic search")
    print("This means semantic similarity is too low for Qdrant to return it")

print(f"\n{'='*70}")
print("GROUND TRUTH CHECK:")
print("="*70)

# Check ground truth expectation
gt = data['ground_truth_memories']
turn_10_gt = [g for g in gt if g['turn'] == 10]

if turn_10_gt:
    expected = turn_10_gt[0]
    print(f"Expected memory at turn 10:")
    print(f"  Type: {expected['type']}")
    print(f"  Value: {expected['value']}")
    print(f"  Message: {expected['message']}")
    print(f"\n  Ground truth KEY: '{expected['key']}'")
    print(f"  Ground truth VALUE: '{expected['value']}'")
    
    # Check if it matches any stored memory
    print(f"\n  Stored memories at turn 10:")
    for mem in turn_10_mems:
        print(f"    {mem['type']}: {mem['key']} = {mem['value']}")
        if expected['value'].lower() in mem['value'].lower() or mem['value'].lower() in expected['value'].lower():
            print(f"      ✓ MATCHES ground truth")
        else:
            print(f"      ✗ Different from ground truth")
