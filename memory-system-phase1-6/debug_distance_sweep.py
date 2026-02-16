"""
Deep Diagnostic: Why is Distance Sweep Failing Completely?
Investigate extraction, storage, and retrieval in the distance sweep test
"""

import sys
import json
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from src.memory_system import MemorySystem

def main():
    print("\n🔬 DEEP DIAGNOSTIC: Distance Sweep Failure Investigation\n")
    print("="*80)
    
    # Load distance sweep test
    with open("evaluation/fixtures/distance_sweep_test.json") as f:
        test = json.load(f)
    
    print(f"Test Configuration:")
    print(f"  Query turn: {test['query_turn']}")
    print(f"  Total turns: {test['num_turns']}")
    print(f"  Target distances: {test['target_distances']}")
    print("\n"+"="*80)
    
    # Initialize memory system with fresh user ID to avoid any Redis collision
    import time
    fresh_user_id = f"diagnostic_distance_{int(time.time())}"
    ms = MemorySystem(user_id=fresh_user_id)
    ms.redis_store.clear_all_memories()  # Still clear just in case
    
    # Process all turns and track what gets stored
    print("\n📝 Processing turns and tracking memory storage...")
    print("-"*80)
    
    memories_by_turn = {}
    
    for turn_data in test['turns']:
        if turn_data.get('is_query'):
            continue
            
        turn_num = turn_data['turn']
        message = turn_data['message']
        has_memory_expected = turn_data.get('has_memory', False)
        is_test_marker = turn_data.get('is_test_marker', False)
        
        # Process the turn
        _, stats = ms.process_turn(message)
        stored_count = stats.get('stored_count', 0)
        
        if is_test_marker:
            print(f"\nTurn {turn_num:4d} (TEST MARKER):")
            print(f"  Message: '{message}'")
            print(f"  Expected memory: {has_memory_expected}")
            print(f"  Extracted: {stats.get('extracted_count', 0)}")
            print(f"  Stored: {stored_count}")
            
            if stored_count > 0:
                # Get the just-stored memories
                all_mems = ms.redis_store.get_all_memories()
                recent_mems = [m for m in all_mems if int(m['turn_number']) == turn_num]
                for mem in recent_mems:
                    print(f"    - {mem['type']}: {mem['key']} = {mem['value']}")
                memories_by_turn[turn_num] = recent_mems
            else:
                print(f"    ⚠️  NO MEMORIES STORED!")
                print(f"    Stats: {stats}")
    
    # Check what's in storage after all turns
    print("\n"+"="*80)
    print("\n💾 Final Storage State:")
    print("-"*80)
    
    all_memories = ms.redis_store.get_all_memories()
    print(f"Total memories in Redis: {len(all_memories)}")
    
    if all_memories:
        print("\nStored memories:")
        for mem in all_memories[:10]:  # Show first 10
            print(f"  Turn {mem['turn_number']:4d}: {mem['type']:12s} - {mem['value']}")
            
        # Check which test markers made it to storage
        test_marker_turns = [t['turn'] for t in test['turns'] if t.get('is_test_marker')]
        stored_test_turns = [int(m['turn_number']) for m in all_memories 
                            if int(m['turn_number']) in test_marker_turns]
        
        print(f"\nTest marker turns expected: {test_marker_turns}")
        print(f"Test marker turns stored:   {stored_test_turns}")
        print(f"Missing: {set(test_marker_turns) - set(stored_test_turns)}")
    else:
        print("  ⚠️  NO MEMORIES IN STORAGE!")
    
    # Try retrieval at query turn
    print("\n"+"="*80)
    print(f"\n🔍 Retrieval Test at Turn {test['query_turn']}:")
    print("-"*80)
    
    query = "Tell me everything you remember"
    retrieved = ms.retriever.retrieve(
        current_message=query,
        turn_number=test['query_turn'],
        priority_types=None
    )
    
    print(f"Retrieved {len(retrieved)} memories")
    
    if retrieved:
        print("\nTop 10 retrieved:")
        for i, mem in enumerate(retrieved[:10], 1):
            turn = mem['turn_number']
            turns_ago = test['query_turn'] - int(turn)
            print(f"  {i:2d}. Turn {turn:4d} ({turns_ago:4d} ago): "
                  f"{mem['type']:12s} - score={mem.get('retrieval_score', 0):.4f}")
    else:
        print("  ⚠️  NO MEMORIES RETRIEVED!")
        
        # Debug: Check semantic search
        if ms.vector_store:
            print("\n  Checking semantic search...")
            results = ms.vector_store.search(query, limit=10)
            print(f"  Vector store returned {len(results)} results")
    
    # Cleanup
    ms.redis_store.clear_all_memories()
    
    print("\n"+"="*80)
    print("\n✅ Diagnostic complete!\n")


if __name__ == "__main__":
    main()
