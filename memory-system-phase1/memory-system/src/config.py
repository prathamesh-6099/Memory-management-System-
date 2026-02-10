"""
Configuration for the Memory System - Phase 1
All tunable parameters from Section 12 of the spec
"""

import os
from pathlib import Path

# Paths
PROJECT_ROOT = Path(__file__).parent.parent
MEMORY_DIR = PROJECT_ROOT / "memory"

# Redis Configuration
REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
REDIS_PORT = int(os.getenv("REDIS_PORT", "6379"))
REDIS_DB = int(os.getenv("REDIS_DB", "0"))

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

# Retrieval Configuration (Phase 1: Basic retrieval, no semantic search yet)
MAX_MEMORIES_TO_RETRIEVE = 10  # Top K memories to inject
MEMORY_TOKEN_BUDGET = 500  # Total token budget for retrieved memories

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
]

# Logging
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
