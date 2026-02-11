"""
Phase 5 Demo: Evaluation Framework & Test Suites

Demonstrates:
1. Evaluation metrics (precision, recall, F1)
2. Synthetic test generation
3. Memory system evaluation
4. Report generation
"""

import sys
import os
import time
import logging

# Add project root to path
sys.path.insert(0, os.path.dirname(__file__))

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

print("=" * 70)
print(" PHASE 5 DEMO: Evaluation Framework & Test Suites")
print("=" * 70)
print()

# Check dependencies
try:
    from src.evaluation import (
        ExtractionMetrics,
        RetrievalMetrics,
        PerformanceMetrics,
        MemoryEvaluator,
        EvaluationReport,
    )
    from tests.generators import (
        SyntheticGenerator,
        GroundTruthBuilder,
        generate_test_suite,
    )
    print("✓ Phase 5 evaluation framework available")
except ImportError as e:
    print(f"✗ Missing Phase 5 components: {e}")
    sys.exit(1)


def demo_metrics():
    """Demonstrate the metrics classes"""
    print("\n" + "=" * 70)
    print(" DEMO 1: Evaluation Metrics")
    print("=" * 70)
    
    # Extraction Metrics
    print("\n--- Extraction Metrics Example ---")
    extraction = ExtractionMetrics()
    
    # Simulate some evaluation results
    extraction.true_positives = 15
    extraction.false_positives = 3
    extraction.false_negatives = 5
    extraction.correct_values = 13
    extraction.incorrect_values = 2
    
    # Add type-specific results
    extraction.add_type_result('preference', tp=5, fp=1, fn=2)
    extraction.add_type_result('constraint', tp=4, fp=0, fn=1)
    extraction.add_type_result('entity', tp=6, fp=2, fn=2)
    
    print(f"Precision: {extraction.precision:.3f}")
    print(f"Recall: {extraction.recall:.3f}")
    print(f"F1 Score: {extraction.f1:.3f}")
    print(f"Value Accuracy: {extraction.value_accuracy:.3f}")
    
    print("\nBy Type F1:")
    for mem_type in ['preference', 'constraint', 'entity']:
        f1 = extraction.get_type_f1(mem_type)
        print(f"  {mem_type}: {f1:.3f}")
    
    # Retrieval Metrics
    print("\n--- Retrieval Metrics Example ---")
    retrieval = RetrievalMetrics()
    
    # Simulate query results
    retrieval.add_query_result(
        retrieved_ids=['m1', 'm2', 'm3', 'm4', 'm5'],
        relevant_ids={'m1', 'm3', 'm6'},
    )
    retrieval.add_query_result(
        retrieved_ids=['m2', 'm4', 'm1', 'm5'],
        relevant_ids={'m1', 'm2'},
    )
    
    print(f"Precision: {retrieval.precision:.3f}")
    print(f"Recall: {retrieval.recall:.3f}")
    print(f"F1 Score: {retrieval.f1:.3f}")
    print(f"MRR: {retrieval.mrr:.3f}")
    print(f"Precision@3: {retrieval.precision_at_k.get(3, 0):.3f}")
    
    # Performance Metrics
    print("\n--- Performance Metrics Example ---")
    performance = PerformanceMetrics()
    
    # Add simulated timing data
    for i in range(20):
        performance.add_turn_timing(
            extraction_ms=10 + i * 2,
            retrieval_ms=25 + i,
            total_ms=50 + i * 3,
        )
    performance.total_time = 2.0  # seconds
    
    print(f"Avg Extraction: {performance.avg_extraction_latency:.1f}ms")
    print(f"Avg Retrieval: {performance.avg_retrieval_latency:.1f}ms")
    print(f"P50 Latency: {performance.p50_latency:.1f}ms")
    print(f"P90 Latency: {performance.p90_latency:.1f}ms")
    print(f"Throughput: {performance.throughput:.1f} turns/sec")


def demo_synthetic_generator():
    """Demonstrate synthetic test generation"""
    print("\n" + "=" * 70)
    print(" DEMO 2: Synthetic Test Generator")
    print("=" * 70)
    
    print("\n--- Generating Test Conversations ---")
    
    generator = SyntheticGenerator(seed=42)
    
    # Generate sample messages
    print("\nSample Generated Messages:")
    
    msg, exp = generator.generate_preference_message()
    print(f"  Preference: \"{msg}\"")
    print(f"    → Expected: type={exp['type']}, value={exp['value']}")
    
    msg, exp = generator.generate_constraint_message()
    print(f"  Constraint: \"{msg}\"")
    print(f"    → Expected: type={exp['type']}, value={exp['value'][:40]}...")
    
    msg, exp = generator.generate_entity_message()
    print(f"  Entity: \"{msg}\"")
    print(f"    → Expected: type={exp['type']}, key={exp['key']}")
    
    msg, exp = generator.generate_instruction_message()
    print(f"  Instruction: \"{msg}\"")
    print(f"    → Expected: type={exp['type']}")
    
    # Generate a complete test case
    print("\n--- Generated Test Suite ---")
    tests = generate_test_suite(num_standard=2, include_edge_cases=True, seed=42)
    
    print(f"Generated {len(tests)} test cases:")
    for test in tests:
        turn_count = len(test.conversation)
        expected_count = sum(
            len(gt.expected_memories) for gt in test.conversation
        )
        print(f"  • {test.name}: {turn_count} turns, {expected_count} expected memories")
    
    # Show edge case tests
    print("\nEdge Cases Included:")
    edge_tests = [t for t in tests if 'edge_case' in t.tags]
    for test in edge_tests:
        print(f"  • {test.name}: {test.description}")


def demo_ground_truth_builder():
    """Demonstrate ground truth builder"""
    print("\n" + "=" * 70)
    print(" DEMO 3: Ground Truth Builder")
    print("=" * 70)
    
    print("\n--- Building Custom Test Case ---")
    
    builder = GroundTruthBuilder("custom_test", "Custom evaluation test")
    builder.add_tag("demo")
    
    # Add turns with ground truth
    builder.add_info_turn(
        message="My name is TestUser.",
        memory_type="entity",
        key="user_name",
        value="TestUser",
        confidence=0.9,
        memory_id="name_mem"
    )
    
    builder.add_info_turn(
        message="I prefer Python for coding.",
        memory_type="preference",
        key="coding_language",
        value="Python",
        confidence=0.8,
        memory_id="lang_pref"
    )
    
    builder.add_empty_turn("Thanks!")
    builder.add_empty_turn("Got it.")
    
    builder.add_info_turn(
        message="Never call me before 9 AM.",
        memory_type="constraint",
        key="never",
        value="call before 9 AM",
        confidence=0.9,
        memory_id="call_constraint"
    )
    
    # Build the test case
    test_case = builder.build()
    
    print(f"Test: {test_case.name}")
    print(f"Description: {test_case.description}")
    print(f"Tags: {test_case.tags}")
    print(f"Turns: {len(test_case.conversation)}")
    
    print("\nConversation breakdown:")
    for gt in test_case.conversation:
        expected_count = len(gt.expected_memories)
        tags_str = f" [{', '.join(gt.tags)}]" if gt.tags else ""
        print(f"  Turn {gt.turn}: \"{gt.message[:40]}...\" → {expected_count} expected{tags_str}")


def demo_evaluation():
    """Demonstrate the full evaluation flow"""
    print("\n" + "=" * 70)
    print(" DEMO 4: Full Evaluation Flow")
    print("=" * 70)
    
    print("\n--- Initializing Memory System ---")
    
    try:
        from src import MemorySystem
        memory_system = MemorySystem(user_id="eval_demo_user")
        memory_system.clear_memories()
        print("✓ Memory system initialized")
    except Exception as e:
        print(f"✗ Could not initialize memory system: {e}")
        print("  Make sure Redis and Qdrant are running")
        return
    
    # Build a test case
    print("\n--- Creating Test Case ---")
    builder = GroundTruthBuilder("evaluation_demo", "Demo evaluation")
    
    builder.add_info_turn(
        "My name is EvalUser.",
        "entity", "user_name", "EvalUser", 0.9
    )
    builder.add_info_turn(
        "I prefer Python for development.",
        "preference", "language", "Python", 0.8
    )
    builder.add_empty_turn("Thanks")
    builder.add_info_turn(
        "Never schedule meetings on Fridays.",
        "constraint", "never", "schedule meetings on Fridays", 0.9
    )
    builder.add_info_turn(
        "Always run tests before committing.",
        "instruction", "always", "run tests before committing", 0.85
    )
    
    test_case = builder.build()
    print(f"Created test: {test_case.name} with {len(test_case.conversation)} turns")
    
    # Run evaluation
    print("\n--- Running Evaluation ---")
    evaluator = MemoryEvaluator(
        memory_system=memory_system,
        extraction_threshold=0.5,  # Lower threshold for demo
        retrieval_threshold=0.5,
        latency_threshold_ms=500,
    )
    
    start_time = time.perf_counter()
    result = evaluator.evaluate_test_case(test_case)
    elapsed = time.perf_counter() - start_time
    
    print(f"Evaluation completed in {elapsed:.2f}s")
    
    # Print results
    print("\n--- Evaluation Results ---")
    print(f"Test: {result.test_name}")
    print(f"Passed: {'✓ Yes' if result.passed else '✗ No'}")
    
    print(f"\nExtraction:")
    print(f"  Precision: {result.extraction_metrics.precision:.3f}")
    print(f"  Recall: {result.extraction_metrics.recall:.3f}")
    print(f"  F1: {result.extraction_metrics.f1:.3f}")
    print(f"  True Positives: {result.extraction_metrics.true_positives}")
    print(f"  False Positives: {result.extraction_metrics.false_positives}")
    print(f"  False Negatives: {result.extraction_metrics.false_negatives}")
    
    print(f"\nPerformance:")
    print(f"  Turns: {result.performance_metrics.turns_processed}")
    print(f"  Avg Latency: {result.performance_metrics.avg_total_latency:.1f}ms")
    print(f"  Throughput: {result.performance_metrics.throughput:.2f} turns/sec")
    
    if result.failures:
        print(f"\nFailures:")
        for f in result.failures:
            print(f"  ! {f}")
    
    # Generate report
    print("\n--- Generating Report ---")
    report = EvaluationReport([result])
    
    # Console summary
    print("\nConsole Report Preview:")
    print("-" * 40)
    console_report = report.to_console()
    # Print first 30 lines
    for line in console_report.split('\n')[:30]:
        print(line)
    print("...")
    
    # Save reports
    print("\n--- Saving Reports ---")
    report.save("evaluation_report.json", format='json')
    report.save("evaluation_report.md", format='markdown')
    print("✓ Saved evaluation_report.json")
    print("✓ Saved evaluation_report.md")


def demo_pytest_info():
    """Show how to run the regression tests"""
    print("\n" + "=" * 70)
    print(" DEMO 5: Running Regression Tests")
    print("=" * 70)
    
    print("""
To run the regression test suites, use pytest:

# Run all tests
pytest tests/regression/ -v

# Run specific test categories
pytest tests/regression/test_extraction.py -v    # Extraction tests
pytest tests/regression/test_retrieval.py -v     # Retrieval tests
pytest tests/regression/test_integration.py -v   # Integration tests
pytest tests/regression/test_performance.py -v   # Performance benchmarks

# Run with markers
pytest tests/regression/ -v -m "not slow"        # Skip slow tests
pytest tests/regression/ -v -m "benchmark"       # Only benchmarks
pytest tests/regression/ -v -m "integration"     # Only integration tests

# Generate coverage report
pytest tests/regression/ --cov=src --cov-report=html

# Run with parallel execution (requires pytest-xdist)
pytest tests/regression/ -n auto

Test Categories:
- Extraction: Tests for memory extraction from messages
- Retrieval: Tests for memory retrieval and ranking
- Integration: End-to-end pipeline tests
- Performance: Latency and throughput benchmarks
""")


def main():
    """Run all demos"""
    demo_metrics()
    demo_synthetic_generator()
    demo_ground_truth_builder()
    demo_evaluation()
    demo_pytest_info()
    
    print("\n" + "=" * 70)
    print(" Demo Complete!")
    print("=" * 70)
    print("""
Phase 5 Features:

✓ Evaluation Framework:
  - ExtractionMetrics: Precision, Recall, F1 for extraction
  - RetrievalMetrics: MRR, Precision@K for retrieval
  - PerformanceMetrics: Latency percentiles, throughput
  - MemoryEvaluator: Orchestrates evaluation
  - EvaluationReport: JSON, Markdown, console reports

✓ Synthetic Test Generator:
  - SyntheticGenerator: Creates realistic test conversations
  - ConversationTemplate: Customize generation parameters
  - GroundTruthBuilder: Build test cases with expectations
  - Edge case generation: Contradictions, long messages, ambiguity

✓ Regression Test Suites:
  - test_extraction.py: Extraction quality tests
  - test_retrieval.py: Retrieval quality tests
  - test_integration.py: End-to-end tests
  - test_performance.py: Performance benchmarks
  - pytest fixtures and markers for test organization

Run 'pytest tests/regression/ -v' to execute the test suite.
""")


if __name__ == "__main__":
    main()
