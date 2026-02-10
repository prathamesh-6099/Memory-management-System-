# Long-Form Memory System - Phase 1

A production-grade memory system for AI agents that enables accurate recall across 1,000+ conversation turns.

## What This Is

This is **Phase 1** of a 6-phase implementation plan for a complete long-form memory system. Phase 1 provides a working end-to-end prototype with:

- ✅ Flat file storage for Core Memory (always-injected user identity)
- ✅ Redis storage for Long-Term Memory (persistent across sessions)
- ✅ Two-stage extraction pipeline (heuristic filter + pattern-based classifier)
- ✅ Basic retrieval (type-priority + recency-based)
- ✅ Automated deduplication
- ✅ Full memory pipeline: Extract → Store → Retrieve → Inject

## Quick Start

### 1. Prerequisites

- Python 3.8+
- Docker and Docker Compose (for Redis)

### 2. Setup

```bash
# Clone/navigate to the project directory
cd memory-system

# Install Python dependencies
pip install -r requirements.txt

# Start Redis
docker-compose up -d

# Verify Redis is running
docker-compose ps
```

### 3. Run the Demo

```bash
python demo.py
```

The demo will:
1. Simulate a 20-turn conversation
2. Extract and store memories
3. Test retrieval with different queries
4. Show statistics and final state

## Project Structure

```
memory-system/
├── docker-compose.yml          # Redis setup
├── redis.conf                  # Redis configuration (AOF persistence)
├── requirements.txt            # Python dependencies
├── demo.py                     # Demo script
├── memory/                     # Flat file storage
│   └── user_1/                # Per-user directory
│       ├── CORE.md            # Core identity (always injected)
│       ├── PREFERENCES.md     # User preferences
│       ├── INSTRUCTIONS.md    # Behavioral instructions
│       └── CONSTRAINTS.md     # Hard constraints
└── src/                       # Source code
    ├── __init__.py
    ├── config.py              # Configuration & tunable parameters
    ├── flat_file_store.py     # Flat file storage layer
    ├── redis_store.py         # Redis storage layer
    ├── extractor.py           # Memory extraction (Stage 1 & 2)
    ├── retriever.py           # Memory retrieval
    └── memory_system.py       # Main orchestrator
```

## Usage

### Basic Usage

```python
from src import MemorySystem

# Initialize for a user
memory = MemorySystem(user_id="alice")

# Process each conversation turn
for user_message in conversation:
    memory_context, stats = memory.process_turn(user_message)
    
    # Inject memory_context into your LLM prompt
    prompt = f"""
    {memory_context}
    
    User: {user_message}
    Assistant: 
    """
    
    # Generate response with your LLM
    response = your_llm(prompt)
```

### Retrieval Only

```python
# Get memory context without processing the turn
memory_context = memory.get_prompt_context(
    user_message="What's my manager's name?",
    priority_types=["entity", "preference"]
)
```

### Update Core Memory

```python
# Update a field in core identity
memory.update_core_memory(
    file="CORE.md",
    section="Identity", 
    field="Name",
    value="Alice"
)
```

### Statistics

```python
stats = memory.get_statistics()
print(f"Total memories: {stats['total_memories']}")
print(f"Memories by type: {stats['memories_by_type']}")
```

## How It Works

### Memory Layers

1. **Core Memory** (Flat Files)
   - Always injected into every prompt
   - Contains: name, language, timezone, core preferences
   - Human-readable Markdown files
   - ~200-500 tokens

2. **Long-Term Memory** (Redis)
   - Selectively retrieved based on current message
   - Contains: preferences, constraints, entities, commitments
   - Indexed by type and recency
   - ~500 tokens budget

### Extraction Pipeline (Phase 1)

**Stage 1: Sensory Filter** (Heuristic)
- Fast pattern matching
- Filters out ~60% of turns (greetings, acknowledgments)
- Weighted scoring: length, keywords, questions, specificity

**Stage 2: Pattern-Based Classifier**
- Regex patterns for each memory type
- Extracts key-value pairs
- Assigns confidence scores
- Types: preference, constraint, entity, instruction, commitment, fact

**Stage 3: LLM Extraction** _(Phase 3)_
- Not yet implemented
- Will use LLM for complex extraction

### Retrieval Strategy (Phase 1)

1. **Always-On Types**: constraint, instruction (always retrieved)
2. **Recency**: Recent memories with exponential decay
3. **Priority Types**: User-specified types to prioritize

**Phase 2** will add semantic similarity search using embeddings.

### Deduplication

- Redis dedup index: `{type}:{key}` → `memory_id`
- Prevents storing identical memories
- Updates recency of existing memories instead

## Configuration

All tunable parameters are in `src/config.py`:

| Parameter | Default | Description |
|-----------|---------|-------------|
| `SENSORY_FILTER_THRESHOLD` | 0.3 | Minimum score to pass heuristic filter |
| `EXTRACTION_CLASSIFIER_THRESHOLD` | 0.6 | Minimum confidence to store memory |
| `MAX_MEMORIES_TO_RETRIEVE` | 10 | Top K memories to inject |
| `MEMORY_TOKEN_BUDGET` | 500 | Max tokens for retrieved memories |
| `CORE_MEMORY_TOKEN_BUDGET` | 500 | Max tokens for core memory |

## What's Implemented (Phase 1)

- ✅ Flat file storage with human-editable Markdown
- ✅ Redis storage with AOF persistence
- ✅ Two-stage extraction (heuristic + pattern classifier)
- ✅ Type-based and recency-based retrieval
- ✅ Deduplication
- ✅ Memory indices (type, recency)
- ✅ Full pipeline orchestration
- ✅ Statistics and monitoring

## What's Coming Next

### Phase 2 (Weeks 3-4)
- Vector store (pgvector or Qdrant)
- Embedding generation
- Semantic similarity search
- Multi-signal ranking (semantic + type + recency)

### Phase 3 (Weeks 5-6)
- LLM-based extraction (Stage 3)
- Improved deduplication
- Confidence scoring

### Phase 4 (Weeks 7-8)
- Background consolidation worker
- Memory merging and decay
- Promotion to Core Memory

### Phase 5 (Weeks 9-10)
- Evaluation framework
- Synthetic test generator
- Regression test suites

### Phase 6 (Weeks 11-12)
- Parameter tuning
- Production monitoring
- Performance optimization

## Testing

The `demo.py` script serves as both a demo and a basic test:

```bash
python demo.py
```

It validates:
- Extraction accuracy (should extract ~15-20 memories from 20 turns)
- Filtering effectiveness (should filter ~5 empty turns)
- Storage persistence
- Retrieval relevance
- Deduplication

## Troubleshooting

### Redis Connection Error

```
redis.exceptions.ConnectionError: Error connecting to Redis
```

**Solution**: Make sure Redis is running:
```bash
docker-compose up -d
docker-compose ps  # Should show redis as "Up"
```

### No Memories Extracted

If the demo shows 0 memories extracted, check:
1. Extraction thresholds in `config.py`
2. Pattern matching in `extractor.py`
3. Enable DEBUG logging to see filtering decisions

### Memory Not Retrieved

If memories are stored but not retrieved:
1. Check retrieval strategy in `retriever.py`
2. Verify memory types match priority types
3. Check token budget limits

## Architecture Notes

This implementation follows the spec in `LONG_FORM_MEMORY_SYSTEM_Version2.md`:

- **Context ≠ Memory**: Context is ephemeral (current window), Memory is persistent
- **Five-stage memory pipeline**: Sensory → Encoding → Storage → Retrieval → Forgetting
- **Human-like memory model**: Inspired by cognitive science research
- **Forgetting is essential**: Phase 4 will add decay and consolidation

## Performance

Phase 1 targets:
- Extraction: ~200ms per turn (async, invisible to user)
- Retrieval: <50ms per turn (blocks response generation)
- Storage: Redis + flat files, <10ms per operation

## License

This is a reference implementation based on the memory system specification.

## Contributing

This is Phase 1. Contributions welcome for:
- Bug fixes
- Performance improvements
- Documentation
- Test cases

Future phases will be implemented incrementally on this foundation.
