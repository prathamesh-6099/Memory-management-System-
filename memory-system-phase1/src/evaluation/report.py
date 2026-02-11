"""
Evaluation Report Generator

Generates formatted reports from evaluation results.
"""

import json
from datetime import datetime
from typing import List, Dict, Any, Optional
from dataclasses import asdict

from .evaluator import EvaluationResult


class EvaluationReport:
    """
    Generate formatted reports from evaluation results.
    
    Supports multiple output formats:
    - Console (colored terminal output)
    - JSON (machine-readable)
    - Markdown (documentation)
    """
    
    def __init__(self, results: List[EvaluationResult]):
        """
        Initialize report generator.
        
        Args:
            results: List of evaluation results to report on
        """
        self.results = results
        self.generated_at = datetime.now().isoformat()
    
    def to_console(self) -> str:
        """Generate console-formatted report"""
        lines = []
        lines.append("=" * 70)
        lines.append(" MEMORY SYSTEM EVALUATION REPORT")
        lines.append("=" * 70)
        lines.append(f"Generated: {self.generated_at}")
        lines.append(f"Test Cases: {len(self.results)}")
        lines.append("")
        
        # Summary
        passed = sum(1 for r in self.results if r.passed)
        failed = len(self.results) - passed
        lines.append("SUMMARY")
        lines.append("-" * 40)
        lines.append(f"  Passed: {passed}")
        lines.append(f"  Failed: {failed}")
        lines.append(f"  Pass Rate: {passed/len(self.results)*100:.1f}%" if self.results else "  Pass Rate: N/A")
        lines.append("")
        
        # Aggregate metrics
        if self.results:
            avg_extraction_f1 = sum(r.extraction_metrics.f1 for r in self.results) / len(self.results)
            avg_retrieval_f1 = sum(
                r.retrieval_metrics.f1 for r in self.results 
                if r.retrieval_metrics.queries_evaluated > 0
            ) / max(1, sum(1 for r in self.results if r.retrieval_metrics.queries_evaluated > 0))
            
            lines.append("AGGREGATE METRICS")
            lines.append("-" * 40)
            lines.append(f"  Avg Extraction F1: {avg_extraction_f1:.3f}")
            lines.append(f"  Avg Retrieval F1: {avg_retrieval_f1:.3f}")
            lines.append("")
        
        # Individual test results
        lines.append("INDIVIDUAL RESULTS")
        lines.append("-" * 40)
        
        for result in self.results:
            status = "✓ PASS" if result.passed else "✗ FAIL"
            lines.append(f"\n{result.test_name}: {status}")
            lines.append(f"  Extraction: P={result.extraction_metrics.precision:.3f}, "
                        f"R={result.extraction_metrics.recall:.3f}, "
                        f"F1={result.extraction_metrics.f1:.3f}")
            
            if result.retrieval_metrics.queries_evaluated > 0:
                lines.append(f"  Retrieval:  P={result.retrieval_metrics.precision:.3f}, "
                            f"R={result.retrieval_metrics.recall:.3f}, "
                            f"F1={result.retrieval_metrics.f1:.3f}")
                lines.append(f"  MRR: {result.retrieval_metrics.mrr:.3f}")
            
            lines.append(f"  Latency: avg={result.performance_metrics.avg_total_latency:.1f}ms, "
                        f"p90={result.performance_metrics.p90_latency:.1f}ms")
            
            if result.failures:
                for failure in result.failures:
                    lines.append(f"  ! {failure}")
        
        lines.append("")
        lines.append("=" * 70)
        
        return "\n".join(lines)
    
    def to_json(self, indent: int = 2) -> str:
        """Generate JSON report"""
        report = {
            'generated_at': self.generated_at,
            'summary': {
                'total_tests': len(self.results),
                'passed': sum(1 for r in self.results if r.passed),
                'failed': sum(1 for r in self.results if not r.passed),
            },
            'results': []
        }
        
        for result in self.results:
            result_dict = {
                'test_name': result.test_name,
                'passed': result.passed,
                'failures': result.failures,
                'extraction': result.extraction_metrics.to_dict(),
                'retrieval': result.retrieval_metrics.to_dict(),
                'performance': result.performance_metrics.to_dict(),
            }
            report['results'].append(result_dict)
        
        return json.dumps(report, indent=indent)
    
    def to_markdown(self) -> str:
        """Generate Markdown report"""
        lines = []
        lines.append("# Memory System Evaluation Report")
        lines.append("")
        lines.append(f"Generated: {self.generated_at}")
        lines.append("")
        
        # Summary
        passed = sum(1 for r in self.results if r.passed)
        failed = len(self.results) - passed
        lines.append("## Summary")
        lines.append("")
        lines.append(f"| Metric | Value |")
        lines.append(f"|--------|-------|")
        lines.append(f"| Total Tests | {len(self.results)} |")
        lines.append(f"| Passed | {passed} |")
        lines.append(f"| Failed | {failed} |")
        lines.append(f"| Pass Rate | {passed/len(self.results)*100:.1f}% |" if self.results else "| Pass Rate | N/A |")
        lines.append("")
        
        # Results table
        lines.append("## Results by Test")
        lines.append("")
        lines.append("| Test | Status | Extraction F1 | Retrieval F1 | Avg Latency |")
        lines.append("|------|--------|---------------|--------------|-------------|")
        
        for result in self.results:
            status = "✅ Pass" if result.passed else "❌ Fail"
            retrieval_f1 = f"{result.retrieval_metrics.f1:.3f}" if result.retrieval_metrics.queries_evaluated > 0 else "N/A"
            lines.append(
                f"| {result.test_name} | {status} | "
                f"{result.extraction_metrics.f1:.3f} | {retrieval_f1} | "
                f"{result.performance_metrics.avg_total_latency:.1f}ms |"
            )
        lines.append("")
        
        # Detailed results
        lines.append("## Detailed Results")
        lines.append("")
        
        for result in self.results:
            lines.append(f"### {result.test_name}")
            lines.append("")
            
            if not result.passed:
                lines.append("**Failures:**")
                for failure in result.failures:
                    lines.append(f"- {failure}")
                lines.append("")
            
            lines.append("**Extraction Metrics:**")
            lines.append("")
            em = result.extraction_metrics
            lines.append(f"- Precision: {em.precision:.3f}")
            lines.append(f"- Recall: {em.recall:.3f}")
            lines.append(f"- F1 Score: {em.f1:.3f}")
            lines.append(f"- True Positives: {em.true_positives}")
            lines.append(f"- False Positives: {em.false_positives}")
            lines.append(f"- False Negatives: {em.false_negatives}")
            lines.append("")
            
            if result.retrieval_metrics.queries_evaluated > 0:
                lines.append("**Retrieval Metrics:**")
                lines.append("")
                rm = result.retrieval_metrics
                lines.append(f"- Precision: {rm.precision:.3f}")
                lines.append(f"- Recall: {rm.recall:.3f}")
                lines.append(f"- F1 Score: {rm.f1:.3f}")
                lines.append(f"- MRR: {rm.mrr:.3f}")
                lines.append(f"- Queries Evaluated: {rm.queries_evaluated}")
                lines.append("")
            
            lines.append("**Performance:**")
            lines.append("")
            pm = result.performance_metrics
            lines.append(f"- Turns Processed: {pm.turns_processed}")
            lines.append(f"- Avg Latency: {pm.avg_total_latency:.1f}ms")
            lines.append(f"- P90 Latency: {pm.p90_latency:.1f}ms")
            lines.append(f"- Throughput: {pm.throughput:.2f} turns/sec")
            lines.append("")
        
        return "\n".join(lines)
    
    def save(self, filepath: str, format: str = 'json'):
        """
        Save report to file.
        
        Args:
            filepath: Output file path
            format: 'json', 'markdown', or 'text'
        """
        if format == 'json':
            content = self.to_json()
        elif format == 'markdown':
            content = self.to_markdown()
        else:
            content = self.to_console()
        
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
    
    def print_summary(self):
        """Print summary to console"""
        print(self.to_console())
