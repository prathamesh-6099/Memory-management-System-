#!/usr/bin/env python3
"""
Demo Script - Phase 1 Memory System
Tests the full extraction → storage → retrieval → injection pipeline
"""

import sys
import logging
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

from src import MemorySystem

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
)

logger = logging.getLogger(__name__)


def print_section(title: str):
    """Print a formatted section header"""
    print(f"\n{'='*70}")
    print(f"  {title}")
    print(f"{'='*70}\n")


def simulate_conversation():
    """Simulate a multi-turn conversation to test memory"""
    
    print_section("PHASE 1 MEMORY SYSTEM DEMO")
    
    # Initialize memory system
    logger.info("Initializing memory system...")
    memory_sys = MemorySystem(user_id="demo_user")
    
    # Check health
    health = memory_sys.health_check()
    print("System Health Check:")
    for component, status in health.items():
        print(f"  {component}: {'✓ OK' if status else '✗ FAILED'}")
    print()
    
    if not all(health.values()):
        print("⚠️  Some components are not healthy. Make sure Redis is running:")
        print("   docker-compose up -d")
        return
    
    # Simulate conversation
    conversation = [
        # Turn 1-5: Basic information
        "Hi, I'm Alice and I prefer to be called by my first name",
        "I work at Google as a software engineer",
        "My favorite programming language is Python",
        "I'm allergic to peanuts, so never suggest recipes with them",
        "I live in San Francisco",
        
        # Turn 6-10: More preferences and constraints
        "I always use dark mode for my IDE",
        "My manager is named Bob Chen",
        "I must deliver the Q1 report by March 15th",
        "I prefer concise answers without too much explanation",
        "Never send me emails after 6 PM",
        
        # Turn 11-15: Noise (should be filtered)
        "okay",
        "thanks",
        "cool",
        "nice",
        "got it",
        
        # Turn 16-20: More meaningful information
        "I'm committed to learning Rust this year",
        "Always format code using Black formatter",
        "I love hiking on weekends",
        "My timezone is PST",
        "I have a meeting with Sarah every Monday at 10 AM",
    ]
    
    print_section("SIMULATING CONVERSATION (20 TURNS)")
    
    for i, user_message in enumerate(conversation, 1):
        print(f"\n--- Turn {i} ---")
        print(f"User: {user_message}")
        
        # Process turn (extract + store + retrieve)
        memory_context, stats = memory_sys.process_turn(user_message)
        
        # Show extraction results
        if stats['extracted_count'] > 0:
            print(f"✓ Extracted {stats['extracted_count']} memories")
            print(f"✓ Stored {stats['stored_count']} new memories")
        else:
            print("○ No memories extracted (filtered)")
        
        print(f"📊 Total memories: {stats['total_memories']}")
    
    # Show final statistics
    print_section("FINAL STATISTICS")
    final_stats = memory_sys.get_statistics()
    
    print(f"Total Turns: {final_stats['total_turns']}")
    print(f"Total Memories Stored: {final_stats['total_memories']}")
    print(f"Total Extractions: {final_stats['extraction_count']}")
    print(f"\nMemories by Type:")
    for mem_type, count in sorted(final_stats['memories_by_type'].items()):
        print(f"  {mem_type}: {count}")
    
    # Test retrieval with specific queries
    print_section("TESTING RETRIEVAL")
    
    test_queries = [
        ("Can you suggest a snack?", "Should retrieve allergy constraint"),
        ("What's my manager's name?", "Should retrieve entity info"),
        ("When is the Q1 report due?", "Should retrieve commitment"),
        ("Format this code for me", "Should retrieve formatting instruction"),
    ]
    
    for query, expected in test_queries:
        print(f"\nQuery: '{query}'")
        print(f"Expected: {expected}")
        print("-" * 70)
        
        memory_context = memory_sys.get_prompt_context(query)
        
        if memory_context:
            # Show just the retrieved long-term memories section
            if "LONG-TERM MEMORY" in memory_context:
                ltm_section = memory_context.split("LONG-TERM MEMORY")[1]
                print(ltm_section.strip()[:500])  # First 500 chars
            else:
                print("(No long-term memories retrieved)")
        else:
            print("(No memory context)")
    
    # Show core memory
    print_section("CORE MEMORY (ALWAYS INJECTED)")
    print(memory_sys.flat_file_store.read_core_memory())
    
    # Demonstrate core memory update
    print_section("UPDATING CORE MEMORY")
    print("Updating user name in CORE.md...")
    memory_sys.update_core_memory("CORE.md", "Identity", "Name", "Alice")
    print("\nUpdated CORE.md:")
    print(memory_sys.flat_file_store.read_core_memory())
    
    print_section("DEMO COMPLETE")
    print("✓ Phase 1 implementation is working!")
    print("\nNext steps:")
    print("  - Phase 2: Add vector store + semantic search")
    print("  - Phase 3: Add LLM-based extraction")
    print("  - Phase 4: Add consolidation worker")
    print()


if __name__ == "__main__":
    try:
        simulate_conversation()
    except KeyboardInterrupt:
        print("\n\nDemo interrupted by user")
    except Exception as e:
        logger.error(f"Demo failed: {e}", exc_info=True)
        sys.exit(1)
