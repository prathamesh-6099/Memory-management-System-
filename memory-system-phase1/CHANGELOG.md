# Changelog - Memory System

All notable changes to the Long-Form Memory System are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).

---

## [2.0.0] - 2026-02-13

### 🎯 Major Achievements
- **100% long-term recall** at all distances (10-1000 turns)
- **80.1% context recall** (up from 68.3%)
- **87% reduction in LLM calls** through optimized extraction
- **Production validation** with 1000-turn latency testing

### ✨ Added

#### Hybrid Retrieval System
- Dual-branch architecture combining semantic search and recency filtering
- Semantic branch: Filtered by MIN_SEMANTIC_SCORE (0.3)
- Recency branch: Unfiltered recent memories (last 100 turns)
- Merge and deduplication logic
- **Result:** 100% long-term recall at 1000 turns (up from 0%)

#### Payment Domain Support
- Extended extraction with payment/financial domain patterns
- Added 11 payment-specific keywords to Phase 1
- Added 13 payment-specific regex patterns to Phase 2:
  - Account numbers (confidence: 0.95)
  - Payment amounts (confidence: 0.90)
  - Due dates (confidence: 0.90)
  - Payment status (confidence: 0.85)
  - Payment arrangements (confidence: 0.85)
  - Customer names (confidence: 0.85)
  - Overdue status (confidence: 0.80-0.85)
  - Payment confirmations (confidence: 0.90)
- **Result:** Phase 1 pass rate 40% → 73.3%, Phase 2 extraction 0% → 46.7%

#### Multi-Key API Rotation
- Support for 4 simultaneous Groq API keys
- Automatic rotation on 429 rate limit errors
- Environment variables: GROQ_API_KEY, GROQ_API_KEY_1, GROQ_API_KEY_2, GROQ_API_KEY_3
- Total capacity: 400k tokens/day, 48k tokens/minute
- **Result:** Enables high-volume testing and production workloads

#### Test Infrastructure
- **test_1000_turn_latency.py**: Comprehensive 1000-turn latency validation
  - Payment reminder conversation patterns
  - Per-turn latency measurement (processing + retrieval)
  - Statistics: mean, median, P95, P99, throughput
  - Results saved to latency_results_1000_turns.txt
- **diagnostic_extraction_phases.py**: Extraction pipeline diagnostics
  - Independent phase testing (Phase 1, 2, 3)
  - 15 payment domain test messages
  - Phase-by-phase pass rates and extraction counts

#### Documentation
- **RESULTS_FEBRUARY_2026.md**: Comprehensive optimization results
  - Before/after comparisons for all metrics
  - Architecture diagrams and code examples
  - Production readiness assessment
  - Detailed performance analysis

### 🔧 Changed

#### 5-Signal Ranking Optimization
- Rebalanced weights for improved context recall:
  - Semantic: 0.35 → **0.30** (down 5%)
  - Type: 0.20 → **0.40** (up 20%)
  - Recency: 0.20 → **0.10** (down 10%)
  - Frequency: 0.15 → **0.05** (down 10%)
  - Confidence: 0.10 → **0.15** (up 5%)
- Adjusted recency decay rate: 0.1 → **0.001** (gentler decay)
- Extended max decay turns: 1000 → **5000**
- **Result:** Context recall 68.3% → 80.1%

#### Stage 3 LLM Configuration
- Increased STAGE_3_MAX_TOKENS: 200 → **500** (prevents JSON cutoff)
- Maintained STAGE_3_TEMPERATURE: **0.1** (consistent extraction)
- Maintained STAGE_3_CONFIDENCE_THRESHOLD: **0.7** (escalate only when needed)

#### Redis Operations
- Optimized `clear_all_memories()` to check count before clearing
- Skip clearing if empty (performance optimization)
- Display count before clearing (visibility)

### 📊 Performance Improvements

#### Extraction Pipeline
| Metric | Before | After | Improvement |
|--------|--------|-------|-------------|
| Phase 1 Pass Rate | 40% | 73.3% | +83% |
| Phase 2 Extraction | 0% | 46.7% | +∞ |
| Phase 3 LLM Calls | ~100% | 13.3% | -87% |

#### Retrieval Quality
| Metric | Before | After | Improvement |
|--------|--------|-------|-------------|
| Long-term Recall (1000) | 0% | 100% | +100% |
| Long-term Recall (500) | 12% | 100% | +733% |
| Context Recall | 68.3% | 80.1% | +17% |

#### Latency & Throughput (1000-turn test)
- Processing latency: **575ms mean**, 350ms median, 1333ms P95
- Retrieval latency: **294ms mean**, 296ms median, 379ms P95
- Throughput: **1.74 turns/second**
- Total time: **9.58 minutes** for 1000 turns
- Memories stored: **40 total** (0.04 per turn)

#### API Efficiency
- LLM calls per turn: ~100% → **13.3%** (-87%)
- Tokens per turn: ~750 → ~100 (-87%)
- Estimated cost (1000 turns): ~$7.50 → ~$1.00 (-87%)

### 🐛 Fixed
- JSON parsing errors due to insufficient max tokens (200 → 500)
- Long-term recall failures at 500+ turns (0% → 100%)
- Rate limit crashes during high-volume testing (single key → 4-key rotation)
- Domain mismatch between system design (personal assistant) and test data (payment reminders)

### 📝 Documentation Updates
- Updated [README.md](README.md) with recent improvements section
- Added hybrid retrieval documentation
- Added payment domain pattern documentation
- Updated performance metrics with 1000-turn results
- Added multi-key API rotation configuration
- Updated project structure with new files
- Added quick reference tables and status indicators

---

## [1.5.0] - 2025-12-XX (Phase 5 Complete)

### Added
- RAGAS-based evaluation framework
- Synthetic conversation generator (200 test samples)
- Extraction accuracy metrics (Precision, Recall, F1)
- Retrieval quality metrics (Context Precision/Recall, MRR)
- Distance sweep tests (10-1000 turn recall)
- Consolidation quality evaluation
- Automated test runner with comprehensive reporting

### Results
- Extraction F1: **89.5%**
- Context Recall: **68.3%** (before optimization)
- Long-term Recall: 0% at 1000 turns (before optimization)

---

## [1.4.0] - 2025-10-XX (Phase 4 Complete)

### Added
- Background consolidation worker
- Memory decay for old/unused memories
- Memory merging for semantically similar content
- Promotion to Core Memory files
- 5-signal ranking (semantic + type + recency + frequency + confidence)
- Access tracking and frequency scoring
- Configurable consolidation intervals

---

## [1.3.0] - 2025-08-XX (Phase 3 Complete)

### Added
- Stage 3 LLM-based extraction (OpenAI, Anthropic, Groq)
- Escalation logic (low confidence → LLM)
- Semantic deduplication using vector similarity
- Memory superseding and update detection
- Confidence scoring with certainty modifiers
- Confidence boosting for repeated mentions
- Superseded memory filtering in retrieval

---

## [1.2.0] - 2025-06-XX (Phase 2 Complete)

### Added
- Vector store (Qdrant) for semantic embeddings
- Embedding generation with sentence-transformers (all-MiniLM-L6-v2)
- Semantic similarity search
- Multi-signal ranking (semantic + type + recency)
- Configurable ranking weights
- Graceful fallback to Phase 1 if Qdrant unavailable

---

## [1.1.0] - 2025-04-XX (Phase 1 Complete)

### Added
- Flat file storage for Core Memory (Markdown files)
- Redis storage for Long-Term Memory (persistent)
- Two-stage extraction pipeline (heuristic + pattern-based)
- Basic retrieval (type-priority + recency-based)
- Automated deduplication (key-based)
- Memory indices (type, recency)
- Full pipeline orchestration
- Statistics and monitoring

### Initial Features
- Core Memory: name, language, timezone, preferences
- Long-Term Memory: preferences, constraints, entities, commitments
- Memory types: preference, constraint, entity, instruction, commitment, fact, event
- Pattern-based extraction with confidence scores
- Type-based and recency-based retrieval
- Docker Compose setup (Redis + Qdrant)

---

## [1.0.0] - 2025-02-XX (Initial Release)

### Added
- Project structure and architecture
- Initial specification document
- Docker Compose configuration
- Basic requirements and setup

---

## Legend

- 🎯 Major Achievement - Significant milestone or breakthrough
- ✨ Added - New features or capabilities
- 🔧 Changed - Changes to existing functionality
- 🐛 Fixed - Bug fixes
- 📊 Performance - Performance improvements
- 📝 Documentation - Documentation updates
- 🗑️ Removed - Removed features
- 🔒 Security - Security improvements

---

**Current Version:** 2.0.0  
**Last Updated:** February 13, 2026
