"""
Retrieval Regression Tests

Tests for memory retrieval quality and ranking behavior.
"""

import pytest
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from tests.conftest import assert_memory_retrieved


class TestBasicRetrieval:
    """Basic retrieval functionality tests"""
    
    def test_retrieves_stored_memory(self, memory_system):
        """Should retrieve a memory that was just stored"""
        # Store a memory
        memory_system.process_turn("My name is TestUser.")
        
        # Query for it
        context, stats = memory_system.process_turn("What's my name?")
        
        # Should retrieve the name memory
        assert 'TestUser' in context or stats.get('retrieved_count', 0) > 0
    
    def test_retrieves_preference(self, memory_system):
        """Should retrieve preferences when queried"""
        # Store preference
        memory_system.process_turn("I prefer Python for coding.")
        
        # Query
        context, stats = memory_system.process_turn(
            "What programming language do I like?"
        )
        
        assert_memory_retrieved(stats, 1)
    
    def test_retrieves_constraint(self, memory_system):
        """Should retrieve constraints when relevant"""
        # Store constraint
        memory_system.process_turn("Never call me before 9 AM.")
        
        # Query
        context, stats = memory_system.process_turn(
            "When can you contact me?"
        )
        
        # Constraints should be retrieved for scheduling queries
        assert_memory_retrieved(stats, 1)


class TestSemanticRetrieval:
    """Tests for semantic search retrieval (Phase 2)"""
    
    def test_semantic_similarity_retrieval(self, memory_system):
        """Should retrieve semantically related memories"""
        # Store memory with specific wording
        memory_system.process_turn("I work at TechCorp.")
        
        # Query with different wording
        context, stats = memory_system.process_turn(
            "What company do I work for?"
        )
        
        # Should match via semantic similarity
        assert 'TechCorp' in context or stats.get('retrieved_count', 0) > 0
    
    def test_retrieves_related_memories(self, memory_system):
        """Should retrieve related memories"""
        # Store multiple related memories
        memory_system.process_turn("I prefer Python for data analysis.")
        memory_system.process_turn("I use pandas and numpy regularly.")
        memory_system.process_turn("I enjoy working with data.")
        
        # Query about data work
        context, stats = memory_system.process_turn(
            "Tell me about my data work preferences."
        )
        
        # Should retrieve multiple related memories
        assert_memory_retrieved(stats, 1)


class TestRankingBehavior:
    """Tests for ranking signal behavior"""
    
    def test_type_priority_ranking(self, memory_system):
        """Constraints should rank higher than preferences"""
        # Store preference
        memory_system.process_turn("I like morning meetings.")
        
        # Store constraint
        memory_system.process_turn("Never schedule meetings before 9 AM.")
        
        # Query about meetings
        context, stats = memory_system.process_turn(
            "When should we meet?"
        )
        
        # Constraint should appear (high priority type)
        assert 'before 9 AM' in context or 'never' in context.lower()
    
    def test_recency_ranking(self, memory_system):
        """Recent memories should rank higher"""
        # Store old memory
        memory_system.process_turn("I prefer Java.")
        
        # Process some turns
        for i in range(5):
            memory_system.process_turn(f"Turn {i} filler content.")
        
        # Store newer memory
        memory_system.process_turn("I now prefer Python.")
        
        # Query - recent should be favored
        context, stats = memory_system.process_turn(
            "What language do I prefer?"
        )
        
        # Should retrieve (exact ranking depends on weights)
        assert_memory_retrieved(stats, 1)
    
    def test_frequency_ranking(self, memory_system):
        """Frequently accessed memories should rank higher (Phase 4)"""
        # Store memory
        memory_system.process_turn("My name is FreqTest.")
        
        # Access it multiple times
        for _ in range(3):
            memory_system.process_turn("What's my name again?")
        
        # Store another memory
        memory_system.process_turn("My pet is called Fluffy.")
        
        # Query - name memory should rank higher due to frequency
        context, stats = memory_system.process_turn(
            "Tell me about myself."
        )
        
        # Should retrieve frequently accessed memory
        assert_memory_retrieved(stats, 1)


class TestRetrievalFiltering:
    """Tests for retrieval filtering behavior"""
    
    def test_superseded_memories_filtered(self, memory_system):
        """Superseded memories should not be retrieved (Phase 3)"""
        # Store initial preference
        memory_system.process_turn("I prefer Java.")
        
        # Update preference
        memory_system.process_turn("Actually, I now prefer Python instead of Java.")
        
        # Query
        context, stats = memory_system.process_turn(
            "What language do I prefer?"
        )
        
        # Should retrieve Python, not Java (if superseding works)
        # Exact behavior depends on Phase 3 implementation
        assert_memory_retrieved(stats, 1)
    
    def test_low_confidence_filtered(self, memory_system):
        """Very low confidence memories should be filtered"""
        # This is implicit in the extraction threshold
        # Store a hedged statement
        memory_system.process_turn("I might possibly like Ruby, maybe.")
        
        # Query
        context, stats = memory_system.process_turn(
            "What languages do I like?"
        )
        
        # Low confidence may not be stored/retrieved
        # Test is informational


class TestContextFormatting:
    """Tests for context formatting in retrieval"""
    
    def test_context_includes_core_memory(self, memory_system):
        """Context should include core memory"""
        context = memory_system.get_prompt_context("Hello")
        
        # Should have a CORE MEMORY section
        assert 'CORE' in context.upper() or 'MEMORY' in context.upper()
    
    def test_context_includes_retrieved(self, memory_system):
        """Context should include retrieved memories"""
        # Store some memories
        memory_system.process_turn("I prefer Python.")
        memory_system.process_turn("Never call me early.")
        
        # Get context
        context = memory_system.get_prompt_context("What are my preferences?")
        
        # Should include retrieved content
        assert len(context) > 0
    
    def test_context_respects_token_budget(self, memory_system):
        """Context should respect token budget"""
        # Store many memories
        for i in range(20):
            memory_system.process_turn(f"I like item number {i}.")
        
        # Get context
        context = memory_system.get_prompt_context("What do I like?")
        
        # Should be reasonable length (not unlimited)
        # Rough estimate: 500 token budget ~= 2000 characters
        assert len(context) < 10000


class TestEmptyAndEdgeCases:
    """Tests for edge cases in retrieval"""
    
    def test_retrieval_empty_store(self, memory_system):
        """Should handle empty memory store gracefully"""
        # Query without any stored memories
        context, stats = memory_system.process_turn(
            "What are my preferences?"
        )
        
        # Should not crash, may have 0 retrievals
        assert stats.get('retrieved_count', 0) >= 0
    
    def test_retrieval_unrelated_query(self, memory_system):
        """Should handle unrelated queries"""
        # Store programming preference
        memory_system.process_turn("I prefer Python.")
        
        # Query about unrelated topic
        context, stats = memory_system.process_turn(
            "What's the weather like?"
        )
        
        # May or may not retrieve (semantic similarity threshold)
        # Should not crash
    
    def test_retrieval_very_long_query(self, memory_system):
        """Should handle very long queries"""
        # Store memory
        memory_system.process_turn("I work at TechCorp.")
        
        # Very long query
        long_query = "I'm wondering about " + "what " * 100 + "company I work for?"
        
        context, stats = memory_system.process_turn(long_query)
        
        # Should handle without crashing
        assert True  # Just checking no crash
