"""
Evaluation Metrics for Memory System

Provides metrics for measuring:
- Extraction quality (precision, recall, F1)
- Retrieval quality (relevance, ranking)
- Performance (latency, throughput)
"""

from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional, Set
import time


def calculate_precision(true_positives: int, false_positives: int) -> float:
    """Calculate precision: TP / (TP + FP)"""
    total = true_positives + false_positives
    return true_positives / total if total > 0 else 0.0


def calculate_recall(true_positives: int, false_negatives: int) -> float:
    """Calculate recall: TP / (TP + FN)"""
    total = true_positives + false_negatives
    return true_positives / total if total > 0 else 0.0


def calculate_f1(precision: float, recall: float) -> float:
    """Calculate F1 score: 2 * (precision * recall) / (precision + recall)"""
    total = precision + recall
    return 2 * (precision * recall) / total if total > 0 else 0.0


@dataclass
class ExtractionMetrics:
    """Metrics for memory extraction quality"""
    
    # Counts
    true_positives: int = 0      # Correctly extracted memories
    false_positives: int = 0     # Incorrectly extracted (shouldn't exist)
    false_negatives: int = 0     # Missed memories (should exist)
    
    # Breakdowns by type
    by_type: Dict[str, Dict[str, int]] = field(default_factory=dict)
    
    # Content accuracy
    correct_values: int = 0      # Memories with correct value
    incorrect_values: int = 0    # Memories with wrong value
    
    # Confidence calibration
    confidence_sum: float = 0.0
    confidence_count: int = 0
    
    @property
    def precision(self) -> float:
        """Extraction precision"""
        return calculate_precision(self.true_positives, self.false_positives)
    
    @property
    def recall(self) -> float:
        """Extraction recall"""
        return calculate_recall(self.true_positives, self.false_negatives)
    
    @property
    def f1(self) -> float:
        """Extraction F1 score"""
        return calculate_f1(self.precision, self.recall)
    
    @property
    def value_accuracy(self) -> float:
        """Accuracy of extracted values"""
        total = self.correct_values + self.incorrect_values
        return self.correct_values / total if total > 0 else 0.0
    
    @property
    def average_confidence(self) -> float:
        """Average confidence of extractions"""
        return self.confidence_sum / self.confidence_count if self.confidence_count > 0 else 0.0
    
    def add_type_result(self, memory_type: str, tp: int = 0, fp: int = 0, fn: int = 0):
        """Add results for a specific memory type"""
        if memory_type not in self.by_type:
            self.by_type[memory_type] = {'tp': 0, 'fp': 0, 'fn': 0}
        self.by_type[memory_type]['tp'] += tp
        self.by_type[memory_type]['fp'] += fp
        self.by_type[memory_type]['fn'] += fn
    
    def get_type_f1(self, memory_type: str) -> float:
        """Get F1 score for a specific type"""
        if memory_type not in self.by_type:
            return 0.0
        data = self.by_type[memory_type]
        precision = calculate_precision(data['tp'], data['fp'])
        recall = calculate_recall(data['tp'], data['fn'])
        return calculate_f1(precision, recall)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for reporting"""
        return {
            'precision': round(self.precision, 4),
            'recall': round(self.recall, 4),
            'f1': round(self.f1, 4),
            'true_positives': self.true_positives,
            'false_positives': self.false_positives,
            'false_negatives': self.false_negatives,
            'value_accuracy': round(self.value_accuracy, 4),
            'average_confidence': round(self.average_confidence, 4),
            'by_type': {
                t: {
                    'tp': d['tp'],
                    'fp': d['fp'],
                    'fn': d['fn'],
                    'f1': round(calculate_f1(
                        calculate_precision(d['tp'], d['fp']),
                        calculate_recall(d['tp'], d['fn'])
                    ), 4)
                }
                for t, d in self.by_type.items()
            }
        }


@dataclass
class RetrievalMetrics:
    """Metrics for memory retrieval quality"""
    
    # Relevance metrics
    queries_evaluated: int = 0
    relevant_retrieved: int = 0     # Retrieved memories that were relevant
    irrelevant_retrieved: int = 0   # Retrieved memories that weren't relevant
    relevant_missed: int = 0        # Relevant memories not retrieved
    
    # Ranking metrics
    mean_reciprocal_rank: float = 0.0
    mrr_count: int = 0
    
    # Position metrics (avg position of relevant results)
    avg_relevant_position: float = 0.0
    position_count: int = 0
    
    # Top-K metrics
    precision_at_k: Dict[int, float] = field(default_factory=dict)
    recall_at_k: Dict[int, float] = field(default_factory=dict)
    
    @property
    def precision(self) -> float:
        """Retrieval precision"""
        return calculate_precision(self.relevant_retrieved, self.irrelevant_retrieved)
    
    @property
    def recall(self) -> float:
        """Retrieval recall"""
        return calculate_recall(self.relevant_retrieved, self.relevant_missed)
    
    @property
    def f1(self) -> float:
        """Retrieval F1 score"""
        return calculate_f1(self.precision, self.recall)
    
    @property
    def mrr(self) -> float:
        """Mean Reciprocal Rank"""
        return self.mean_reciprocal_rank / self.mrr_count if self.mrr_count > 0 else 0.0
    
    def add_query_result(
        self,
        retrieved_ids: List[str],
        relevant_ids: Set[str],
        k_values: List[int] = None
    ):
        """Add results for a single query"""
        k_values = k_values or [1, 3, 5, 10]
        self.queries_evaluated += 1
        
        retrieved_set = set(retrieved_ids)
        
        # Count relevant/irrelevant
        relevant_found = retrieved_set & relevant_ids
        self.relevant_retrieved += len(relevant_found)
        self.irrelevant_retrieved += len(retrieved_set - relevant_ids)
        self.relevant_missed += len(relevant_ids - retrieved_set)
        
        # MRR: position of first relevant result
        for i, mem_id in enumerate(retrieved_ids):
            if mem_id in relevant_ids:
                self.mean_reciprocal_rank += 1.0 / (i + 1)
                self.mrr_count += 1
                break
        
        # Average position of relevant results
        for i, mem_id in enumerate(retrieved_ids):
            if mem_id in relevant_ids:
                self.avg_relevant_position += i + 1
                self.position_count += 1
        
        # Precision@K and Recall@K
        for k in k_values:
            top_k = set(retrieved_ids[:k])
            relevant_in_k = len(top_k & relevant_ids)
            
            precision_k = relevant_in_k / k if k > 0 else 0.0
            recall_k = relevant_in_k / len(relevant_ids) if relevant_ids else 0.0
            
            if k not in self.precision_at_k:
                self.precision_at_k[k] = 0.0
                self.recall_at_k[k] = 0.0
            
            # Running average
            n = self.queries_evaluated
            self.precision_at_k[k] = (
                (self.precision_at_k[k] * (n - 1) + precision_k) / n
            )
            self.recall_at_k[k] = (
                (self.recall_at_k[k] * (n - 1) + recall_k) / n
            )
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for reporting"""
        return {
            'precision': round(self.precision, 4),
            'recall': round(self.recall, 4),
            'f1': round(self.f1, 4),
            'mrr': round(self.mrr, 4),
            'queries_evaluated': self.queries_evaluated,
            'relevant_retrieved': self.relevant_retrieved,
            'irrelevant_retrieved': self.irrelevant_retrieved,
            'relevant_missed': self.relevant_missed,
            'avg_relevant_position': round(
                self.avg_relevant_position / self.position_count 
                if self.position_count > 0 else 0.0, 2
            ),
            'precision_at_k': {k: round(v, 4) for k, v in sorted(self.precision_at_k.items())},
            'recall_at_k': {k: round(v, 4) for k, v in sorted(self.recall_at_k.items())},
        }


@dataclass 
class PerformanceMetrics:
    """Performance benchmarking metrics"""
    
    # Latency tracking
    extraction_latencies: List[float] = field(default_factory=list)
    storage_latencies: List[float] = field(default_factory=list)
    retrieval_latencies: List[float] = field(default_factory=list)
    total_latencies: List[float] = field(default_factory=list)
    
    # Throughput
    turns_processed: int = 0
    total_time: float = 0.0
    
    # Memory usage
    peak_memory_mb: float = 0.0
    avg_memory_mb: float = 0.0
    memory_samples: int = 0
    
    @property
    def avg_extraction_latency(self) -> float:
        """Average extraction latency in ms"""
        return sum(self.extraction_latencies) / len(self.extraction_latencies) if self.extraction_latencies else 0.0
    
    @property
    def avg_storage_latency(self) -> float:
        """Average storage latency in ms"""
        return sum(self.storage_latencies) / len(self.storage_latencies) if self.storage_latencies else 0.0
    
    @property
    def avg_retrieval_latency(self) -> float:
        """Average retrieval latency in ms"""
        return sum(self.retrieval_latencies) / len(self.retrieval_latencies) if self.retrieval_latencies else 0.0
    
    @property
    def avg_total_latency(self) -> float:
        """Average total turn latency in ms"""
        return sum(self.total_latencies) / len(self.total_latencies) if self.total_latencies else 0.0
    
    @property
    def p50_latency(self) -> float:
        """50th percentile latency"""
        return self._percentile(self.total_latencies, 50)
    
    @property
    def p90_latency(self) -> float:
        """90th percentile latency"""
        return self._percentile(self.total_latencies, 90)
    
    @property
    def p99_latency(self) -> float:
        """99th percentile latency"""
        return self._percentile(self.total_latencies, 99)
    
    @property
    def throughput(self) -> float:
        """Turns per second"""
        return self.turns_processed / self.total_time if self.total_time > 0 else 0.0
    
    def _percentile(self, data: List[float], percentile: int) -> float:
        """Calculate percentile"""
        if not data:
            return 0.0
        sorted_data = sorted(data)
        k = (len(sorted_data) - 1) * percentile / 100
        f = int(k)
        c = f + 1
        if c >= len(sorted_data):
            return sorted_data[-1]
        return sorted_data[f] * (c - k) + sorted_data[c] * (k - f)
    
    def add_turn_timing(
        self,
        extraction_ms: float = 0.0,
        storage_ms: float = 0.0,
        retrieval_ms: float = 0.0,
        total_ms: float = 0.0
    ):
        """Add timing for a single turn"""
        if extraction_ms > 0:
            self.extraction_latencies.append(extraction_ms)
        if storage_ms > 0:
            self.storage_latencies.append(storage_ms)
        if retrieval_ms > 0:
            self.retrieval_latencies.append(retrieval_ms)
        if total_ms > 0:
            self.total_latencies.append(total_ms)
        self.turns_processed += 1
    
    def add_memory_sample(self, memory_mb: float):
        """Add a memory usage sample"""
        self.peak_memory_mb = max(self.peak_memory_mb, memory_mb)
        self.avg_memory_mb = (
            (self.avg_memory_mb * self.memory_samples + memory_mb) / 
            (self.memory_samples + 1)
        )
        self.memory_samples += 1
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for reporting"""
        return {
            'turns_processed': self.turns_processed,
            'latency': {
                'extraction_avg_ms': round(self.avg_extraction_latency, 2),
                'storage_avg_ms': round(self.avg_storage_latency, 2),
                'retrieval_avg_ms': round(self.avg_retrieval_latency, 2),
                'total_avg_ms': round(self.avg_total_latency, 2),
                'p50_ms': round(self.p50_latency, 2),
                'p90_ms': round(self.p90_latency, 2),
                'p99_ms': round(self.p99_latency, 2),
            },
            'throughput': {
                'turns_per_second': round(self.throughput, 2),
                'total_time_seconds': round(self.total_time, 2),
            },
            'memory': {
                'peak_mb': round(self.peak_memory_mb, 2),
                'avg_mb': round(self.avg_memory_mb, 2),
            }
        }


class Timer:
    """Context manager for timing code blocks"""
    
    def __init__(self):
        self.start_time = 0.0
        self.elapsed_ms = 0.0
    
    def __enter__(self):
        self.start_time = time.perf_counter()
        return self
    
    def __exit__(self, *args):
        self.elapsed_ms = (time.perf_counter() - self.start_time) * 1000
