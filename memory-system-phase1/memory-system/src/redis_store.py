"""
Redis Storage Layer - Long-Term Memory
Handles structured key-value storage with indices
"""

import logging
import json
import time
from typing import Dict, List, Optional, Set
from datetime import datetime
import redis

from .config import (
    REDIS_HOST,
    REDIS_PORT,
    REDIS_DB,
    REDIS_MEMORY_PREFIX,
    REDIS_DEDUP_PREFIX,
    REDIS_TYPE_INDEX_PREFIX,
    REDIS_RECENCY_INDEX,
    MEMORY_FIELDS,
)

logger = logging.getLogger(__name__)


class RedisStore:
    """Manages Redis storage for long-term memories"""

    def __init__(self):
        try:
            self.client = redis.Redis(
                host=REDIS_HOST,
                port=REDIS_PORT,
                db=REDIS_DB,
                decode_responses=True,
            )
            # Test connection
            self.client.ping()
            logger.info(f"Connected to Redis at {REDIS_HOST}:{REDIS_PORT}")
        except redis.ConnectionError as e:
            logger.error(f"Failed to connect to Redis: {e}")
            raise

    def store_memory(self, memory: Dict) -> bool:
        """
        Store a memory record in Redis with proper indexing.
        
        Args:
            memory: Dictionary with keys: memory_id, type, key, value, 
                   confidence, turn_number, timestamp, source_text
        
        Returns:
            True if stored successfully, False if duplicate
        """
        memory_id = memory['memory_id']
        memory_type = memory['type']
        memory_key = memory.get('key', '')
        
        # Check for duplicates using dedup key
        dedup_key = f"{REDIS_DEDUP_PREFIX}{memory_type}:{memory_key}"
        existing = self.client.get(dedup_key)
        
        if existing:
            logger.debug(f"Duplicate memory found: {dedup_key} -> {existing}")
            # Update the existing memory's recency
            self._update_recency(existing, memory['timestamp'])
            return False
        
        # Store the full memory record as a hash
        redis_key = f"{REDIS_MEMORY_PREFIX}{memory_id}"
        self.client.hset(redis_key, mapping=memory)
        
        # Create dedup entry
        if memory_key:
            self.client.set(dedup_key, memory_id)
        
        # Add to type-based index
        type_index_key = f"{REDIS_TYPE_INDEX_PREFIX}{memory_type}"
        self.client.sadd(type_index_key, memory_id)
        
        # Add to recency-ordered index (sorted set by timestamp)
        self.client.zadd(REDIS_RECENCY_INDEX, {memory_id: memory['timestamp']})
        
        logger.info(f"Stored memory {memory_id} (type={memory_type}, key={memory_key})")
        return True

    def get_memory(self, memory_id: str) -> Optional[Dict]:
        """
        Retrieve a memory by ID.
        
        Args:
            memory_id: Unique memory identifier
        
        Returns:
            Memory dictionary or None if not found
        """
        redis_key = f"{REDIS_MEMORY_PREFIX}{memory_id}"
        memory = self.client.hgetall(redis_key)
        
        if not memory:
            return None
        
        # Convert string fields back to appropriate types
        if 'confidence' in memory:
            memory['confidence'] = float(memory['confidence'])
        if 'turn_number' in memory:
            memory['turn_number'] = int(memory['turn_number'])
        if 'timestamp' in memory:
            memory['timestamp'] = float(memory['timestamp'])
        
        return memory

    def get_memories_by_type(self, memory_type: str, limit: int = 100) -> List[Dict]:
        """
        Retrieve all memories of a specific type.
        
        Args:
            memory_type: Type of memory (preference, constraint, etc.)
            limit: Maximum number to retrieve
        
        Returns:
            List of memory dictionaries
        """
        type_index_key = f"{REDIS_TYPE_INDEX_PREFIX}{memory_type}"
        memory_ids = self.client.smembers(type_index_key)
        
        memories = []
        for memory_id in list(memory_ids)[:limit]:
            memory = self.get_memory(memory_id)
            if memory:
                memories.append(memory)
        
        return memories

    def get_recent_memories(self, limit: int = 20) -> List[Dict]:
        """
        Retrieve the N most recent memories.
        
        Args:
            limit: Maximum number to retrieve
        
        Returns:
            List of memory dictionaries, sorted by recency (newest first)
        """
        # Get most recent memory IDs from sorted set (reverse order)
        memory_ids = self.client.zrevrange(REDIS_RECENCY_INDEX, 0, limit - 1)
        
        memories = []
        for memory_id in memory_ids:
            memory = self.get_memory(memory_id)
            if memory:
                memories.append(memory)
        
        return memories

    def _update_recency(self, memory_id: str, timestamp: float):
        """Update the timestamp of a memory in the recency index"""
        self.client.zadd(REDIS_RECENCY_INDEX, {memory_id: timestamp})

    def count_memories(self) -> int:
        """Count total number of stored memories"""
        return self.client.zcard(REDIS_RECENCY_INDEX)

    def count_memories_by_type(self, memory_type: str) -> int:
        """Count memories of a specific type"""
        type_index_key = f"{REDIS_TYPE_INDEX_PREFIX}{memory_type}"
        return self.client.scard(type_index_key)

    def delete_memory(self, memory_id: str) -> bool:
        """
        Delete a memory and all its indices.
        
        Args:
            memory_id: Memory to delete
        
        Returns:
            True if deleted, False if not found
        """
        # Get memory to find its type and key
        memory = self.get_memory(memory_id)
        if not memory:
            return False
        
        # Delete from main storage
        redis_key = f"{REDIS_MEMORY_PREFIX}{memory_id}"
        self.client.delete(redis_key)
        
        # Delete from dedup index
        if memory.get('key'):
            dedup_key = f"{REDIS_DEDUP_PREFIX}{memory['type']}:{memory['key']}"
            self.client.delete(dedup_key)
        
        # Remove from type index
        type_index_key = f"{REDIS_TYPE_INDEX_PREFIX}{memory['type']}"
        self.client.srem(type_index_key, memory_id)
        
        # Remove from recency index
        self.client.zrem(REDIS_RECENCY_INDEX, memory_id)
        
        logger.info(f"Deleted memory {memory_id}")
        return True

    def clear_all_memories(self):
        """Clear all memories (use with caution!)"""
        logger.warning("Clearing ALL memories from Redis")
        
        # Get all memory IDs
        memory_ids = self.client.zrange(REDIS_RECENCY_INDEX, 0, -1)
        
        # Delete each memory properly
        for memory_id in memory_ids:
            self.delete_memory(memory_id)

    def health_check(self) -> bool:
        """Check if Redis is responsive"""
        try:
            return self.client.ping()
        except:
            return False
