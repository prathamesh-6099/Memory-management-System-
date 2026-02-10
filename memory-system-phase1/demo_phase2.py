#!/usr/bin/env python3
"""
Phase 2 Demo - Semantic Search & Multi-Signal Ranking

This demo showcases Phase 2 features:
1. Vector store (Qdrant) for semantic search
2. Embedding generation with sentence-transformers
3. Semantic similarity search
4. Multi-signal ranking (semantic + type + recency)

Prerequisites:
- Redis running (docker-compose up -d)
- Qdrant running (docker-compose up -d)
- pip install -r requirements.txt
"""

import logging
import time
import sys

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def print_header(text: str):
    """Print a formatted header"""
    print(f"\n{'='*70}")
    print(f" {text}")
    print('='*70)


def print_subheader(text: str):
    """Print a formatted subheader"""
    print(f"\n--- {text} ---")


def demo_phase2():
    """Run the Phase 2 demonstration"""
    
    print_header("PHASE 2 DEMO: Semantic Search & Multi-Signal Ranking")
    
    # Check if Phase 2 dependencies are available
    try:
        from sentence_transformers import SentenceTransformer
        from qdrant_client import QdrantClient
        print("✓ Phase 2 dependencies available")
    except ImportError as e:
        print(f"✗ Missing Phase 2 dependencies: {e}")
        print("  Install with: pip install -r requirements.txt")
        sys.exit(1)
    
    # Import our modules
    from src import MemorySystem
    from src.config import RANKING_WEIGHTS, TYPE_PRIORITIES
    
    print_subheader("Configuration")
    print(f"Ranking Weights: {RANKING_WEIGHTS}")
    print(f"Type Priorities: {TYPE_PRIORITIES}")
    
    # Initialize memory system with semantic search enabled
    print_subheader("Initializing Memory System")
    try:
        memory = MemorySystem(user_id="phase2_demo", enable_semantic_search=True)
    except Exception as e:
        print(f"✗ Failed to initialize: {e}")
        print("\nMake sure Redis and Qdrant are running:")
        print("  docker-compose up -d")
        sys.exit(1)
    
    # Check health
    health = memory.health_check()
    print(f"Health Check: {health}")
    
    if not health.get('redis'):
        print("✗ Redis not available")
        sys.exit(1)
    
    if health.get('vector_store') is False:
        print("✗ Qdrant not available")
        sys.exit(1)
    
    # Clear previous demo data
    print_subheader("Clearing Previous Demo Data")
    memory.clear_memories()
    
    # Sample conversation with rich information
    print_subheader("Processing Sample Conversation")
    
    conversation = [
        # Personal info
        "My name is Alex and I'm a software engineer at Google.",
        "I live in San Francisco and work remotely most days.",
        
        # Preferences
        "I prefer Python over JavaScript for backend work.",
        "I really enjoy hiking and photography on weekends.",
        "My favorite programming language is Rust for systems programming.",
        
        # Constraints
        "I can't eat gluten because I have celiac disease.",
        "I must attend standup meetings at 10am every day.",
        
        # Entities
        "My manager is named Sarah Chen.",
        "My project is called 'Project Atlas' - it's a cloud migration tool.",
        
        # Instructions
        "Always remind me about deadlines a day in advance.",
        "When I ask about code, give examples in Python first.",
        
        # Facts
        "I studied computer science at Stanford University.",
        "I've been programming for about 15 years now.",
        
        # Commitments
        "I have a code review deadline this Friday.",
        "I promised to mentor a junior developer starting next week.",
        
        # More preferences for semantic search testing
        "I like using VS Code with Vim keybindings.",
        "Coffee is essential - I drink at least 3 cups a day.",
        "I prefer dark mode for all my development tools.",
        "Working late at night is when I'm most productive.",
    ]
    
    # Process each message
    for i, message in enumerate(conversation):
        memory_context, stats = memory.process_turn(message)
        print(f"Turn {i+1}: Extracted={stats['extracted_count']}, Stored={stats['stored_count']}")
    
    # Show statistics
    print_subheader("Memory Statistics")
    stats = memory.get_statistics()
    print(f"Total turns: {stats['total_turns']}")
    print(f"Total memories: {stats['total_memories']}")
    print(f"Vector count: {stats.get('vector_count', 'N/A')}")
    print(f"Semantic search enabled: {stats['semantic_search_enabled']}")
    print(f"Memories by type: {stats['memories_by_type']}")
    
    # Test semantic search with various queries
    print_subheader("Testing Semantic Search")
    
    test_queries = [
        # Direct match
        ("What's my name?", "Should find 'Alex' entity"),
        
        # Semantic similarity (not exact match)
        ("What should I eat for lunch?", "Should find gluten constraint (allergies)"),
        ("Tell me about my work", "Should find Google, Project Atlas, Sarah"),
        ("What are my hobbies?", "Should find hiking, photography"),
        ("When am I most focused?", "Should find 'working late at night'"),
        ("What editor do I use?", "Should find VS Code"),
        ("What beverages do I like?", "Should find coffee preference"),
        
        # Abstract queries
        ("Help me be more productive", "Should find work preferences, deadlines"),
        ("What meetings do I have?", "Should find standup at 10am"),
    ]
    
    for query, expected in test_queries:
        print(f"\n📝 Query: '{query}'")
        print(f"   Expected: {expected}")
        
        # Get memory context for query
        start_time = time.time()
        context = memory.get_prompt_context(query)
        elapsed = (time.time() - start_time) * 1000
        
        print(f"   Time: {elapsed:.1f}ms")
        
        # Show retrieved memories (abbreviated)
        if context:
            lines = context.split('\n')
            memory_lines = [l for l in lines if l.startswith('- ')]
            print(f"   Retrieved {len(memory_lines)} memories:")
            for line in memory_lines[:3]:  # Show first 3
                print(f"     {line[:80]}...")
        else:
            print("   No memories retrieved")
    
    # Demonstrate multi-signal ranking
    print_subheader("Multi-Signal Ranking Demonstration")
    print("""
The retrieval system combines three signals:

1. SEMANTIC SCORE (50%): How similar is the query to the memory?
   - Uses sentence-transformers for embedding generation
   - Cosine similarity between query and memory vectors

2. TYPE PRIORITY (25%): How important is this memory type?
   - Constraints: 1.0 (highest - safety critical)
   - Instructions: 0.95 (very high - behavioral)
   - Commitments: 0.8 (time-sensitive)
   - Preferences: 0.7 (user experience)
   - Entities: 0.6 (context)
   - Facts: 0.5 (general knowledge)
   - Events: 0.4 (lowest)

3. RECENCY SCORE (25%): How recent is the memory?
   - Exponential decay based on turns ago
   - Recent memories score higher
""")
    
    # Show a detailed retrieval with scores
    print_subheader("Detailed Retrieval Example")
    
    # Access the retriever directly to see scores
    query = "What dietary restrictions do I have?"
    print(f"Query: '{query}'\n")
    
    memories = memory.retriever.retrieve(query, memory.turn_number)
    
    print(f"{'Memory':<40} {'Semantic':>8} {'Type':>8} {'Recency':>8} {'Final':>8}")
    print("-" * 80)
    
    for mem in memories[:5]:  # Top 5
        key = mem.get('key', 'unknown')[:35]
        semantic = mem.get('semantic_score', 0)
        type_score = mem.get('type_score', 0)
        recency = mem.get('recency_score', 0)
        final = mem.get('retrieval_score', 0)
        
        print(f"{key:<40} {semantic:>8.3f} {type_score:>8.3f} {recency:>8.3f} {final:>8.3f}")
    
    print_subheader("Demo Complete!")
    print("""
Phase 2 Features Demonstrated:
✓ Vector store (Qdrant) for memory embeddings
✓ Embedding generation with sentence-transformers
✓ Semantic similarity search
✓ Multi-signal ranking (semantic + type + recency)

To compare with Phase 1 (non-semantic), run:
  memory = MemorySystem(user_id="test", enable_semantic_search=False)
""")


if __name__ == "__main__":
    demo_phase2()
