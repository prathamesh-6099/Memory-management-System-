# Long-Form Memory System - Phase 1, 2, 3 & 4

A production-grade memory system for AI agents that enables accurate recall across 1,000+ conversation turns.

## What This Is

This is **Phase 1, 2, 3 & 4** of a 6-phase implementation plan for a complete long-form memory system.

### Phase 1 Features:
- ✅ Flat file storage for Core Memory (always-injected user identity)
- ✅ Redis storage for Long-Term Memory (persistent across sessions)
- ✅ Two-stage extraction pipeline (heuristic filter + pattern-based classifier)
- ✅ Basic retrieval (type-priority + recency-based)
- ✅ Automated deduplication
- ✅ Full memory pipeline: Extract → Store → Retrieve → Inject

### Phase 2 Features:
- ✅ Vector store (Qdrant) for semantic search
- ✅ Embedding generation with sentence-transformers
- ✅ Semantic similarity search
- ✅ Multi-signal ranking (semantic + type + recency)

### Phase 3 Features:
- ✅ Stage 3 LLM-based extraction for complex cases
- ✅ Multi-provider support (OpenAI, Anthropic, Groq)
- ✅ Semantic deduplication using vector similarity
- ✅ Memory updates and superseding
- ✅ Confidence scoring with certainty modifiers
- ✅ Confidence boosting for repeated mentions

### Phase 4 Features:
- ✅ Background consolidation worker
- ✅ Memory decay for old/unused memories
- ✅ Memory merging for similar content
- ✅ Promotion to Core Memory
- ✅ 5-signal ranking (semantic + type + recency + frequency + confidence)
- ✅ Access tracking for frequency scoring

> **Status:** All 4 phases verified working as of February 2026

## Quick Start

### 1. Prerequisites

- Python 3.8+
- Docker and Docker Compose (for Redis and Qdrant)

### 2. Setup

```bash
# Clone/navigate to the project directory
cd memory-system

# Install Python dependencies
pip install -r requirements.txt

# Start Redis and Qdrant
docker-compose up -d

# Verify services are running
docker-compose ps
```

### 3. Run the Demo

```bash
# Set your LLM API key(s) first:
# For Groq (fastest, recommended): 
#   Single key: set GROQ_API_KEY=your_key_here
#   Multiple keys for rate limit rotation: 
#     set GROQ_API_KEY_1=your_first_key
#     set GROQ_API_KEY_2=your_second_key
# For OpenAI: set OPENAI_API_KEY=your_key_here
# For Anthropic: set ANTHROPIC_API_KEY=your_key_here

# Phase 4 demo (consolidation & 5-signal ranking)
python demo_phase4.py

# Comprehensive test (all phases, 120+ turns, 3 consolidation cycles)
python test_all_phases.py

# Full conversation test (60-turn customer service scenario with active memory tracking)
python test_customer_conversation.py

# Active memory tracking demo (10-turn demonstration)
python demo_active_memories.py

# Simple active memory example (5 turns)
python example_active_memories.py
```

The demos demonstrate:

**demo_phase4.py**:
1. Full 4-phase system with LLM extraction
2. Semantic search and 5-signal ranking
3. Background consolidation triggering
4. Memory decay, merging, and promotion

**test_all_phases.py** (comprehensive):
1. Process 120+ conversation turns with 60+ extractable memories
2. Trigger automatic consolidation 3 times (at turns 50, 100, 150)
3. Demonstrate all 4 phases working together
4. Show memory decay, merging, and promotion to core memory
5. Test 5-signal ranking with various query types
6. Multi-API key rotation (avoids rate limits)

**test_customer_conversation.py**:
1. Realistic 60-turn customer service conversation
2. Extract customer information, preferences, and transaction details
3. Demonstrate active memory tracking at each turn
4. Show which memories influenced each response with full metadata

**demo_active_memories.py**:
1. 10-turn conversation showing memory tracking
2. Exposes which memories influenced each response
3. Shows memory evolution: origin_turn, last_used_turn, access_count
4. Demonstrates memory persistence across turns

## Project Structure

```
memory-system-phase1/
├── docker-compose.yml          # Redis + Qdrant setup
├── redis.conf                  # Redis configuration (AOF persistence)
├── requirements.txt            # Python dependencies
├── .env.example                # Environment variable template
├── .gitignore                  # Git ignore patterns
├── demo_phase4.py              # Phase 4 demo (consolidation)
├── test_all_phases.py          # Comprehensive test (120+ turns)
├── test_customer_conversation.py  # Customer service test (60 turns)
├── demo_active_memories.py     # Active memory tracking demo
├── example_active_memories.py  # Simple active memory example
├── memory/                     # Flat file storage
│   └── user_1/                 # Per-user directory
│       ├── CORE.md             # Core identity (always injected)
│       ├── PREFERENCES.md      # User preferences
│       ├── INSTRUCTIONS.md     # Behavioral instructions
│       └── CONSTRAINTS.md      # Hard constraints
└── src/                        # Source code
    ├── __init__.py
    ├── config.py               # Configuration & tunable parameters
    ├── flat_file_store.py      # Flat file storage layer
    ├── redis_store.py          # Redis storage layer (with superseding)
    ├── extractor.py            # Memory extraction (Stage 1, 2 & 3)
    ├── llm_extractor.py        # Phase 3: LLM-based extraction (multi-key support)
    ├── retriever.py            # Memory retrieval (5-signal ranking)
    ├── memory_system.py        # Main orchestrator (with active memory tracking)
    ├── embedding_service.py    # Phase 2: Embedding generation
    ├── vector_store.py         # Phase 2: Qdrant vector store
    └── consolidation_worker.py # Phase 4: Background consolidation
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
    
    # Access active memories that influenced this response
    active_memories = stats.get('active_memories', [])
    for mem in active_memories:
        print(f"Memory {mem['memory_id']} influenced response:")
        print(f"  Content: {mem['content']}")
        print(f"  Origin: Turn {mem['origin_turn']}")
        print(f"  Last Used: Turn {mem['last_used_turn']}")
        print(f"  Confidence: {mem['confidence']:.2f}")
    
    # Inject memory_context into your LLM prompt
    prompt = f"""
    {memory_context}
    
    User: {user_message}
    Assistant: 
    """
    
    # Generate response with your LLM
    response = your_llm(prompt)
```

### Active Memory Tracking

The system exposes which memories influenced each response:

```python
# Process a turn
_, stats = memory.process_turn("What are my scheduling preferences?")

# Get active memories
active_memories = stats['active_memories']

# Example output:
# [
#   {
#     "memory_id": "mem_0142",
#     "content": "call_preference: after 11 AM",
#     "type": "preference",
#     "origin_turn": 1,
#     "last_used_turn": 412,
#     "confidence": 0.95,
#     "mention_count": 1,
#     "access_count": 15
#   }
# ]
```

This allows you to:
- Track which memories influenced each response
- Debug retrieval behavior  
- Audit memory usage over time
- Validate memory relevance

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

### Extraction Pipeline (Phase 1 & 3)

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
- Uses OpenAI, Anthropic, or Groq for complex extraction
- Escalates when Stage 2 confidence < 0.7 or no results
- Structured JSON extraction with confidence scores
- Detects memory updates and contradictions
- Target latency: ~1-3s (Groq), ~200-500ms (standard APIs)

### Retrieval Strategy

#### Phase 1 (Basic Retrieval)
1. **Always-On Types**: constraint, instruction (always retrieved)
2. **Recency**: Recent memories with exponential decay
3. **Priority Types**: User-specified types to prioritize

#### Phase 2 (Semantic Search + Multi-Signal Ranking)

Phase 2 uses a **multi-signal ranking** formula that combines three signals:

```
final_score = w_semantic × semantic_score + w_type × type_priority + w_recency × recency_score
```

| Signal | Weight | Description |
|--------|--------|-------------|
| **Semantic** | 0.5 | Cosine similarity between query and memory embeddings |
| **Type Priority** | 0.25 | Memory type importance (constraints > instructions > preferences) |
| **Recency** | 0.25 | Exponential decay based on turns since memory creation |

**Type Priority Values:**
- constraint: 1.0 (highest - safety critical)
- instruction: 0.95 (behavioral guidance)
- commitment: 0.8 (time-sensitive)
- preference: 0.7 (user experience)
- entity: 0.6 (context)
- fact: 0.5 (general knowledge)
- event: 0.4 (lowest)

### Deduplication (Phase 1 & 3)

**Phase 1: Key-Based Deduplication**
- Redis dedup index: `{type}:{key}` → `memory_id`
- Prevents storing identical memories
- Updates recency of existing memories instead

**Phase 3: Semantic Deduplication**
- Uses vector similarity (cosine score > 0.92 = duplicate)
- Catches near-duplicates with different wording:
  - "I prefer calls after 11 AM"
  - "Call me after 11 in the morning"
- Boosts confidence when repeated
- Supersedes old memories when updates detected

## Configuration

All tunable parameters are in `src/config.py`:

### Phase 1 Parameters

| Parameter | Default | Description |
|-----------|---------|-------------|
| `SENSORY_FILTER_THRESHOLD` | 0.3 | Minimum score to pass heuristic filter |
| `EXTRACTION_CLASSIFIER_THRESHOLD` | 0.6 | Minimum confidence to store memory |
| `MAX_MEMORIES_TO_RETRIEVE` | 10 | Top K memories to inject |
| `MEMORY_TOKEN_BUDGET` | 500 | Max tokens for retrieved memories |
| `CORE_MEMORY_TOKEN_BUDGET` | 500 | Max tokens for core memory |

### Phase 2 Parameters

| Parameter | Default | Description |
|-----------|---------|-------------|
| `SEMANTIC_SEARCH_ENABLED` | True | Enable/disable semantic search |
| `SEMANTIC_SEARCH_LIMIT` | 20 | Number of candidates from vector search |
| `MIN_SEMANTIC_SCORE` | 0.3 | Minimum similarity score threshold |
| `QDRANT_HOST` | localhost | Qdrant server host |
| `QDRANT_PORT` | 6333 | Qdrant server port |
| `EMBEDDING_MODEL` | all-MiniLM-L6-v2 | Sentence-transformers model |
| `RANKING_WEIGHTS.semantic` | 0.5 | Weight for semantic similarity |
| `RANKING_WEIGHTS.type` | 0.25 | Weight for type priority |
| `RANKING_WEIGHTS.recency` | 0.25 | Weight for recency score |

### Phase 3 Parameters (NEW)

| Parameter | Default | Description |
|-----------|---------|-------------|
| `STAGE_3_ENABLED` | False | Enable/disable LLM-based extraction |
| `LLM_PROVIDER` | groq | LLM provider: "openai", "anthropic", "groq" |
| `LLM_EXTRACTION_MODEL` | llama-3.3-70b-versatile | Model for Stage 3 extraction |
| `STAGE_3_CONFIDENCE_THRESHOLD` | 0.7 | Escalate to LLM if Stage 2 < this |
| `SEMANTIC_DEDUP_ENABLED` | True | Enable semantic deduplication |
| `SEMANTIC_DEDUP_THRESHOLD` | 0.92 | Similarity score to consider duplicate |
| `MIN_CONFIDENCE_TO_STORE` | 0.6 | Discard memories below this confidence |
| `CONFIDENCE_BOOST_PER_MENTION` | 0.1 | Boost confidence when repeated |
| `MAX_CONFIDENCE` | 0.95 | Maximum confidence after boosts |

### Phase 4 Parameters (NEW)

| Parameter | Default | Description |
|-----------|---------|-------------|
| `CONSOLIDATION_ENABLED` | True | Enable/disable background consolidation |
| `CONSOLIDATION_INTERVAL_TURNS` | 50 | Turns between consolidation runs |
| `MEMORY_DECAY_ENABLED` | True | Enable memory decay for old memories |
| `MEMORY_MERGE_ENABLED` | True | Enable merging of similar memories |
| `PROMOTION_ENABLED` | True | Enable promotion to Core Memory |
| `DECAY_TURNS_THRESHOLD` | 100 | Turns before decay starts |
| `DECAY_FACTOR` | 0.95 | Confidence multiplier per decay cycle |
| `MERGE_SIMILARITY_THRESHOLD` | 0.88 | Similarity to consider for merging |
| `PROMOTION_CONFIDENCE_THRESHOLD` | 0.85 | Min confidence for promotion |
| `PROMOTION_MENTION_THRESHOLD` | 3 | Min mentions for promotion |
| `PROMOTION_ACCESS_THRESHOLD` | 5 | Min accesses for promotion |
| `RANKING_WEIGHTS_5_SIGNAL.semantic` | 0.35 | Weight for semantic similarity |
| `RANKING_WEIGHTS_5_SIGNAL.type` | 0.20 | Weight for type priority |
| `RANKING_WEIGHTS_5_SIGNAL.recency` | 0.20 | Weight for recency score |
| `RANKING_WEIGHTS_5_SIGNAL.frequency` | 0.15 | Weight for access frequency |
| `RANKING_WEIGHTS_5_SIGNAL.confidence` | 0.10 | Weight for confidence score |

## What's Implemented

### Phase 1
- ✅ Flat file storage with human-editable Markdown
- ✅ Redis storage with AOF persistence
- ✅ Two-stage extraction (heuristic + pattern classifier)
- ✅ Type-based and recency-based retrieval
- ✅ Deduplication
- ✅ Memory indices (type, recency)
- ✅ Full pipeline orchestration
- ✅ Statistics and monitoring

### Phase 2
- ✅ Vector store (Qdrant) for semantic embeddings
- ✅ Embedding generation with sentence-transformers (all-MiniLM-L6-v2)
- ✅ Semantic similarity search
- ✅ Multi-signal ranking (semantic + type + recency)
- ✅ Configurable ranking weights
- ✅ Graceful fallback to Phase 1 if Qdrant unavailable

### Phase 3
- ✅ Stage 3 LLM-based extraction (OpenAI, Anthropic, Groq)
- ✅ Escalation logic (low confidence → LLM)
- ✅ Semantic deduplication using vector similarity
- ✅ Memory superseding and update detection
- ✅ Confidence modifiers (certainty words)
- ✅ Confidence boosting for repeated mentions
- ✅ Superseded memory filtering in retrieval

### Phase 4
- ✅ Background consolidation worker
- ✅ Memory decay for old/unused memories
- ✅ Memory merging for semantically similar content
- ✅ Promotion to Core Memory files
- ✅ 5-signal ranking (semantic + type + recency + frequency + confidence)
- ✅ Access tracking and frequency scoring
- ✅ Configurable consolidation intervals

## What's Coming Next

### Phase 5 (Weeks 9-10)
- Evaluation framework
- Synthetic test generator
- Regression test suites

### Comprehensive Test

The `test_all_phases.py` runs a full system test:

```bash
python test_all_phases.py
```

It validates:
- All 4 phases working together (120+ turns)
- Automatic consolidation triggering (3 cycles at turns 50, 100, 150)
- 60+ memory extractions from realistic dialogue
- 5-signal ranking effectiveness
- Memory decay, merging, and promotion to core memory
- Multi-API key rotation (prevents rate limit issues)
- Performance metrics across extended conversations

### Customer Service Test

The `test_customer_conversation.py` runs a realistic scenario:

```bash
python test_customer_conversation.py
```

It validates:
- 60-turn customer service conversation
- Extraction of entities, facts, preferences, and constraints
- Active memory tracking (which memories influenced each response)
- Memory persistence and access count tracking
- JSON output format for integration

### Active Memory Demos

These demonstrate the active memory tracking feature:

```bash
# 10-turn comprehensive demo
python demo_active_memories.py

# 5-turn simple example
python example_active_memories.py
```

They show:
- Which memories influenced each response
- Memory metadata: origin_turn, last_used_turn, access_count, confidence
- Memory evolution across conversation turns
- JSON output format for debugging and auditing

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

### Qdrant Connection Error (Phase 2)

```
Failed to connect to Qdrant
```

**Solution**: Make sure Qdrant is running:
```bash
docker-compose up -d
docker-compose ps  # Should show qdrant as "Up"
```

If Qdrant is not available, the system will automatically fall back to Phase 1 mode (non-semantic retrieval).

### Slow First Query (Phase 2)

The first query after startup may take a few seconds as the embedding model (all-MiniLM-L6-v2) is loaded. Subsequent queries will be much faster.

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
4. (Phase 2) Check `MIN_SEMANTIC_SCORE` threshold

## Architecture Notes

This implementation follows the spec in `LONG_FORM_MEMORY_SYSTEM_Version2.md`:

- **Context ≠ Memory**: Context is ephemeral (current window), Memory is persistent
- **Five-stage memory pipeline**: Sensory → Encoding → Storage → Retrieval → Forgetting
- **Human-like memory model**: Inspired by cognitive science research
- **Forgetting is essential**: Phase 4 will add decay and consolidation

## Performance

### Verified Performance Metrics (All 3 Phases)

| Operation | Target | Actual (Measured) |
|-----------|--------|-------------------|
| **Retrieval** | <50ms | 24-52ms ✅ |
| **Storage** | <10ms | 130-233ms (with vector indexing) |
| **LLM Extraction (Groq)** | 50-200ms | 1.1-3.2s |
| **Embedding Model Load** | - | ~16s (one-time cold start) |
| **Semantic Search** | - | 24-35ms ✅ |

### Phase-Specific Performance

**Phase 1 (Basic):**
- Extraction: ~1-2ms per turn (heuristic + pattern matching)
- Storage: <10ms per operation

**Phase 2 (Semantic Search):**
- First query: ~16-26s (embedding model cold start)
- Subsequent queries: 24-52ms
- Vector indexing adds ~20-50ms to storage

**Phase 3 (LLM Extraction):**
- Groq API latency: 1.1-3.2s per extraction
- Includes retry logic for JSON parsing errors
- Semantic deduplication: <50ms

## License

This is a reference implementation based on the memory system specification.

## Contributing

All 4 phases are now implemented and verified working. Contributions welcome for:
- Bug fixes
- Performance improvements
- Documentation
- Test cases
- Phase 5-6 implementation

See "What's Coming Next" section for planned features.
