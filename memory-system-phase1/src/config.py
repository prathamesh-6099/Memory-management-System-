"""
Configuration for the Memory System - Phase 1, 2 & 3
All tunable parameters from Section 12 of the spec
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env file in the project root
env_path = Path(__file__).parent.parent / ".env"
load_dotenv(dotenv_path=env_path)

# Paths
PROJECT_ROOT = Path(__file__).parent.parent
MEMORY_DIR = PROJECT_ROOT / "memory"

# Redis Configuration
REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
REDIS_PORT = int(os.getenv("REDIS_PORT", "6379"))
REDIS_DB = int(os.getenv("REDIS_DB", "0"))

# Qdrant Configuration (Phase 2)
QDRANT_HOST = os.getenv("QDRANT_HOST", "localhost")
QDRANT_PORT = int(os.getenv("QDRANT_PORT", "6333"))
QDRANT_COLLECTION_NAME = os.getenv("QDRANT_COLLECTION", "memory_vectors")

# Embedding Configuration (Phase 2)
EMBEDDING_MODEL = "all-MiniLM-L6-v2"  # Fast and good quality
EMBEDDING_DIMENSION = 384  # Dimension for all-MiniLM-L6-v2

# Memory Layer Configuration
CORE_MEMORY_FILES = ["CORE.md", "PREFERENCES.md", "INSTRUCTIONS.md", "CONSTRAINTS.md"]
CORE_MEMORY_TOKEN_BUDGET = 500  # Always injected

# Extraction Configuration (Phase 1: Stage 1 & 2 only)
SENSORY_FILTER_THRESHOLD = 0.3  # Heuristic score threshold
EXTRACTION_CLASSIFIER_THRESHOLD = 0.6  # Classifier confidence threshold

# Heuristic weights for sensory filter
HEURISTIC_WEIGHTS = {
    "length": 0.3,  # Longer messages more likely to contain info
    "keywords": 0.4,  # Presence of important keywords
    "question": 0.15,  # Questions often contain context
    "specificity": 0.15,  # Specific details vs vague statements
}

# Keywords that signal extractable information
EXTRACTION_KEYWORDS = {
    "preference": ["prefer", "like", "hate", "love", "favorite", "always", "never"],
    "constraint": ["must", "cannot", "don't", "won't", "shouldn't", "allergic", "avoid"],
    "entity": ["my", "named", "called", "manager", "friend", "colleague", "family"],
    "instruction": ["always", "whenever", "remember to", "make sure", "don't forget"],
    "commitment": ["will", "promise", "committed", "deadline", "by", "before"],
    "fact": ["live in", "work at", "am", "is", "from", "born", "studied"],
}

# Memory Types (for Redis indexing)
MEMORY_TYPES = ["preference", "constraint", "entity", "instruction", "commitment", "fact", "event"]

# Retrieval Configuration
MAX_MEMORIES_TO_RETRIEVE = 10  # Top K memories to inject
MEMORY_TOKEN_BUDGET = 500  # Total token budget for retrieved memories

# Phase 2: Semantic Search Configuration
SEMANTIC_SEARCH_ENABLED = True  # Enable vector-based semantic search
SEMANTIC_SEARCH_LIMIT = 20  # Number of candidates from vector search
MIN_SEMANTIC_SCORE = 0.3  # Minimum similarity score to consider

# Phase 2: Multi-Signal Ranking Weights
# These weights sum to 1.0 for final score calculation
RANKING_WEIGHTS = {
    "semantic": 0.5,   # Semantic similarity score weight
    "type": 0.25,      # Memory type priority weight
    "recency": 0.25,   # Recency score weight
}

# Memory type priorities for ranking (higher = more important)
TYPE_PRIORITIES = {
    "constraint": 1.0,    # Constraints are critical
    "instruction": 0.95,  # Instructions are very important
    "preference": 0.7,    # Preferences are valuable
    "entity": 0.6,        # Entities for context
    "commitment": 0.8,    # Commitments are time-sensitive
    "fact": 0.5,          # Facts are general info
    "event": 0.4,         # Events are context
}

# Recency decay configuration
RECENCY_DECAY_RATE = 0.1  # Decay factor per turn (exponential decay)
RECENCY_MAX_TURNS = 100   # After this many turns, recency score approaches 0

# Redis Key Prefixes
REDIS_MEMORY_PREFIX = "mem:"
REDIS_DEDUP_PREFIX = "dedup:"
REDIS_TYPE_INDEX_PREFIX = "type:"
REDIS_RECENCY_INDEX = "recent_memories"

# Memory Record Fields
MEMORY_FIELDS = [
    "memory_id",
    "type",
    "key",
    "value",
    "confidence",
    "turn_number",
    "timestamp",
    "source_text",
    "mention_count",     # Phase 3: Track repetitions for confidence boost
    "superseded_by",     # Phase 3: ID of memory that supersedes this one
    "supersedes",        # Phase 3: ID of memory this one supersedes
    "is_update",         # Phase 3: Flag if this is an update to existing memory
    "last_accessed_turn",  # Phase 3: For frequency tracking
]

# Phase 3: Stage 3 LLM Extraction Configuration
STAGE_3_ENABLED = True  # Enable/disable LLM-based extraction
LLM_PROVIDER = "groq"  # "openai" | "anthropic" | "groq"
LLM_EXTRACTION_MODEL = os.getenv("LLM_EXTRACTION_MODEL", "llama-3.3-70b-versatile")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
STAGE_3_CONFIDENCE_THRESHOLD = 0.7  # Escalate to LLM if Stage 2 < this
STAGE_3_MAX_TOKENS = 200  # Max tokens for LLM extraction response
STAGE_3_TEMPERATURE = 0.1  # Low temperature for consistent extraction

# Phase 3: Semantic Deduplication Configuration
SEMANTIC_DEDUP_ENABLED = True  # Enable/disable semantic deduplication
SEMANTIC_DEDUP_THRESHOLD = 0.92  # Similarity score to consider duplicate
SEMANTIC_DEDUP_CHECK_LIMIT = 5  # Check top N similar memories for duplicates

# Phase 3: Confidence Scoring Configuration
MIN_CONFIDENCE_TO_STORE = 0.6  # Discard memories below this confidence
HIGH_CONFIDENCE_THRESHOLD = 0.9  # Candidate for core memory promotion
CONFIDENCE_BOOST_PER_MENTION = 0.1  # Boost confidence when repeated
MAX_CONFIDENCE = 0.95  # Maximum confidence after boosts
LOW_CONFIDENCE_DECAY_RATE = 0.1  # Reduce confidence of unused memories
LOW_CONFIDENCE_DECAY_TURNS = 200  # After this many turns, apply decay

# Phase 3: Update Detection Patterns
UPDATE_PATTERNS = [
    r"actually[,\s]+(.+)",
    r"i changed my mind[,\s]+(.+)",
    r"not anymore[,\s]+(.+)",
    r"i used to .+ but now (.+)",
    r"correction[,:\s]+(.+)",
    r"i meant[,:\s]+(.+)",
    r"let me correct that[,:\s]+(.+)",
]

# Phase 3: Confidence Modifiers
CONFIDENCE_MODIFIERS = {
    # Certainty boosters
    "always": 0.1,
    "never": 0.1,
    "definitely": 0.1,
    "absolutely": 0.1,
    "must": 0.1,
    
    # Certainty reducers
    "maybe": -0.2,
    "perhaps": -0.2,
    "possibly": -0.2,
    "might": -0.2,
    "sometimes": -0.15,
    "occasionally": -0.15,
    "could": -0.15,
}

# Logging
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
