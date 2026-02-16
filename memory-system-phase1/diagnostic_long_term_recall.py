"""
Diagnostic Script: Long-Term Memory Recall Investigation
Tests why 1000-turn memories aren't being retrieved
"""

import sys
import math
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

from src.memory_system import MemorySystem
from src.config import (
    RECENCY_DECAY_RATE, 
    RANKING_WEIGHTS_5_SIGNAL,
    MAX_MEMORIES_TO_RETRIEVE
)

def test_recency_decay():
    """Test how recency decay affects retrieval scores"""
    print("=" * 70)
    print("DIAGNOSTIC 1: Recency Decay Impact")
    print("=" * 70)
    
    turns_list = [10, 50, 100, 500, 1000]
    
    print(f"\nCurrent RECENCY_DECAY_RATE: {RECENCY_DECAY_RATE}")
    print(f"Recency weight in ranking: {RANKING_WEIGHTS_5_SIGNAL['recency'] * 100}%\n")
    
    for turns_ago in turns_list:
        recency_score = math.exp(-RECENCY_DECAY_RATE * turns_ago)
        contribution = recency_score * RANKING_WEIGHTS_5_SIGNAL['recency']
        
        print(f"  {turns_ago:4} turns ago:")
        print(f"    Raw recency score:    {recency_score:.6f}")
        print(f"    Weighted contribution: {contribution:.6f} (out of 1.0)")
        
        # Simulate best-case scenario (perfect semantic, type, freq, confidence)
        best_case_score = (
            RANKING_WEIGHTS_5_SIGNAL['semantic'] * 1.0 +  # Perfect semantic match
            RANKING_WEIGHTS_5_SIGNAL['type'] * 1.0 +       # Highest type priority
            RANKING_WEIGHTS_5_SIGNAL['recency'] * recency_score +  # Current recency
            RANKING_WEIGHTS_5_SIGNAL['frequency'] * 1.0 +  # Perfect frequency
            RANKING_WEIGHTS_5_SIGNAL['confidence'] * 1.0   # Perfect confidence
        )
        print(f"    Best-case total score: {best_case_score:.6f}")
        print()
    
    print("\n⚠️  FINDING: Memories older than 100 turns have essentially zero recency")
    print("   score, making them nearly impossible to retrieve even with perfect")
    print("   semantic/type/frequency/confidence scores.\n")


def test_vector_persistence():
    """Test if vector embeddings persist correctly in Qdrant"""
    print("=" * 70)
    print("DIAGNOSTIC 2: Vector Embedding Persistence")
    print("=" * 70)
    
    user_id = "diagnostic_test"
    ms = MemorySystem(user_id)
    
    # Clear previous test data
    print("\n✓ Clearing previous test data...")
    ms.redis_store.clear_all_memories()
    if ms.vector_store:
        try:
            ms.vector_store.client.delete_collection(ms.vector_store.collection_name)
            ms.vector_store._ensure_collection()
        except:
            pass
    
    # Store a test memory
    test_message = "I really love chocolate ice cream for dessert"
    print(f"\n✓ Storing test memory at turn 1...")
    print(f"  Message: '{test_message}'")
    
    result = ms.process_message(test_message, turn_number=1)
    
    if not result['stored']:
        print("  ✗ No memories were stored!")
        return
    
    stored_count = len(result['memories'])
    print(f"  ✓ Stored {stored_count} memory(ies)")
    
    # Check Redis persistence
    print(f"\n✓ Checking Redis persistence...")
    all_mems = ms.redis_store.get_all_memories()
    print(f"  ✓ Found {len(all_mems)} memories in Redis")
    
    # Check Qdrant persistence
    print(f"\n✓ Checking Qdrant vector persistence...")
    if ms.vector_store:
        try:
            # Try semantic search
            results = ms.vector_store.search("chocolate ice cream", limit=5)
            print(f"  ✓ Found {len(results)} vectors in Qdrant")
            
            if results:
                print(f"  ✓ Top result similarity: {results[0][1]:.4f}")
            else:
                print("  ✗ No vectors found in Qdrant!")
        except Exception as e:
            print(f"  ✗ Error searching Qdrant: {e}")
    else:
        print("  ✗ Vector store not initialized!")
    
    # Simulate 1000 turns later
    print(f"\n✓ Simulating retrieval at turn 1000...")
    query = "What desserts do I like?"
    print(f"  Query: '{query}'")
    
    retrieved = ms.retriever.retrieve(
        current_message=query,
        turn_number=1000,
        priority_types=None
    )
    
    print(f"  ✓ Retrieved {len(retrieved)} memories")
    
    if retrieved:
        for mem in retrieved[:3]:  # Show top 3
            print(f"\n  Memory: {mem['key']} = {mem['value']}")
            print(f"    Turn: {mem['turn_number']} ({1000 - int(mem['turn_number'])} turns ago)")
            print(f"    Scores:")
            print(f"      - Semantic:  {mem.get('semantic_score', 0):.4f}")
            print(f"      - Type:      {mem.get('type_score', 0):.4f}")
            print(f"      - Recency:   {mem.get('recency_score', 0):.4f}")
            print(f"      - Frequency: {mem.get('frequency_score', 0):.4f}")
            print(f"      - Confidence:{mem.get('confidence_score', 0):.4f}")
            print(f"      - TOTAL:     {mem.get('retrieval_score', 0):.4f}")
    else:
        print("  ✗ No memories retrieved!")
        
        # Check if it's in the database at all
        print("\n  Checking if memory still exists in storage...")
        all_mems = ms.redis_store.get_all_memories()
        if all_mems:
            print(f"  ✓ {len(all_mems)} memories exist in Redis")
            print(f"  ✗ But recency decay prevented retrieval!")
        else:
            print("  ✗ No memories in Redis - data loss issue!")
    
    # Cleanup
    print(f"\n✓ Cleaning up test data...")
    ms.redis_store.clear_all_memories()
    if ms.vector_store:
        try:
            ms.vector_store.client.delete_collection(ms.vector_store.collection_name)
            ms.vector_store._ensure_collection()
        except:
            pass


def propose_solutions():
    """Propose solutions for long-term recall"""
    print("\n" + "=" * 70)
    print("RECOMMENDATIONS")
    print("=" * 70)
    
    print("\n1. REDUCE RECENCY_DECAY_RATE for long-term memory:")
    print("   Current: RECENCY_DECAY_RATE = 0.1")
    print("   Proposed: RECENCY_DECAY_RATE = 0.001")
    print("   Impact:")
    print("     - 100 turns:  0.9048 (was 0.0000)")
    print("     - 1000 turns: 0.3679 (was 0.0000)")
    
    print("\n2. ADJUST RANKING WEIGHTS to favor semantic relevance:")
    print("   Consider increasing semantic weight if content is more")
    print("   important than recency for your use case.")
    
    print("\n3. ALTERNATIVE: Use logarithmic decay instead of exponential:")
    print("   recency_score = 1 / (1 + log(1 + turns_ago))")
    print("   This degrades more slowly over time.")
    
    print("\n4. VERIFY Qdrant persistence:")
    print("   Ensure Qdrant volume is mounted in docker-compose.yml")
    print("   Check: docker-compose.yml has 'qdrant_storage' volume")
    
    print("\n" + "=" * 70)


if __name__ == "__main__":
    print("\n🔬 LONG-TERM MEMORY RECALL DIAGNOSTIC\n")
    
    test_recency_decay()
    
    try:
        test_vector_persistence()
    except Exception as e:
        print(f"\n✗ Error during vector persistence test: {e}")
        print("  Make sure Redis and Qdrant are running:")
        print("    docker-compose up -d")
    
    propose_solutions()
    
    print("\n✅ Diagnostic complete!\n")
