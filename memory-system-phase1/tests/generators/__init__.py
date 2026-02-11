"""
Test Generators for Memory System Evaluation

Includes:
- Synthetic conversation generator
- Ground truth tracking
"""

from .synthetic_generator import (
    SyntheticGenerator,
    ConversationTemplate,
    generate_test_suite,
)
from .ground_truth import GroundTruthBuilder

__all__ = [
    'SyntheticGenerator',
    'ConversationTemplate',
    'GroundTruthBuilder',
    'generate_test_suite',
]
