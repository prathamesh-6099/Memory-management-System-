"""Check if turn 510 exists in vector store without user filter"""
import json
from src.memory_system import MemorySystem

# Initialize
ms = MemorySystem('test_vector_filter')
ms.clear_memories()

# Load and process
with open('evaluation/fixtures/distance_sweep_test.json') as f:
    data = json.load(f)

# Process all turns
for turn in data['turns']:
    if not turn.get('is_query'):
        ms.process_turn(turn['message'])

print(f"User ID: {ms.user_id}\n")

# Search WITH user_id filter
print("WITH user_id filter:")
with_filter = ms.vector_store.search_similar(
    query="TechCorp tech lead company work",
    limit=10,
    min_score=0.0,
    user_id=ms.user_id
)
print(f"  Found {len(with_filter)} results")
for r in with_filter:
    mem = r['memory']
    print(f"    Turn {mem.get('turn_number')}: {mem.get('value', '')[:40]}")

# Search WITHOUT user_id filter
print("\nWITHOUT user_id filter (user_id=None):")
without_filter = ms.vector_store.search_similar(
    query="TechCorp tech lead company work",
    limit=10,
    min_score=0.0,
    user_id=None  # No filter
)
print(f"  Found {len(without_filter)} results")
for r in without_filter:
    mem = r['memory']
    print(f"    Turn {mem.get('turn_number')}: user={mem.get('user_id', 'NONE')} - {mem.get('value', '')[:40]}")

# Get all memories from vector store with no query
print("\nDirect Qdrant search for turn 510...")
try:
    from qdrant_client import models
    # Search by metadata filter
    results = ms.vector_store.client.scroll(
        collection_name=ms.vector_store.collection_name,
        scroll_filter=models.Filter(
            must=[
                models.FieldCondition(
                    key="turn_number",
                    match=models.MatchValue(value=510)
                )
            ]
        ),
        limit=10
    )
    
    points = results[0]  # (points, next_page_offset)
    print(f"  Found {len(points)} point(s) with turn_number=510")
    for point in points:
        print(f"    ID: {point.id}")
        print(f"    Payload: {point.payload}")
except Exception as e:
    print(f"  Error: {e}")
