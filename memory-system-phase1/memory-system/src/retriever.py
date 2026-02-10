"""
Memory Retrieval - Phase 1
Type-based + recency-based retrieval (no semantic search yet)
"""

import logging
from typing import List, Dict, Optional

from .config import (
    MAX_MEMORIES_TO_RETRIEVE,
    MEMORY_TOKEN_BUDGET,
    MEMORY_TYPES,
)
from .redis_store import RedisStore

logger = logging.getLogger(__name__)


class MemoryRetriever:
    """Retrieves relevant memories for prompt injection"""

    def __init__(self, redis_store: RedisStore):
        self.redis_store = redis_store

    def retrieve(
        self, 
        current_message: str, 
        turn_number: int,
        priority_types: Optional[List[str]] = None,
    ) -> List[Dict]:
        """
        Retrieve relevant memories for the current turn.
        
        Phase 1: Simple retrieval using type priority + recency
        Phase 2: Will add semantic similarity search
        
        Args:
            current_message: The current user message
            turn_number: Current turn number
            priority_types: Memory types to prioritize (e.g., ["constraint", "preference"])
        
        Returns:
            List of memory dictionaries, ranked by relevance
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
