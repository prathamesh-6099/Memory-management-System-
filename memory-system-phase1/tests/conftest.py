"""
Pytest Configuration and Fixtures

Provides shared fixtures for memory system tests.
"""

import pytest
import sys
import os
import time

# Add project root to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src import MemorySystem
from src.config import (
    EXTRACTION_CLASSIFIER_THRESHOLD,
    SENSORY_FILTER_THRESHOLD,
)


# Test user IDs - use unique IDs to avoid conflicts
TEST_USER_PREFIX = "test_user_"


@pytest.fixture(scope="function")
def memory_system():
    """
    Create a fresh MemorySystem instance for each test.
    
    Clears memories before and after each test.
    """
    user_id = f"{TEST_USER_PREFIX}{int(time.time() * 1000)}"
    
    try:
        ms = MemorySystem(user_id=user_id)
        ms.clear_memories()
        yield ms
        # Cleanup after test
        ms.clear_memories()
    except Exception as e:
        pytest.skip(f"Could not initialize MemorySystem: {e}")


@pytest.fixture(scope="module")
def shared_memory_system():
    """
    Shared MemorySystem instance for a test module.
    
    Use when tests need to share state.
    """
    user_id = f"{TEST_USER_PREFIX}shared"
    
    try:
        ms = MemorySystem(user_id=user_id)
        ms.clear_memories()
        yield ms
        ms.clear_memories()
    except Exception as e:
        pytest.skip(f"Could not initialize MemorySystem: {e}")


@pytest.fixture
def sample_messages():
    """Provide sample messages for testing"""
    return {
        'preference': [
            "I prefer Python for data analysis.",
            "I like working in the morning.",
            "Dark mode is my preference for all IDEs.",
        ],
        'constraint': [
            "Never call me before 9 AM.",
            "Don't schedule meetings on Fridays.",
            "Never push directly to main branch.",
        ],
        'instruction': [
            "Always run tests before committing.",
            "Remember to update documentation.",
            "Make sure to review code before merging.",
        ],
        'entity': [
            "My name is Alex.",
            "I work at TechCorp.",
            "My manager is Jordan.",
        ],
        'empty': [
            "Hi",
            "Thanks",
            "Okay",
            "Got it",
        ],
    }


@pytest.fixture
def config_values():
    """Provide configuration values for validation"""
    return {
        'extraction_threshold': EXTRACTION_CLASSIFIER_THRESHOLD,
        'sensory_threshold': SENSORY_FILTER_THRESHOLD,
    }


# Markers for test categorization
def pytest_configure(config):
    """Configure custom markers"""
    config.addinivalue_line(
        "markers", "slow: marks tests as slow (deselect with '-m \"not slow\"')"
    )
    config.addinivalue_line(
        "markers", "integration: marks tests as integration tests"
    )
    config.addinivalue_line(
        "markers", "benchmark: marks tests as performance benchmarks"
    )
    config.addinivalue_line(
        "markers", "requires_llm: marks tests that require LLM API"
    )


# Helper functions available to all tests
def assert_memory_extracted(stats: dict, min_count: int = 1):
    """Assert that at least min_count memories were extracted"""
    assert stats.get('extracted_count', 0) >= min_count, \
        f"Expected at least {min_count} extractions, got {stats.get('extracted_count', 0)}"


def assert_memory_stored(stats: dict, min_count: int = 1):
    """Assert that at least min_count memories were stored"""
    assert stats.get('stored_count', 0) >= min_count, \
        f"Expected at least {min_count} stored, got {stats.get('stored_count', 0)}"


def assert_memory_retrieved(stats: dict, min_count: int = 1):
    """Assert that at least min_count memories were retrieved"""
    assert stats.get('retrieved_count', 0) >= min_count, \
        f"Expected at least {min_count} retrieved, got {stats.get('retrieved_count', 0)}"
