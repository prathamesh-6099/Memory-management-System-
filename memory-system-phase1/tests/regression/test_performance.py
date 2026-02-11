"""
Performance Regression Tests

Benchmarks for memory system performance.
"""

import pytest
import time
import sys
import os
import statistics

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))


# Performance thresholds
EXTRACTION_LATENCY_MS = 500    # Max extraction time
RETRIEVAL_LATENCY_MS = 100     # Max retrieval time  
STORAGE_LATENCY_MS = 500       # Max storage time
TOTAL_TURN_LATENCY_MS = 1000   # Max total turn time


def measure_latency(func, *args, **kwargs):
    """Measure function execution time in milliseconds"""
    start = time.perf_counter()
    result = func(*args, **kwargs)
    elapsed_ms = (time.perf_counter() - start) * 1000
    return result, elapsed_ms


@pytest.mark.benchmark
class TestExtractionPerformance:
    """Benchmarks for extraction performance"""
    
    def test_simple_extraction_latency(self, memory_system):
        """Simple extraction should be fast"""
        message = "I prefer Python for coding."
        
        _, latency = measure_latency(memory_system.process_turn, message)
        
        # First call may be slow due to model loading
        # Do a second call for warm benchmark
        _, latency = measure_latency(memory_system.process_turn, 
                                     "I like JavaScript too.")
        
        assert latency < TOTAL_TURN_LATENCY_MS, \
            f"Extraction took {latency:.1f}ms, expected < {TOTAL_TURN_LATENCY_MS}ms"
    
    def test_complex_extraction_latency(self, memory_system):
        """Complex messages should still be reasonably fast"""
        complex_message = (
            "My name is Alexander, I work at TechCorp as a senior engineer. "
            "I prefer Python for data analysis but JavaScript for frontend. "
            "Never call me before 9 AM, and always send meeting agendas in advance."
        )
        
        _, latency = measure_latency(memory_system.process_turn, complex_message)
        
        # Complex messages can take longer
        assert latency < TOTAL_TURN_LATENCY_MS * 2, \
            f"Complex extraction took {latency:.1f}ms"
    
    def test_extraction_throughput(self, memory_system):
        """Measure extraction throughput"""
        messages = [
            "I prefer Python.",
            "My name is Test.",
            "I work at TechCorp.",
            "Never call early.",
            "Always run tests.",
        ] * 4  # 20 messages
        
        start = time.perf_counter()
        for msg in messages:
            memory_system.process_turn(msg)
        elapsed = time.perf_counter() - start
        
        throughput = len(messages) / elapsed
        
        # Should process at least 5 turns per second
        assert throughput > 5, \
            f"Throughput was {throughput:.1f} turns/sec, expected > 5"


@pytest.mark.benchmark
class TestRetrievalPerformance:
    """Benchmarks for retrieval performance"""
    
    def test_retrieval_latency_empty(self, memory_system):
        """Retrieval from empty store should be fast"""
        _, latency = measure_latency(
            memory_system.get_prompt_context, "What's my name?"
        )
        
        assert latency < RETRIEVAL_LATENCY_MS, \
            f"Empty retrieval took {latency:.1f}ms, expected < {RETRIEVAL_LATENCY_MS}ms"
    
    def test_retrieval_latency_loaded(self, memory_system):
        """Retrieval with stored memories should be acceptable"""
        # Store some memories
        for i in range(20):
            memory_system.process_turn(f"I like item {i}.")
        
        # Measure retrieval
        latencies = []
        for _ in range(5):
            _, latency = measure_latency(
                memory_system.get_prompt_context, "What do I like?"
            )
            latencies.append(latency)
        
        avg_latency = statistics.mean(latencies)
        
        # Allow for some variance
        assert avg_latency < RETRIEVAL_LATENCY_MS * 2, \
            f"Avg retrieval was {avg_latency:.1f}ms"
    
    def test_semantic_search_latency(self, memory_system):
        """Semantic search should be acceptably fast"""
        # Store memories with embeddings
        memory_system.process_turn("I prefer Python for data science.")
        memory_system.process_turn("I work at TechCorp in engineering.")
        memory_system.process_turn("My manager Sarah is great.")
        
        # Semantic query
        _, latency = measure_latency(
            memory_system.get_prompt_context,
            "Tell me about my work preferences."
        )
        
        # Semantic search can be slower than keyword
        assert latency < RETRIEVAL_LATENCY_MS * 3, \
            f"Semantic search took {latency:.1f}ms"


@pytest.mark.benchmark
class TestStoragePerformance:
    """Benchmarks for storage performance"""
    
    def test_storage_latency(self, memory_system):
        """Memory storage should be fast"""
        latencies = []
        
        for i in range(5):
            start = time.perf_counter()
            memory_system.process_turn(f"I prefer tool {i}.")
            elapsed = (time.perf_counter() - start) * 1000
            latencies.append(elapsed)
        
        avg_latency = statistics.mean(latencies)
        
        assert avg_latency < STORAGE_LATENCY_MS, \
            f"Avg storage was {avg_latency:.1f}ms, expected < {STORAGE_LATENCY_MS}ms"
    
    def test_dedup_check_latency(self, memory_system):
        """Deduplication check should be fast"""
        # Store a memory
        memory_system.process_turn("I prefer Python.")
        
        # Store duplicate - should check and dedupe
        _, latency = measure_latency(
            memory_system.process_turn, "I prefer Python."
        )
        
        # Dedup should be fast
        assert latency < STORAGE_LATENCY_MS, \
            f"Dedup check took {latency:.1f}ms"


@pytest.mark.benchmark
class TestOverallPerformance:
    """Overall system performance benchmarks"""
    
    def test_turn_latency_p50(self, memory_system):
        """50th percentile turn latency"""
        messages = [
            "I prefer Python.",
            "My name is Test.",
            "Thanks",
            "What's my name?",
            "I work at TechCorp.",
        ] * 4  # 20 messages
        
        latencies = []
        for msg in messages:
            _, latency = measure_latency(memory_system.process_turn, msg)
            latencies.append(latency)
        
        p50 = statistics.median(latencies)
        
        # P50 should be good
        assert p50 < TOTAL_TURN_LATENCY_MS, \
            f"P50 latency was {p50:.1f}ms, expected < {TOTAL_TURN_LATENCY_MS}ms"
    
    def test_turn_latency_p90(self, memory_system):
        """90th percentile turn latency"""
        messages = [
            "I prefer Python.",
            "My name is Test.",
            "Thanks",
            "What's my name?",
            "I work at TechCorp.",
        ] * 4  # 20 messages
        
        latencies = []
        for msg in messages:
            _, latency = measure_latency(memory_system.process_turn, msg)
            latencies.append(latency)
        
        sorted_latencies = sorted(latencies)
        p90_index = int(0.9 * len(sorted_latencies))
        p90 = sorted_latencies[p90_index]
        
        # P90 can be higher
        assert p90 < TOTAL_TURN_LATENCY_MS * 2, \
            f"P90 latency was {p90:.1f}ms"
    
    def test_memory_system_warmup(self, memory_system):
        """Measure cold start vs warm latency"""
        # Cold start (first turn)
        _, cold_latency = measure_latency(
            memory_system.process_turn, "I prefer Python."
        )
        
        # Warm (subsequent turns)
        warm_latencies = []
        for _ in range(5):
            _, latency = measure_latency(
                memory_system.process_turn, "I like JavaScript."
            )
            warm_latencies.append(latency)
        
        avg_warm = statistics.mean(warm_latencies)
        
        # Warm should be faster than cold
        print(f"Cold: {cold_latency:.1f}ms, Warm avg: {avg_warm:.1f}ms")
        
        # No assertion - just measurement for reporting


@pytest.mark.benchmark
@pytest.mark.slow  
class TestScalabilityPerformance:
    """Scalability benchmarks"""
    
    def test_100_memories_retrieval(self, memory_system):
        """Retrieval should scale with 100 memories"""
        # Store 100 memories
        for i in range(100):
            memory_system.process_turn(f"Fact {i}: I like item_{i}.")
        
        # Measure retrieval
        latencies = []
        for _ in range(5):
            _, latency = measure_latency(
                memory_system.get_prompt_context, "What do I like?"
            )
            latencies.append(latency)
        
        avg_latency = statistics.mean(latencies)
        
        # Should still be reasonable
        assert avg_latency < RETRIEVAL_LATENCY_MS * 5, \
            f"Retrieval with 100 memories took {avg_latency:.1f}ms"
    
    def test_long_conversation_performance(self, memory_system):
        """Performance should degrade gracefully over long conversations"""
        messages = [
            "I prefer Python.",
            "My name is Test.",
            "I work at TechCorp.",
            "What's my name?",
            "Thanks!",
        ]
        
        # Track latency over time
        early_latencies = []
        late_latencies = []
        
        for i, msg in enumerate(messages * 40):  # 200 turns
            _, latency = measure_latency(memory_system.process_turn, msg)
            
            if i < 20:
                early_latencies.append(latency)
            elif i >= 180:
                late_latencies.append(latency)
        
        early_avg = statistics.mean(early_latencies)
        late_avg = statistics.mean(late_latencies)
        
        # Late should not be dramatically slower
        slowdown_ratio = late_avg / early_avg if early_avg > 0 else 1
        
        print(f"Early avg: {early_avg:.1f}ms, Late avg: {late_avg:.1f}ms, "
              f"Slowdown: {slowdown_ratio:.2f}x")
        
        # Allow 3x slowdown maximum
        assert slowdown_ratio < 3, \
            f"Late conversation {slowdown_ratio:.1f}x slower than early"
