"""
Main Memory System - Phase 1
Orchestrates the full pipeline: Extract → Store → Retrieve → Inject
"""

import logging
from typing import Dict, List, Optional, Tuple

from .flat_file_store import FlatFileStore
from .redis_store import RedisStore
from .extractor import MemoryExtractor
from .retriever import MemoryRetriever

logger = logging.getLogger(__name__)


class MemorySystem:
    """
    Complete memory system orchestrating all layers.
    
    Pipeline:
    1. EXTRACT - Identify what's worth remembering (per turn)
    2. STORE - Persist memories (flat files + Redis)
    3. RETRIEVE - Find relevant memories (per turn)
    4. INJECT - Compose into prompt
    5. RESPOND - Generate response (external LLM call)
    """

    def __init__(self, user_id: str):
        """
        Initialize memory system for a user.
        
        Args:
            user_id: Unique user identifier
        """
        self.user_id = user_id
        self.turn_number = 0
        
        # Initialize storage layers
        self.flat_file_store = FlatFileStore(user_id)
        self.redis_store = RedisStore()
        
        # Initialize processing modules
        self.extractor = MemoryExtractor()
        self.retriever = MemoryRetriever(self.redis_store)
        
        logger.info(f"Initialized memory system for user {user_id}")

    def process_turn(
        self, 
        user_message: str,
        priority_types: Optional[List[str]] = None,
    ) -> Tuple[str, Dict]:
        """
        Process a single conversation turn.
        
        This is the main entry point for the memory system.
        Call this for each user message before generating a response.
        
        Args:
            user_message: The user's message text
            priority_types: Optional list of memory types to prioritize
        
        Returns:
            (memory_context, stats) where:
            - memory_context: Formatted string to inject into prompt
            - stats: Dictionary with extraction/retrieval statistics
        """
        self.turn_number += 1
        logger.info(f"\n{'='*60}\nProcessing turn {self.turn_number}\n{'='*60}")
        
        stats = {
            'turn_number': self.turn_number,
            'extracted_count': 0,
            'stored_count': 0,
            'retrieved_count': 0,
            'total_memories': 0,
        }
        
        # STEP 1: EXTRACT - Identify memories from this message
        extracted_memories = self.extractor.extract(user_message, self.turn_number)
        stats['extracted_count'] = len(extracted_memories)
        
        # STEP 2: STORE - Persist extracted memories
        stored_count = 0
        for memory in extracted_memories:
            success = self.redis_store.store_memory(memory)
            if success:
                stored_count += 1
        
        stats['stored_count'] = stored_count
        stats['total_memories'] = self.redis_store.count_memories()
        
        # STEP 3 & 4: RETRIEVE + INJECT - Get relevant memories and format for prompt
        memory_context = self._compose_prompt_context(
            user_message, 
            priority_types
        )
        
        # Count retrieved memories (rough estimate from formatted text)
        stats['retrieved_count'] = memory_context.count('\n- ') if memory_context else 0
        
        logger.info(
            f"Turn {self.turn_number} complete: "
            f"extracted={stats['extracted_count']}, "
            f"stored={stats['stored_count']}, "
            f"retrieved={stats['retrieved_count']}, "
            f"total={stats['total_memories']}"
        )
        
        return memory_context, stats

    def _compose_prompt_context(
        self, 
        user_message: str, 
        priority_types: Optional[List[str]] = None,
    ) -> str:
        """
        Compose the full memory context for prompt injection.
        
        Structure:
        1. Core Memory (ALWAYS injected)
        2. Retrieved Long-Term Memories (selective)
        
        Args:
            user_message: Current user message
            priority_types: Memory types to prioritize
        
        Returns:
            Complete formatted memory context
        """
        sections = []
        
        # Layer 1: Core Memory (always injected)
        core_memory = self.flat_file_store.read_core_memory()
        if core_memory.strip():
            sections.append("### CORE MEMORY (Always Active)")
            sections.append(core_memory)
        
        # Layer 4: Long-Term Memory (selective retrieval)
        retrieved_memories = self.retriever.retrieve_for_prompt(
            user_message,
            self.turn_number,
            priority_types,
        )
        
        if retrieved_memories.strip():
            sections.append("### LONG-TERM MEMORY (Retrieved)")
            sections.append(retrieved_memories)
        
        return "\n\n".join(sections)

    def get_prompt_context(
        self, 
        user_message: str,
        priority_types: Optional[List[str]] = None,
    ) -> str:
        """
        Get memory context without processing the turn.
        Useful for testing retrieval without extraction.
        
        Args:
            user_message: Message to retrieve memories for
            priority_types: Memory types to prioritize
        
        Returns:
            Formatted memory context
        """
        return self._compose_prompt_context(user_message, priority_types)

    def update_core_memory(self, file: str, section: str, field: str, value: str):
        """
        Update a field in core memory.
        Use sparingly - only for high-confidence identity updates.
        
        Args:
            file: Core file name (e.g., "CORE.md")
            section: Section within the file
            field: Field to update
            value: New value
        """
        self.flat_file_store.update_core_field(file, section, field, value)
        logger.info(f"Updated core memory: {file} -> {section} -> {field}")

    def get_statistics(self) -> Dict:
        """
        Get memory system statistics.
        
        Returns:
            Dictionary with counts and metrics
        """
        stats = {
            'total_turns': self.turn_number,
            'total_memories': self.redis_store.count_memories(),
            'memories_by_type': {},
            'extraction_count': self.extractor.extraction_count,
        }
        
        # Count by type
        from .config import MEMORY_TYPES
        for mem_type in MEMORY_TYPES:
            count = self.redis_store.count_memories_by_type(mem_type)
            if count > 0:
                stats['memories_by_type'][mem_type] = count
        
        return stats

    def clear_memories(self):
        """Clear all long-term memories (use with caution!)"""
        logger.warning(f"Clearing all memories for user {self.user_id}")
        self.redis_store.clear_all_memories()

    def health_check(self) -> Dict[str, bool]:
        """
        Check health of all storage layers.
        
        Returns:
            Dictionary with status of each component
        """
        return {
            'redis': self.redis_store.health_check(),
            'flat_files': self.flat_file_store.user_dir.exists(),
        }
