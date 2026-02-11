# Long-Form Memory System - Phase 1, 2 & 3

A production-grade memory system for AI agents that enables accurate recall across 1,000+ conversation turns.

## What This Is

This is **Phase 1, 2 & 3** of a 6-phase implementation plan for a complete long-form memory system.

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

### Phase 3 Features (NEW):
- ✅ Stage 3 LLM-based extraction for complex cases
- ✅ Multi-provider support (OpenAI, Anthropic, Groq)
- ✅ Semantic deduplication using vector similarity
- ✅ Memory updates and superseding
- ✅ Confidence scoring with certainty modifiers
- ✅ Confidence boosting for repeated mentions

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
# Phase 1 demo (basic retrieval)
python demo.py

# Phase 2 demo (semantic search)
python demo_phase2.py

# Phase 3 demo (LLM extraction, deduplication, updates)
# First, set your LLM API key:
# For Groq (fastest): set GROQ_API_KEY=your_key_here
# For OpenAI: set OPENAI_API_KEY=your_key_here
# For Anthropic: set ANTHROPIC_API_KEY=your_key_here

python demo_phase3.py
```

The Phase 2 demo will:
1. Simulate a conversation with rich information
2. Extract and store memories with embeddings
3. Test semantic similarity search
4. Demonstrate multi-signal ranking

The Phase 3 demo will:
1. Test LLM-based extraction for complex messages
2. Demonstrate semantic deduplication (similarity > 0.92)
3. Show memory updates and superseding
4. Test confidence boosting for repeated information
5. Verify superseded memories are filtered from retrieval

## Project Structure

```
memory-system/
├── docker-compose.yml          # Redis + Qdrant setup
├── redis.conf                  # Redis configuration (AOF persistence)
├── requirements.txt            # Python dependencies
├── demo.py                     # Phase 1 demo script
├── demo_phase2.py              # Phase 2 demo script
├── demo_phase3.py              # Phase 3 demo script (NEW)
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
    ├── redis_store.py         # Redis storage layer (Phase 3: + superseding)
    ├── extractor.py           # Memory extraction (Stage 1, 2 & 3)
    ├── llm_extractor.py       # Phase 3: LLM-based extraction (NEW)
    ├── retriever.py           # Memory retrieval (with semantic search)
    ├── memory_system.py       # Main orchestrator
    ├── embedding_service.py   # Phase 2: Embedding generation
    └── vector_store.py        # Phase 2: Qdrant vector store
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

**Stage 3: LLM Extraction** _(Phase 3 - NEW)_
- Uses OpenAI, Anthropic, or Groq for complex extraction
- Escalates when Stage 2 confidence < 0.7 or no results
- Structured JSON extraction with confidence scores
- Detects memory updates and contradictions
- Target latency: ~50-200ms (Groq), ~200-500ms (standard APIs)

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

**Phase 3: Semantic Deduplication** _(NEW)_
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
| `LLM_EXTRACTION_MODEL` | llama3-8b-8192 | Model for Stage 3 extraction |
| `STAGE_3_CONFIDENCE_THRESHOLD` | 0.7 | Escalate to LLM if Stage 2 < this |
| `SEMANTIC_DEDUP_ENABLED` | True | Enable semantic deduplication |
| `SEMANTIC_DEDUP_THRESHOLD` | 0.92 | Similarity score to consider duplicate |
| `MIN_CONFIDENCE_TO_STORE` | 0.6 | Discard memories below this confidence |
| `CONFIDENCE_BOOST_PER_MENTION` | 0.1 | Boost confidence when repeated |
| `MAX_CONFIDENCE` | 0.95 | Maximum confidence after boosts |

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

### Phase 3 (NEW)
- ✅ Stage 3 LLM-based extraction (OpenAI, Anthropic, Groq)
- ✅ Escalation logic (low confidence → LLM)
- ✅ Semantic deduplication using vector similarity
- ✅ Memory superseding and update detection
- ✅ Confidence modifiers (certainty words)
- ✅ Confidence boosting for repeated mentions
- ✅ Superseded memory filtering in retrieval

## What's Coming Next

### Phase 4 (Weeks 7-8)
- Background consolidation worker
- Memory merging and decay
- Promotion to Core Memory
- 5-signal ranking (add frequency + confidence signals)

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
