"""Debug semantic search behavior"""
import json
from src.memory_system import MemorySystem

# Initialize
ms = MemorySystem('test_semantic_debug')
ms.clear_memories()

# Load and process
with open('evaluation/fixtures/distance_sweep_test.json') as f:
    data = json.load(f)

# Process all turns
print("Processing conversation...")
for turn in data['turns']:
    if not turn.get('is_query'):
        ms.process_turn(turn['message'])

print(f"\nTotal memories in Redis: {len(ms.redis_store.get_all_memories())}")

# Now do semantic search directly
query = "Tell me everything you remember"
print(f"\nQuery: '{query}'\n")

# Direct semantic search
if ms.vector_store:
    semantic_results = ms.vector_store.search_similar(
        query=query,
        limit=100,
        min_score=0.0,  # NO threshold
        user_id=ms.user_id
    )
    
    print(f"Semantic search returned {len(semantic_results)} results:")
    target_turns = [1000, 960, 910, 510, 10]
    
    for i, result in enumerate(semantic_results[:20], 1):
        memory = result['memory']
        score = result['score']
        turn = memory.get('turn_number', 0)
        mtype = memory.get('memory_type', 'unknown')
        value = memory.get('value', '')[:40]
        
        marker = "🎯" if turn in target_turns else "  "
        print(f"{marker} {i:2d}. Turn {turn:4d} (score={score:.3f}): {mtype:12s} - {value}")
