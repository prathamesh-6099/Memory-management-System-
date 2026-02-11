"""
Ground Truth Builder

Helps construct ground truth data for test cases.
"""

from typing import List, Dict, Any, Set, Optional
from dataclasses import dataclass, field
import sys
import os

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'src'))

from src.evaluation.evaluator import GroundTruth, TestCase


class GroundTruthBuilder:
    """
    Builder for constructing ground truth test cases.
    
    Makes it easy to create test conversations with expected
    extractions and retrievals.
    """
    
    def __init__(self, name: str, description: str = ""):
        """
        Initialize builder.
        
        Args:
            name: Test case name
            description: Test case description
        """
        self.name = name
        self.description = description
        self.turns: List[GroundTruth] = []
        self.tags: List[str] = []
        self._turn_counter = 0
        self._memory_id_map: Dict[str, str] = {}  # Track memory IDs for retrieval tests
    
    def add_tag(self, tag: str) -> 'GroundTruthBuilder':
        """Add a tag to the test case"""
        self.tags.append(tag)
        return self
    
    def add_turn(
        self,
        message: str,
        expected_memories: List[Dict[str, Any]] = None,
        relevant_memory_ids: Set[str] = None,
        tags: List[str] = None,
    ) -> 'GroundTruthBuilder':
        """
        Add a conversation turn with ground truth.
        
        Args:
            message: The user message
            expected_memories: List of expected memory extractions
            relevant_memory_ids: Set of memory IDs that should be retrieved
            tags: Tags for this turn
            
        Returns:
            self for chaining
        """
        self._turn_counter += 1
        
        gt = GroundTruth(
            turn=self._turn_counter,
            message=message,
            expected_memories=expected_memories or [],
            relevant_memory_ids=relevant_memory_ids or set(),
            tags=tags or [],
        )
        
        self.turns.append(gt)
        return self
    
    def add_info_turn(
        self,
        message: str,
        memory_type: str,
        key: str,
        value: str,
        confidence: float = 0.8,
        memory_id: str = None,
    ) -> 'GroundTruthBuilder':
        """
        Convenience method: Add turn with single expected memory.
        
        Args:
            message: User message containing information
            memory_type: Expected type (preference, constraint, etc.)
            key: Expected key
            value: Expected value
            confidence: Expected confidence
            memory_id: Optional ID for tracking (used in retrieval tests)
            
        Returns:
            self for chaining
        """
        expected = {
            'type': memory_type,
            'key': key,
            'value': value,
            'confidence': confidence,
        }
        
        self._turn_counter += 1
        
        # Track memory ID if provided
        if memory_id:
            self._memory_id_map[memory_id] = f"mem_{self._turn_counter}"
        
        gt = GroundTruth(
            turn=self._turn_counter,
            message=message,
            expected_memories=[expected],
        )
        
        self.turns.append(gt)
        return self
    
    def add_query_turn(
        self,
        query: str,
        relevant_ids: List[str],
    ) -> 'GroundTruthBuilder':
        """
        Add a query turn that should retrieve specific memories.
        
        Args:
            query: The query message
            relevant_ids: List of memory IDs (from add_info_turn) that should be retrieved
            
        Returns:
            self for chaining
        """
        self._turn_counter += 1
        
        # Map symbolic IDs to actual turn-based IDs
        resolved_ids = set()
        for id in relevant_ids:
            if id in self._memory_id_map:
                resolved_ids.add(self._memory_id_map[id])
            else:
                resolved_ids.add(id)
        
        gt = GroundTruth(
            turn=self._turn_counter,
            message=query,
            relevant_memory_ids=resolved_ids,
        )
        
        self.turns.append(gt)
        return self
    
    def add_empty_turn(self, message: str) -> 'GroundTruthBuilder':
        """
        Add a turn that should NOT produce any memories.
        
        Useful for testing that greetings/acknowledgments are filtered.
        
        Args:
            message: The message (e.g., "Hi", "Thanks", "Okay")
            
        Returns:
            self for chaining
        """
        self._turn_counter += 1
        
        gt = GroundTruth(
            turn=self._turn_counter,
            message=message,
            expected_memories=[],
            tags=['should_filter'],
        )
        
        self.turns.append(gt)
        return self
    
    def add_update_turn(
        self,
        message: str,
        old_memory_id: str,
        new_value: str,
        memory_type: str,
        key: str,
    ) -> 'GroundTruthBuilder':
        """
        Add a turn that updates an existing memory.
        
        Args:
            message: The update message
            old_memory_id: ID of the memory being updated
            new_value: The new value
            memory_type: Type of the memory
            key: Key of the memory
            
        Returns:
            self for chaining
        """
        expected = {
            'type': memory_type,
            'key': key,
            'value': new_value,
            'supersedes': old_memory_id,
        }
        
        self._turn_counter += 1
        
        gt = GroundTruth(
            turn=self._turn_counter,
            message=message,
            expected_memories=[expected],
            tags=['update'],
        )
        
        self.turns.append(gt)
        return self
    
    def build(self) -> TestCase:
        """
        Build the final TestCase.
        
        Returns:
            TestCase object ready for evaluation
        """
        return TestCase(
            name=self.name,
            description=self.description,
            conversation=self.turns,
            tags=self.tags,
        )


def build_extraction_test(
    name: str,
    messages_and_expectations: List[tuple],
) -> TestCase:
    """
    Quick helper to build an extraction test case.
    
    Args:
        name: Test name
        messages_and_expectations: List of (message, expected_memories) tuples
        
    Returns:
        TestCase
    """
    builder = GroundTruthBuilder(name)
    
    for item in messages_and_expectations:
        if len(item) == 2:
            message, expected = item
            builder.add_turn(message, expected_memories=expected)
        else:
            # Single message, no expected memories
            builder.add_turn(item[0])
    
    return builder.build()
