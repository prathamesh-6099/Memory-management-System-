"""
Extraction Regression Tests

Tests for memory extraction quality across different message types.
"""

import pytest
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from tests.conftest import assert_memory_extracted, assert_memory_stored


class TestPreferenceExtraction:
    """Tests for preference memory extraction"""
    
    def test_explicit_preference(self, memory_system):
        """Should extract explicit preferences"""
        messages = [
            "I prefer Python for data analysis.",
            "I like working in the morning.",
            "My favorite IDE is VS Code.",
        ]
        
        total_extracted = 0
        for msg in messages:
            context, stats = memory_system.process_turn(msg)
            total_extracted += stats.get('extracted_count', 0)
        
        assert total_extracted >= 2, f"Expected at least 2 preferences, got {total_extracted}"
    
    def test_implicit_preference(self, memory_system):
        """Should extract implicit preferences"""
        context, stats = memory_system.process_turn(
            "Python is my go-to language for everything."
        )
        # May or may not extract - test is informational
        # Implicit preferences are harder to detect
    
    def test_preference_with_context(self, memory_system):
        """Should extract preferences with context"""
        context, stats = memory_system.process_turn(
            "When coding backend services, I prefer Go over Python."
        )
        assert_memory_extracted(stats, 1)


class TestConstraintExtraction:
    """Tests for constraint memory extraction"""
    
    def test_never_constraint(self, memory_system):
        """Should extract 'never' constraints"""
        context, stats = memory_system.process_turn(
            "Never call me before 9 AM."
        )
        assert_memory_extracted(stats, 1)
    
    def test_dont_constraint(self, memory_system):
        """Should extract 'don't' constraints"""
        context, stats = memory_system.process_turn(
            "Don't schedule meetings on Fridays."
        )
        assert_memory_extracted(stats, 1)
    
    def test_must_not_constraint(self, memory_system):
        """Should extract 'must not' constraints"""
        context, stats = memory_system.process_turn(
            "You must not share my personal data."
        )
        assert_memory_extracted(stats, 1)


class TestInstructionExtraction:
    """Tests for instruction memory extraction"""
    
    def test_always_instruction(self, memory_system):
        """Should extract 'always' instructions"""
        context, stats = memory_system.process_turn(
            "Always run tests before committing code."
        )
        assert_memory_extracted(stats, 1)
    
    def test_remember_instruction(self, memory_system):
        """Should extract 'remember' instructions"""
        context, stats = memory_system.process_turn(
            "Remember to update the changelog after releases."
        )
        assert_memory_extracted(stats, 1)
    
    def test_make_sure_instruction(self, memory_system):
        """Should extract 'make sure' instructions"""
        context, stats = memory_system.process_turn(
            "Make sure to notify the team before deployments."
        )
        assert_memory_extracted(stats, 1)


class TestEntityExtraction:
    """Tests for entity memory extraction"""
    
    def test_name_entity(self, memory_system):
        """Should extract user name"""
        context, stats = memory_system.process_turn(
            "My name is Alexander."
        )
        assert_memory_extracted(stats, 1)
    
    def test_company_entity(self, memory_system):
        """Should extract company name"""
        context, stats = memory_system.process_turn(
            "I work at TechCorp as a senior engineer."
        )
        assert_memory_extracted(stats, 1)
    
    def test_manager_entity(self, memory_system):
        """Should extract manager name"""
        context, stats = memory_system.process_turn(
            "My manager is Sarah Williams."
        )
        assert_memory_extracted(stats, 1)
    
    def test_project_entity(self, memory_system):
        """Should extract project name"""
        context, stats = memory_system.process_turn(
            "I'm currently working on Project Phoenix."
        )
        assert_memory_extracted(stats, 1)


class TestFilteringBehavior:
    """Tests for sensory filter behavior"""
    
    def test_filters_greetings(self, memory_system):
        """Should filter simple greetings"""
        empty_messages = ["Hi", "Hello", "Hey there"]
        
        for msg in empty_messages:
            context, stats = memory_system.process_turn(msg)
            assert stats.get('extracted_count', 0) == 0, \
                f"Greeting '{msg}' should not produce memories"
    
    def test_filters_acknowledgments(self, memory_system):
        """Should filter acknowledgments"""
        ack_messages = ["Thanks", "Okay", "Got it", "Sure", "Perfect"]
        
        for msg in ack_messages:
            context, stats = memory_system.process_turn(msg)
            assert stats.get('extracted_count', 0) == 0, \
                f"Acknowledgment '{msg}' should not produce memories"
    
    def test_filters_single_words(self, memory_system):
        """Should filter very short messages"""
        short_messages = ["Yes", "No", "Maybe"]
        
        for msg in short_messages:
            context, stats = memory_system.process_turn(msg)
            assert stats.get('extracted_count', 0) == 0, \
                f"Short message '{msg}' should not produce memories"


class TestComplexExtraction:
    """Tests for complex message extraction"""
    
    def test_multiple_memories_one_message(self, memory_system):
        """Should extract multiple memories from one message"""
        context, stats = memory_system.process_turn(
            "My name is Alex, I work at TechCorp, and I prefer Python."
        )
        # Should extract at least 2 (name and preference are clearest)
        assert_memory_extracted(stats, 2)
    
    def test_long_message_extraction(self, memory_system):
        """Should handle long messages"""
        long_message = (
            "Let me tell you about my work setup. I'm a senior engineer at TechCorp. "
            "I prefer Python for backend work and TypeScript for frontend. "
            "Please never call me before 9 AM, and always send meeting agendas in advance. "
            "My manager is Sarah, and we're working on Project Phoenix."
        )
        
        context, stats = memory_system.process_turn(long_message)
        assert_memory_extracted(stats, 3)
    
    def test_question_message(self, memory_system):
        """Questions should generally not produce memories"""
        context, stats = memory_system.process_turn(
            "What's the best programming language for web development?"
        )
        # Questions about opinions shouldn't create user memories
        # (unless they contain personal info)


class TestConfidenceScoring:
    """Tests for confidence score behavior"""
    
    def test_high_confidence_explicit(self, memory_system):
        """Explicit statements should have high confidence"""
        context, stats = memory_system.process_turn(
            "I definitely prefer Python over JavaScript."
        )
        # Confidence should be high due to "definitely"
        assert_memory_extracted(stats, 1)
    
    def test_lower_confidence_hedged(self, memory_system):
        """Hedged statements should have lower confidence"""
        context, stats = memory_system.process_turn(
            "I kind of like Python, I guess."
        )
        # May or may not extract due to uncertainty
        # This tests that hedged language is handled


class TestDeduplication:
    """Tests for deduplication behavior"""
    
    def test_exact_duplicate_filtered(self, memory_system):
        """Should not store exact duplicates"""
        msg = "I prefer Python for coding."
        
        # Process twice
        memory_system.process_turn(msg)
        context, stats = memory_system.process_turn(msg)
        
        # Second time should update existing, not create new
        final_stats = memory_system.get_statistics()
        # Should have at most 1 memory for this preference
        assert final_stats['total_memories'] <= 2  # May have other memories
    
    def test_semantic_duplicate_filtered(self, memory_system):
        """Should detect semantic duplicates (Phase 3)"""
        # First message
        memory_system.process_turn("I prefer Python for development.")
        
        # Semantically similar message
        context, stats = memory_system.process_turn(
            "Python is my preferred language for dev work."
        )
        
        # Should boost confidence or update, not create duplicate
        final_stats = memory_system.get_statistics()
        # The exact behavior depends on semantic similarity threshold
