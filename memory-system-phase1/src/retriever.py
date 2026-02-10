"""
Memory Retrieval - Phase 1 & Phase 2
Type-based + recency-based retrieval with semantic search (Phase 2)
"""

import logging
import math
from typing import List, Dict, Optional

from .config import (
    MAX_MEMORIES_TO_RETRIEVE,
    MEMORY_TOKEN_BUDGET,
    MEMORY_TYPES,
    SEMANTIC_SEARCH_ENABLED,
    SEMANTIC_SEARCH_LIMIT,
    MIN_SEMANTIC_SCORE,
    RANKING_WEIGHTS,
    TYPE_PRIORITIES,
    RECENCY_DECAY_RATE,
    RECENCY_MAX_TURNS,
)
from .redis_store import RedisStore

logger = logging.getLogger(__name__)


class MemoryRetriever:
    """
    Retrieves relevant memories for prompt injection.
    
    Phase 1: Type priority + recency-based retrieval
    Phase 2: Adds semantic search + multi-signal ranking
    """

    def __init__(self, redis_store: RedisStore, vector_store=None):
        """
        Initialize the retriever.
        
        Args:
            redis_store: Redis store instance
            vector_store: Optional vector store for semantic search (Phase 2)
        """
        self.redis_store = redis_store
        self.vector_store = vector_store
        self._semantic_enabled = SEMANTIC_SEARCH_ENABLED and vector_store is not None
        
        if self._semantic_enabled:
            logger.info("Semantic search enabled for memory retrieval")
        else:
            logger.info("Using non-semantic retrieval (Phase 1 mode)")

    def retrieve(
        self, 
        current_message: str, 
        turn_number: int,
        priority_types: Optional[List[str]] = None,
    ) -> List[Dict]:
        """
        Retrieve relevant memories for the current turn.
        
        Phase 1: Simple retrieval using type priority + recency
        Phase 2: Semantic similarity search + multi-signal ranking
        
        Args:
            current_message: The current user message
            turn_number: Current turn number
            priority_types: Memory types to prioritize (e.g., ["constraint", "preference"])
        
        Returns:
            List of memory dictionaries, ranked by relevance
        """
        if self._semantic_enabled:
            return self._retrieve_with_semantic_search(
                current_message, turn_number, priority_types
            )
        else:
            return self._retrieve_phase1(
                current_message, turn_number, priority_types
            )
    
    def _retrieve_with_semantic_search(
        self,
        current_message: str,
        turn_number: int,
        priority_types: Optional[List[str]] = None,
    ) -> List[Dict]:
        """
        Phase 2: Retrieve using semantic search + multi-signal ranking.
        
        Ranking formula:
            final_score = w_semantic * semantic_score 
                        + w_type * type_priority 
                        + w_recency * recency_score
        """
        all_memories = {}  # memory_id -> memory with scores
        
        # Step 1: Get candidates from semantic search
        semantic_results = self.vector_store.search_similar(
            query=current_message,
            limit=SEMANTIC_SEARCH_LIMIT,
            min_score=MIN_SEMANTIC_SCORE,
        )
        
        for result in semantic_results:
            memory = result['memory']
            memory_id = result['memory_id']
            
            # Get full memory from Redis (has more fields)
            full_memory = self.redis_store.get_memory(memory_id)
            if full_memory:
                full_memory['semantic_score'] = result['score']
                all_memories[memory_id] = full_memory
            else:
                # Fall back to vector store payload
                memory['semantic_score'] = result['score']
                all_memories[memory_id] = memory
        
        logger.debug(f"Semantic search found {len(all_memories)} candidates")
        
        # Step 2: Always include constraint and instruction types
        always_on_types = ["constraint", "instruction"]
        for mem_type in always_on_types:
            memories = self.redis_store.get_memories_by_type(mem_type, limit=20)
            for mem in memories:
                mem_id = mem['memory_id']
                if mem_id not in all_memories:
                    mem['semantic_score'] = 0.5  # Default score for always-on
                    all_memories[mem_id] = mem
                # Boost semantic score for always-on types already found
                elif mem_id in all_memories:
                    all_memories[mem_id]['semantic_score'] = max(
                        all_memories[mem_id].get('semantic_score', 0), 
                        0.5
                    )
        
        # Step 3: Add priority types if specified
        if priority_types:
            for mem_type in priority_types:
                if mem_type not in always_on_types:
                    memories = self.redis_store.get_memories_by_type(mem_type, limit=10)
                    for mem in memories:
                        mem_id = mem['memory_id']
                        if mem_id not in all_memories:
                            mem['semantic_score'] = 0.3  # Lower default for priority types
                            all_memories[mem_id] = mem
        
        # Step 4: Calculate multi-signal ranking scores
        ranked_memories = []
        
        for memory_id, memory in all_memories.items():
            # Semantic score (0-1)
            semantic_score = memory.get('semantic_score', 0)
            
            # Type priority score (0-1)
            mem_type = memory.get('type', 'fact')
            type_score = TYPE_PRIORITIES.get(mem_type, 0.5)
            
            # Recency score (0-1, exponential decay)
            mem_turn = int(memory.get('turn_number', 0))
            turns_ago = max(0, turn_number - mem_turn)
            recency_score = math.exp(-RECENCY_DECAY_RATE * turns_ago)
            
            # Combined score using weighted sum
            final_score = (
                RANKING_WEIGHTS['semantic'] * semantic_score +
                RANKING_WEIGHTS['type'] * type_score +
                RANKING_WEIGHTS['recency'] * recency_score
            )
            
            memory['retrieval_score'] = final_score
            memory['semantic_score'] = semantic_score
            memory['type_score'] = type_score
            memory['recency_score'] = recency_score
            
            ranked_memories.append(memory)
        
        # Sort by final score
        ranked_memories.sort(key=lambda m: m['retrieval_score'], reverse=True)
        
        # Take top K
        top_memories = ranked_memories[:MAX_MEMORIES_TO_RETRIEVE]
        
        # Budget check
        estimated_tokens = len(top_memories) * 50
        if estimated_tokens > MEMORY_TOKEN_BUDGET:
            max_count = MEMORY_TOKEN_BUDGET // 50
            top_memories = top_memories[:max_count]
            logger.warning(f"Trimmed memories to {max_count} to fit token budget")
        
        logger.info(
            f"Retrieved {len(top_memories)} memories (semantic search) for turn {turn_number} "
            f"(from {len(all_memories)} candidates)"
        )
        
        return top_memories
    
    def _retrieve_phase1(
        self,
        current_message: str,
        turn_number: int,
        priority_types: Optional[List[str]] = None,
    ) -> List[Dict]:
        """
        Phase 1: Simple retrieval using type priority + recency (fallback).
        """
        all_memories = []
        
        # Strategy 1: Always retrieve CONSTRAINT and INSTRUCTION types
        # These are critical and should always be considered
        always_on_types = ["constraint", "instruction"]
        
        for mem_type in always_on_types:
            memories = self.redis_store.get_memories_by_type(mem_type, limit=20)
            for mem in memories:
                mem['retrieval_score'] = 1.0  # Max priority for always-on
            all_memories.extend(memories)
        
        # Strategy 2: Get recent memories (recency-based)
        recent_memories = self.redis_store.get_recent_memories(limit=30)
        
        # Score recent memories by recency
        for i, mem in enumerate(recent_memories):
            # Recency score: exponential decay
            # Most recent = 1.0, decays as we go back
            recency_score = 0.9 ** i
            
            # If already in always_on, don't add again
            if mem['type'] not in always_on_types:
                mem['retrieval_score'] = recency_score * 0.5  # Lower than always-on
                all_memories.append(mem)
        
        # Strategy 3: Priority types (if specified)
        if priority_types:
            for mem_type in priority_types:
                if mem_type not in always_on_types:
                    memories = self.redis_store.get_memories_by_type(mem_type, limit=10)
                    for mem in memories:
                        # Check if already retrieved
                        if not any(m['memory_id'] == mem['memory_id'] for m in all_memories):
                            mem['retrieval_score'] = 0.7  # Medium priority
                            all_memories.append(mem)
        
        # Deduplicate by memory_id (keep highest score)
        seen = {}
        for mem in all_memories:
            mem_id = mem['memory_id']
            if mem_id not in seen or mem['retrieval_score'] > seen[mem_id]['retrieval_score']:
                seen[mem_id] = mem
        
        all_memories = list(seen.values())
        
        # Rank by retrieval_score
        all_memories.sort(key=lambda m: m['retrieval_score'], reverse=True)
        
        # Take top K
        top_memories = all_memories[:MAX_MEMORIES_TO_RETRIEVE]
        
        # Budget check (estimate ~50 tokens per memory on average)
        # This is a rough estimate; Phase 2+ will have more precise token counting
        estimated_tokens = len(top_memories) * 50
        
        if estimated_tokens > MEMORY_TOKEN_BUDGET:
            # Trim to fit budget
            max_count = MEMORY_TOKEN_BUDGET // 50
            top_memories = top_memories[:max_count]
            logger.warning(f"Trimmed memories to {max_count} to fit token budget")
        
        logger.info(
            f"Retrieved {len(top_memories)} memories for turn {turn_number} "
            f"(from {len(all_memories)} candidates)"
        )
        
        return top_memories

    def format_memories_for_prompt(self, memories: List[Dict]) -> str:
        """
        Format retrieved memories for injection into the prompt.
        
        Args:
            memories: List of memory dictionaries
        
        Returns:
            Formatted string ready for prompt injection
        """
        if not memories:
            return ""
        
        sections = {
            "constraint": [],
            "instruction": [],
            "preference": [],
            "entity": [],
            "commitment": [],
            "fact": [],
            "event": [],
        }
        
        # Group by type
        for mem in memories:
            mem_type = mem.get('type', 'fact')
            if mem_type in sections:
                sections[mem_type].append(mem)
        
        # Format each section
        formatted_sections = []
        
        for mem_type, mem_list in sections.items():
            if not mem_list:
                continue
            
            section_title = mem_type.upper()
            section_lines = [f"=== {section_title} ==="]
            
            for mem in mem_list:
                key = mem.get('key', 'unknown')
                value = mem.get('value', '')
                confidence = mem.get('confidence', 0)
                turn = mem.get('turn_number', 0)
                
                # Format: key: value [turn X, confidence Y%]
                line = f"- {key}: {value} [turn {turn}, {confidence*100:.0f}% confident]"
                section_lines.append(line)
            
            formatted_sections.append("\n".join(section_lines))
        
        return "\n\n".join(formatted_sections)

    def retrieve_for_prompt(
        self, 
        current_message: str, 
        turn_number: int,
        priority_types: Optional[List[str]] = None,
    ) -> str:
        """
        One-shot method: retrieve and format memories for prompt.
        
        Returns:
            Formatted memory string ready for injection
        """
        memories = self.retrieve(current_message, turn_number, priority_types)
        return self.format_memories_for_prompt(memories)
