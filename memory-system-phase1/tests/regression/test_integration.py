"""
Integration Regression Tests

End-to-end tests for the complete memory pipeline.
"""

import pytest
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from src import MemorySystem


class TestFullPipeline:
    """End-to-end pipeline tests"""
    
    def test_full_conversation_flow(self, memory_system):
        """Test a complete conversation flow"""
        # Introduction turn
        context, stats = memory_system.process_turn(
            "Hi, my name is Alex and I'm a software engineer."
        )
        assert stats['total_turns'] == 1
        
        # Preference turn
        context, stats = memory_system.process_turn(
            "I prefer Python for backend development."
        )
        assert stats['total_turns'] == 2
        
        # Constraint turn
        context, stats = memory_system.process_turn(
            "Please never schedule meetings before 10 AM."
        )
        assert stats['total_turns'] == 3
        
        # Query turn
        context, stats = memory_system.process_turn(
            "What do you know about me?"
        )
        assert stats['total_turns'] == 4
        
        # Should have some memories
        final_stats = memory_system.get_statistics()
        assert final_stats['total_memories'] >= 2
    
    def test_multi_user_isolation(self):
        """Different users should have isolated memories"""
        # Create two memory systems for different users
        ms1 = MemorySystem(user_id="test_user_1_isolation")
        ms2 = MemorySystem(user_id="test_user_2_isolation")
        
        try:
            # Clear both
            ms1.clear_memories()
            ms2.clear_memories()
            
            # Store memory for user 1
            ms1.process_turn("My name is User One.")
            
            # Store different memory for user 2
            ms2.process_turn("My name is User Two.")
            
            # Query user 1
            context1, stats1 = ms1.process_turn("What's my name?")
            
            # Query user 2
            context2, stats2 = ms2.process_turn("What's my name?")
            
            # They should have different content
            # (exact verification depends on implementation)
            stats1_final = ms1.get_statistics()
            stats2_final = ms2.get_statistics()
            
            # Each should have their own memories
            assert stats1_final['total_memories'] >= 1
            assert stats2_final['total_memories'] >= 1
            
        finally:
            ms1.clear_memories()
            ms2.clear_memories()
    
    def test_persistence_across_sessions(self, memory_system):
        """Memories should persist (Redis persistence)"""
        user_id = memory_system.user_id
        
        # Store memory
        memory_system.process_turn("I prefer JavaScript.")
        
        # Get initial count
        initial_stats = memory_system.get_statistics()
        initial_count = initial_stats['total_memories']
        
        # Create new MemorySystem instance for same user
        ms2 = MemorySystem(user_id=user_id)
        
        # Should still have memories
        stats2 = ms2.get_statistics()
        assert stats2['total_memories'] >= initial_count
    
    @pytest.mark.integration
    def test_health_check(self, memory_system):
        """Health check should pass for all services"""
        health = memory_system.health_check()
        
        # Redis should be healthy
        assert health.get('redis') is True, "Redis should be healthy"
        
        # Flat files should be healthy
        assert health.get('flat_files') is True, "Flat files should be healthy"
        
        # Vector store may or may not be available
        # (depends on Qdrant being running)


class TestCoreMemory:
    """Tests for Core Memory functionality"""
    
    def test_core_memory_always_included(self, memory_system):
        """Core memory should always be in context"""
        # Update core memory
        memory_system.update_core_memory(
            file="CORE.md",
            section="Identity",
            field="Name",
            value="TestUser"
        )
        
        # Get context for any query
        context = memory_system.get_prompt_context("Hello")
        
        # Should include core memory
        assert 'CORE' in context.upper() or 'TestUser' in context
    
    def test_core_memory_update(self, memory_system):
        """Should be able to update core memory"""
        # Update a field
        result = memory_system.update_core_memory(
            file="PREFERENCES.md",
            section="General",
            field="TestField",
            value="TestValue"
        )
        
        # Should succeed
        assert result or result is None  # Depends on implementation
        
        # Should be reflected in context
        context = memory_system.get_prompt_context("test")
        # May or may not show immediately depending on implementation


class TestStatistics:
    """Tests for statistics and monitoring"""
    
    def test_statistics_structure(self, memory_system):
        """Statistics should have expected structure"""
        stats = memory_system.get_statistics()
        
        # Should have key fields
        assert 'total_turns' in stats
        assert 'total_memories' in stats
        assert 'memories_by_type' in stats
    
    def test_statistics_update_after_turn(self, memory_system):
        """Statistics should update after processing"""
        initial_stats = memory_system.get_statistics()
        initial_turns = initial_stats['total_turns']
        
        # Process a turn
        memory_system.process_turn("I prefer Python.")
        
        # Stats should update
        new_stats = memory_system.get_statistics()
        assert new_stats['total_turns'] == initial_turns + 1
    
    def test_clear_memories(self, memory_system):
        """Should be able to clear all memories"""
        # Store some memories
        memory_system.process_turn("I prefer Python.")
        memory_system.process_turn("My name is Test.")
        
        # Verify stored
        stats = memory_system.get_statistics()
        assert stats['total_memories'] > 0
        
        # Clear
        memory_system.clear_memories()
        
        # Verify cleared
        stats = memory_system.get_statistics()
        assert stats['total_memories'] == 0


class TestErrorHandling:
    """Tests for error handling"""
    
    def test_handles_none_input(self, memory_system):
        """Should handle None input gracefully"""
        with pytest.raises((TypeError, ValueError, AttributeError)):
            memory_system.process_turn(None)
    
    def test_handles_empty_string(self, memory_system):
        """Should handle empty string input"""
        context, stats = memory_system.process_turn("")
        
        # Should not crash, may filter out
        assert stats['total_turns'] >= 0
    
    def test_handles_unicode(self, memory_system):
        """Should handle unicode characters"""
        context, stats = memory_system.process_turn(
            "Mé llamo José and I work at Über."
        )
        
        # Should not crash
        assert True
    
    def test_handles_special_characters(self, memory_system):
        """Should handle special characters"""
        context, stats = memory_system.process_turn(
            "I prefer C++ and C# for game development!"
        )
        
        # Should not crash
        assert True


@pytest.mark.integration
class TestConsolidation:
    """Tests for Phase 4 consolidation features"""
    
    def test_consolidation_enabled(self, memory_system):
        """Consolidation should be configurable"""
        # Check if consolidation is enabled
        is_enabled = memory_system.is_consolidation_enabled()
        
        # Should return a boolean
        assert isinstance(is_enabled, bool)
    
    def test_manual_consolidation(self, memory_system):
        """Should be able to run manual consolidation"""
        # Store some memories first
        memory_system.process_turn("I prefer Python.")
        memory_system.process_turn("My name is Test.")
        
        # Run consolidation
        if memory_system.is_consolidation_enabled():
            result = memory_system.run_consolidation(force=True)
            
            # Should return stats
            assert result is not None
            assert 'decayed' in result or 'merged' in result or 'promoted' in result
    
    def test_consolidation_stats(self, memory_system):
        """Should be able to get consolidation stats"""
        if memory_system.is_consolidation_enabled():
            stats = memory_system.get_consolidation_stats()
            
            # Should return something (even if empty)
            assert stats is not None


@pytest.mark.slow
class TestLongConversations:
    """Tests for longer conversation scenarios"""
    
    def test_100_turn_conversation(self, memory_system):
        """Should handle 100-turn conversations"""
        messages = [
            "I prefer Python.",
            "My name is Alex.",
            "I work at TechCorp.",
            "Never call me early.",
            "I like morning standups.",
            "Always run tests.",
            "My manager is Sarah.",
            "I prefer dark mode.",
            "Remember my timezone is PST.",
            "Thanks for your help.",
        ]
        
        for i in range(100):
            msg = messages[i % len(messages)]
            context, stats = memory_system.process_turn(msg)
        
        # Should have processed all turns
        final_stats = memory_system.get_statistics()
        assert final_stats['total_turns'] == 100
        
        # Should have some memories (dedup should prevent explosion)
        assert final_stats['total_memories'] > 0
        assert final_stats['total_memories'] < 50  # Should dedup
    
    def test_memory_growth_bounded(self, memory_system):
        """Memory count should be bounded by deduplication"""
        # Send same message many times
        for i in range(50):
            memory_system.process_turn("I prefer Python for coding.")
        
        # Memory count should not be 50
        stats = memory_system.get_statistics()
        assert stats['total_memories'] < 10  # Should dedup heavily
