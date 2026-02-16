"""Check vector storage completeness"""
import json
from src.memory_system import MemorySystem

# Initialize
ms = MemorySystem('test_vector_storage')
ms.clear_memories()

# Load and process
with open('evaluation/fixtures/distance_sweep_test.json') as f:
    data = json.load(f)

# Process all turns and track storage
print("Processing conversation and tracking storage...\n")
target_turns = [10, 510, 910, 960, 1000]

for turn in data['turns']:
    if turn.get('is_query'):
        continue
    
    turn_num = turn['turn']
    _, stats = ms.process_turn(turn['message'])
    
    if turn_num in target_turns:
        extracted = stats.get('extracted_count', 0)
        stored = stats.get('stored_count', 0)
        vector_stored = stats.get('vector_stored_count', 0)
        
        print(f"Turn {turn_num:4d}:")
        print(f"  Extracted: {extracted}, Stored in Redis: {stored}, Stored in Vector: {vector_stored}")

#Check what's in Redis vs Vector Store
print(f"\n{'='*60}")
print("STORAGE COMPARISON")
print(f"{'='*60}\n")

redis_mems = ms.redis_store.get_all_memories()
print(f"Redis: {len(redis_mems)} total memories")
for mem in redis_mems:
    turn = int(mem.get('turn_number', 0))
    if turn in target_turns:
        mtype = mem.get('type', 'unknown')
        value = mem.get('value', '')[:30]
        print(f"  Turn {turn:4d}: {mtype:12s} - {value}")

# Check vector store by searching with no filter
if ms.vector_store:
    print(f"\nVector Store: Searching for all user memories...")
    all_vectors = ms.vector_store.search_similar(
        query="everything",  # Generic query
        limit=100,
        min_score=0.0,
        user_id=ms.user_id
    )
    
    print(f"Vector Store: {len(all_vectors)} memories found")
    target_vector_mems = [v for v in all_vectors if v['memory'].get('turn_number', 0) in target_turns]
    
    for v in sorted(target_vector_mems, key=lambda x: -x['memory'].get('turn_number', 0)):
        mem = v['memory']
        turn = mem.get('turn_number', 0)
        mtype = mem.get('memory_type', 'unknown')
        value = mem.get('value', '')[:30]
        print(f"  Turn {turn:4d}: {mtype:12s} - {value}")
    
    print(f"\n⚠️  Missing from vector store: {len([t for t in target_turns if not any(v['memory'].get('turn_number')==t for v in all_vectors)])}")
