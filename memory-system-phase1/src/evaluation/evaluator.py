"""
Memory System Evaluator

Orchestrates evaluation of memory system against ground truth data.
"""

import logging
import time
from typing import List, Dict, Any, Optional, Set, Tuple
from dataclasses import dataclass, field

from .metrics import (
    ExtractionMetrics,
    RetrievalMetrics,
    PerformanceMetrics,
    Timer,
)

logger = logging.getLogger(__name__)


@dataclass
class GroundTruth:
    """Ground truth for a test case"""
    turn: int
    message: str
    
    # Expected extractions
    expected_memories: List[Dict[str, Any]] = field(default_factory=list)
    
    # Expected retrievals (for query messages)
    relevant_memory_ids: Set[str] = field(default_factory=set)
    
    # Metadata
    tags: List[str] = field(default_factory=list)
    
    def __post_init__(self):
        # Convert to set if list provided
        if isinstance(self.relevant_memory_ids, list):
            self.relevant_memory_ids = set(self.relevant_memory_ids)


@dataclass
class TestCase:
    """A test case with conversation and ground truth"""
    name: str
    description: str
    conversation: List[GroundTruth]
    tags: List[str] = field(default_factory=list)


@dataclass
class EvaluationResult:
    """Complete evaluation result"""
    test_name: str
    extraction_metrics: ExtractionMetrics
    retrieval_metrics: RetrievalMetrics
    performance_metrics: PerformanceMetrics
    
    # Detailed results
    extraction_details: List[Dict[str, Any]] = field(default_factory=list)
    retrieval_details: List[Dict[str, Any]] = field(default_factory=list)
    
    # Pass/fail thresholds
    passed: bool = True
    failures: List[str] = field(default_factory=list)


class MemoryEvaluator:
    """
    Evaluator for memory system quality.
    
    Compares extracted memories against ground truth to compute
    extraction precision, recall, and F1 scores. Also evaluates
    retrieval quality and performance.
    """
    
    def __init__(
        self,
        memory_system,
        extraction_threshold: float = 0.6,
        retrieval_threshold: float = 0.6,
        latency_threshold_ms: float = 100.0,
    ):
        """
        Initialize evaluator.
        
        Args:
            memory_system: The MemorySystem instance to evaluate
            extraction_threshold: Minimum F1 for extraction to pass
            retrieval_threshold: Minimum F1 for retrieval to pass
            latency_threshold_ms: Maximum avg latency to pass
        """
        self.memory_system = memory_system
        self.extraction_threshold = extraction_threshold
        self.retrieval_threshold = retrieval_threshold
        self.latency_threshold_ms = latency_threshold_ms
        
        # Track extracted memories for comparison
        self._extracted_memories: Dict[int, List[Dict]] = {}
        self._stored_memory_ids: Dict[str, str] = {}  # content hash -> memory_id
    
    def evaluate_test_case(self, test_case: TestCase) -> EvaluationResult:
        """
        Evaluate memory system against a test case.
        
        Args:
            test_case: TestCase with conversation and ground truth
            
        Returns:
            EvaluationResult with all metrics
        """
        logger.info(f"Evaluating test case: {test_case.name}")
        
        # Initialize metrics
        extraction_metrics = ExtractionMetrics()
        retrieval_metrics = RetrievalMetrics()
        performance_metrics = PerformanceMetrics()
        
        extraction_details = []
        retrieval_details = []
        
        # Clear any existing memories for clean evaluation
        self.memory_system.clear_memories()
        self._extracted_memories.clear()
        self._stored_memory_ids.clear()
        
        start_time = time.perf_counter()
        
        # Process each turn
        for gt in test_case.conversation:
            turn_result = self._evaluate_turn(
                gt,
                extraction_metrics,
                retrieval_metrics,
                performance_metrics,
            )
            
            if turn_result.get('extraction'):
                extraction_details.append(turn_result['extraction'])
            if turn_result.get('retrieval'):
                retrieval_details.append(turn_result['retrieval'])
        
        performance_metrics.total_time = time.perf_counter() - start_time
        
        # Check pass/fail
        result = EvaluationResult(
            test_name=test_case.name,
            extraction_metrics=extraction_metrics,
            retrieval_metrics=retrieval_metrics,
            performance_metrics=performance_metrics,
            extraction_details=extraction_details,
            retrieval_details=retrieval_details,
        )
        
        self._check_thresholds(result)
        
        return result
    
    def _evaluate_turn(
        self,
        gt: GroundTruth,
        extraction_metrics: ExtractionMetrics,
        retrieval_metrics: RetrievalMetrics,
        performance_metrics: PerformanceMetrics,
    ) -> Dict[str, Any]:
        """Evaluate a single turn"""
        result = {}
        
        # Time the full turn
        with Timer() as total_timer:
            # Process the turn
            context, stats = self.memory_system.process_turn(gt.message)
        
        performance_metrics.add_turn_timing(total_ms=total_timer.elapsed_ms)
        
        # Get actually extracted memories from this turn
        extracted = self._get_extracted_from_stats(stats)
        
        # Evaluate extraction
        if gt.expected_memories:
            extraction_result = self._evaluate_extraction(
                gt.turn,
                gt.message,
                extracted,
                gt.expected_memories,
                extraction_metrics,
            )
            result['extraction'] = extraction_result
        
        # Evaluate retrieval
        if gt.relevant_memory_ids:
            retrieved_ids = self._get_retrieved_ids(stats)
            retrieval_result = self._evaluate_retrieval(
                gt.turn,
                gt.message,
                retrieved_ids,
                gt.relevant_memory_ids,
                retrieval_metrics,
            )
            result['retrieval'] = retrieval_result
        
        return result
    
    def _get_extracted_from_stats(self, stats: Dict) -> List[Dict]:
        """Extract memory info from turn stats"""
        # This depends on what stats contains
        # For now, track via memory system's Redis store
        extracted = []
        
        if stats.get('extracted_count', 0) > 0:
            # Get recent memories from store
            memories = self.memory_system.redis_store.get_recent_memories(
                limit=stats['extracted_count']
            )
            for mem in memories:
                extracted.append({
                    'type': mem.get('type'),
                    'key': mem.get('key'),
                    'value': mem.get('value'),
                    'confidence': mem.get('confidence', 0.7),
                    'memory_id': mem.get('memory_id'),
                })
        
        return extracted
    
    def _get_retrieved_ids(self, stats: Dict) -> List[str]:
        """Get IDs of retrieved memories from stats"""
        # This is a simplification - ideally stats would include retrieved IDs
        return stats.get('retrieved_ids', [])
    
    def _evaluate_extraction(
        self,
        turn: int,
        message: str,
        extracted: List[Dict],
        expected: List[Dict],
        metrics: ExtractionMetrics,
    ) -> Dict[str, Any]:
        """
        Compare extracted memories against expected.
        
        Uses fuzzy matching on type + value to handle variations.
        """
        result = {
            'turn': turn,
            'message': message[:50] + '...' if len(message) > 50 else message,
            'expected_count': len(expected),
            'extracted_count': len(extracted),
            'matches': [],
            'missed': [],
            'spurious': [],
        }
        
        matched_extracted = set()
        matched_expected = set()
        
        # Match extracted to expected
        for i, exp in enumerate(expected):
            best_match = None
            best_score = 0.0
            best_idx = -1
            
            for j, ext in enumerate(extracted):
                if j in matched_extracted:
                    continue
                
                score = self._match_score(exp, ext)
                if score > best_score:
                    best_score = score
                    best_match = ext
                    best_idx = j
            
            # Consider it a match if score > 0.5
            if best_score > 0.5:
                matched_expected.add(i)
                matched_extracted.add(best_idx)
                metrics.true_positives += 1
                metrics.add_type_result(exp.get('type', 'unknown'), tp=1)
                
                # Check value accuracy
                if self._values_match(exp.get('value'), best_match.get('value')):
                    metrics.correct_values += 1
                else:
                    metrics.incorrect_values += 1
                
                # Track confidence
                metrics.confidence_sum += best_match.get('confidence', 0.7)
                metrics.confidence_count += 1
                
                result['matches'].append({
                    'expected': exp,
                    'extracted': best_match,
                    'score': best_score,
                })
            else:
                # False negative - expected but not found
                metrics.false_negatives += 1
                metrics.add_type_result(exp.get('type', 'unknown'), fn=1)
                result['missed'].append(exp)
        
        # Count false positives (extracted but not expected)
        for j, ext in enumerate(extracted):
            if j not in matched_extracted:
                metrics.false_positives += 1
                metrics.add_type_result(ext.get('type', 'unknown'), fp=1)
                result['spurious'].append(ext)
        
        return result
    
    def _match_score(self, expected: Dict, extracted: Dict) -> float:
        """
        Calculate match score between expected and extracted memory.
        
        Returns score 0.0-1.0 based on type and value similarity.
        """
        score = 0.0
        
        # Type match (40% of score)
        if expected.get('type') == extracted.get('type'):
            score += 0.4
        
        # Key match (20% of score)
        exp_key = str(expected.get('key', '')).lower()
        ext_key = str(extracted.get('key', '')).lower()
        if exp_key and ext_key:
            if exp_key == ext_key:
                score += 0.2
            elif exp_key in ext_key or ext_key in exp_key:
                score += 0.1
        
        # Value similarity (40% of score)
        exp_value = str(expected.get('value', '')).lower()
        ext_value = str(extracted.get('value', '')).lower()
        if exp_value and ext_value:
            # Simple word overlap
            exp_words = set(exp_value.split())
            ext_words = set(ext_value.split())
            if exp_words and ext_words:
                overlap = len(exp_words & ext_words)
                union = len(exp_words | ext_words)
                jaccard = overlap / union if union > 0 else 0
                score += 0.4 * jaccard
        
        return score
    
    def _values_match(self, expected: Any, extracted: Any) -> bool:
        """Check if values match (allowing for minor variations)"""
        if expected is None or extracted is None:
            return expected == extracted
        
        exp_str = str(expected).lower().strip()
        ext_str = str(extracted).lower().strip()
        
        # Exact match
        if exp_str == ext_str:
            return True
        
        # Substring match (for partial extractions)
        if exp_str in ext_str or ext_str in exp_str:
            return True
        
        return False
    
    def _evaluate_retrieval(
        self,
        turn: int,
        message: str,
        retrieved_ids: List[str],
        relevant_ids: Set[str],
        metrics: RetrievalMetrics,
    ) -> Dict[str, Any]:
        """Evaluate retrieval quality for a query"""
        result = {
            'turn': turn,
            'query': message[:50] + '...' if len(message) > 50 else message,
            'retrieved_count': len(retrieved_ids),
            'relevant_count': len(relevant_ids),
            'retrieved_ids': retrieved_ids[:5],  # First 5
            'relevant_ids': list(relevant_ids)[:5],
        }
        
        metrics.add_query_result(retrieved_ids, relevant_ids)
        
        # Calculate overlap
        retrieved_set = set(retrieved_ids)
        overlap = retrieved_set & relevant_ids
        result['overlap'] = len(overlap)
        result['precision'] = len(overlap) / len(retrieved_ids) if retrieved_ids else 0
        result['recall'] = len(overlap) / len(relevant_ids) if relevant_ids else 0
        
        return result
    
    def _check_thresholds(self, result: EvaluationResult):
        """Check if results pass thresholds"""
        result.passed = True
        result.failures = []
        
        # Extraction F1
        if result.extraction_metrics.f1 < self.extraction_threshold:
            result.passed = False
            result.failures.append(
                f"Extraction F1 {result.extraction_metrics.f1:.3f} "
                f"< threshold {self.extraction_threshold}"
            )
        
        # Retrieval F1 (if evaluated)
        if result.retrieval_metrics.queries_evaluated > 0:
            if result.retrieval_metrics.f1 < self.retrieval_threshold:
                result.passed = False
                result.failures.append(
                    f"Retrieval F1 {result.retrieval_metrics.f1:.3f} "
                    f"< threshold {self.retrieval_threshold}"
                )
        
        # Latency
        if result.performance_metrics.avg_total_latency > self.latency_threshold_ms:
            # Just a warning, don't fail
            logger.warning(
                f"Avg latency {result.performance_metrics.avg_total_latency:.1f}ms "
                f"> threshold {self.latency_threshold_ms}ms"
            )
    
    def evaluate_batch(self, test_cases: List[TestCase]) -> List[EvaluationResult]:
        """Evaluate multiple test cases"""
        results = []
        for test_case in test_cases:
            result = self.evaluate_test_case(test_case)
            results.append(result)
            logger.info(
                f"Test '{test_case.name}': "
                f"Extraction F1={result.extraction_metrics.f1:.3f}, "
                f"{'PASSED' if result.passed else 'FAILED'}"
            )
        return results
