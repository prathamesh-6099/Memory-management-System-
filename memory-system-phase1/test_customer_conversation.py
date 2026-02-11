#!/usr/bin/env python3
"""
SAMPLE: Test Memory Extraction from Customer Service Conversation

This demonstrates how the memory system extracts information from a realistic
customer service conversation between an agent and Jennifer Martinez.

The system should extract:
- Entities: Names, company, dates, amounts
- Events: Payments, transactions
- Facts: Account numbers, payment methods

Run: python test_customer_conversation.py
"""

import logging
import sys
import time
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

from src import MemorySystem

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

def test_customer_conversation():
    """Test memory extraction from a customer service conversation"""
    
    print("\n" + "="*80)
    print("  CUSTOMER SERVICE CONVERSATION - MEMORY EXTRACTION TEST")
    print("="*80)
    
    # Initialize memory system for Jennifer Martinez
    print("\nInitializing memory system for Jennifer Martinez...")
    memory = MemorySystem(user_id="jennifer_martinez", enable_semantic_search=True)
    
    # Clear previous data
    memory.clear_memories()
    
    # Customer service conversation turns
    conversation = [
        {
            "speaker": "USER",
            "message": "Speaking. Who is this?"
        },
        {
            "speaker": "USER",
            "message": "A payment reminder? I already paid that bill three days ago!"
        },
        {
            "speaker": "USER",
            "message": "It's 3847."  # Account number last 4 digits
        },
        {
            "speaker": "USER",
            "message": "Sure."
        },
        {
            "speaker": "USER",
            "message": "So my payment went through then?"
        },
        {
            "speaker": "USER",
            "message": "Okay, good. I was worried something went wrong with my bank."
        },
        {
            "speaker": "USER",
            "message": "Yes, that's right."  # Confirming bank transfer
        },
        {
            "speaker": "USER",
            "message": "Alright, that's a relief. Thank you for checking."
        },
        {
            "speaker": "USER",
            "message": "No, I'm all set. Thanks for clarifying."
        },
        {
            "speaker": "USER",
            "message": "You too. Goodbye."
        },
        # Add some agent messages with context for the user
        {
            "speaker": "AGENT",
            "message": "Good evening, Ms. Martinez. This is David calling from National Payment Services."
        },
        {
            "speaker": "AGENT",
            "message": "Ms. Martinez, I can see you're correct. There is a payment of $650 that was submitted on February 7th."
        },
        {
            "speaker": "AGENT",
            "message": "Your payment method was a bank transfer, correct?"
        },
    ]
    
    print("\n" + "="*80)
    print("  Processing conversation turns...")
    print("="*80)
    
    total_extracted = 0
    total_stored = 0
    stage3_count = 0
    
    start_time = time.time()
    
    for i, turn in enumerate(conversation, 1):
        speaker = turn["speaker"]
        message = turn["message"]
        
        print(f"\n--- Turn {i} ({speaker}) ---")
        print(f'"{message}"')
        
        # Process the turn
        turn_start = time.time()
        memory_context, stats = memory.process_turn(
            user_message=message
        )
        turn_time_ms = (time.time() - turn_start) * 1000
        
        extracted = stats.get('extracted_count', 0)
        stored = stats.get('stored_count', 0)
        
        total_extracted += extracted
        total_stored += stored
        
        if extracted > 0:
            print(f"\n> EXTRACTED: {extracted} memories")
            stage3_count += 1
        else:
            print(f"\n> No memories extracted")
        
        print(f"> Processing time: {turn_time_ms:.2f}ms")
        print(f"  - Extraction: {stats.get('extraction_time_ms', 0):.2f}ms")
        print(f"  - Storage: {stats.get('storage_time_ms', 0):.2f}ms")
        print(f"  - Retrieval: {stats.get('retrieval_time_ms', 0):.2f}ms")
        print("-" * 80)
    
    total_time_ms = (time.time() - start_time) * 1000
    
    # Show all extracted memories
    print("\n" + "="*80)
    print("  EXTRACTED MEMORIES FROM CONVERSATION")
    print("="*80)
    
    all_memories = memory.redis_store.get_recent_memories(limit=100)
    
    if all_memories:
        print(f"\nTotal memories stored: {len(all_memories)}\n")
        
        # Group by type
        by_type = {}
        for mem in all_memories:
            mem_type = mem['type']
            if mem_type not in by_type:
                by_type[mem_type] = []
            by_type[mem_type].append(mem)
        
        for mem_type, mems in sorted(by_type.items()):
            print(f"\n[{mem_type.upper()}] ({len(mems)} memories):")
            for mem in mems:
                print(f"  - {mem['key']}: {mem['value']}")
                print(f"    Confidence: {mem['confidence']:.2f}, Turn: {mem['turn_number']}")
                print(f"    Source: \"{mem['source_text'][:60]}...\"")
    else:
        print("\nNo memories were extracted from this conversation.")
    
    # Performance metrics
    print("\n" + "="*80)
    print("  PERFORMANCE METRICS")
    print("="*80)
    
    print(f"\nTotal conversation turns: {len(conversation)}")
    print(f"Total memories extracted: {total_extracted}")
    print(f"Total memories stored: {total_stored}")
    print(f"Turns with extractions: {stage3_count}")
    print(f"Total processing time: {total_time_ms:.2f}ms")
    print(f"Average time per turn: {total_time_ms/len(conversation):.2f}ms")
    
    # LLM stats if available
    extractor = memory.extractor
    if hasattr(extractor, 'llm_extractor') and extractor.llm_extractor:
        llm = extractor.llm_extractor
        if llm.api_call_count > 0:
            avg_llm_response = llm.total_response_time_ms / llm.api_call_count
            print(f"\nLLM API Calls: {llm.api_call_count}")
            print(f"Average LLM response time: {avg_llm_response:.2f}ms")
            print(f"Total LLM response time: {llm.total_response_time_ms:.2f}ms")
    
    print("\n" + "="*80)
    print("  TEST COMPLETE")
    print("="*80)

if __name__ == "__main__":
    test_customer_conversation()
