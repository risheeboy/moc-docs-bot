"""Comprehensive benchmark suite for model evaluation."""

import json
import asyncio
from pathlib import Path
from typing import Dict, List, Any, Optional
from datetime import datetime

from app.evaluation.hindi_qa_eval import HindiQAEvaluator
from app.evaluation.hallucination_detector import HallucinationDetector
from app.evaluation.response_quality import ResponseQualityEvaluator
from app.utils.logging_config import setup_json_logging


logger = setup_json_logging("benchmark_suite")


class BenchmarkSuite:
    """Comprehensive evaluation benchmark suite."""

    def __init__(self):
        """Initialize benchmark suite."""
        self.qa_evaluator = HindiQAEvaluator()
        self.hallucination_detector = HallucinationDetector()
        self.quality_evaluator = ResponseQualityEvaluator()

    def run_complete_benchmark(
        self,
        eval_dataset_path: str,
        predictions: List[str],
        sources: Optional[List[List[str]]] = None,
    ) -> Dict[str, Any]:
        """Run complete evaluation benchmark.

        Args:
            eval_dataset_path: Path to evaluation dataset
            predictions: List of model predictions
            sources: Optional list of source documents

        Returns:
            Complete benchmark results
        """
        logger.info(
            "Starting complete benchmark suite",
            extra={"eval_size": len(predictions)},
        )

        # Load evaluation dataset
        eval_data = self._load_eval_dataset(eval_dataset_path)

        if not eval_data or len(eval_data) != len(predictions):
            logger.error(
                "Mismatch between eval data and predictions",
                extra={
                    "eval_size": len(eval_data),
                    "prediction_size": len(predictions),
                },
            )
            return {}

        # Extract references from eval data
        references = [item.get("output", "") for item in eval_data]
        questions = [item.get("input", "") for item in eval_data]

        results = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "benchmark_name": "complete_evaluation",
            "sample_count": len(predictions),
            "metrics": {},
        }

        # Run QA evaluation
        logger.info("Running QA evaluation")
        qa_metrics = self.qa_evaluator.evaluate_batch(predictions, references)
        results["metrics"]["qa_metrics"] = qa_metrics

        # Run Hindi-specific evaluation
        logger.info("Running Hindi-specific evaluation")
        hindi_metrics = self.qa_evaluator.hindi_specific_evaluation(
            predictions, references
        )
        results["metrics"]["hindi_metrics"] = hindi_metrics

        # Run hallucination detection
        if sources:
            logger.info("Running hallucination detection")
            hallucination_metrics = (
                self.hallucination_detector.evaluate_batch_hallucinations(
                    predictions, sources
                )
            )
            results["metrics"]["hallucination_metrics"] = hallucination_metrics

        # Run response quality evaluation
        logger.info("Running response quality evaluation")
        quality_metrics = asyncio.run(
            self.quality_evaluator.evaluate_batch_quality(
                questions, predictions, references
            )
        )
        results["metrics"]["quality_metrics"] = quality_metrics

        # Calculate aggregate score
        results["overall_score"] = self._calculate_overall_score(results["metrics"])

        logger.info(
            "Benchmark suite completed",
            extra={
                "overall_score": results["overall_score"],
                "sample_count": len(predictions),
            },
        )

        return results

    def run_qa_benchmark(
        self,
        predictions: List[str],
        references: List[str],
    ) -> Dict[str, float]:
        """Run QA-specific benchmark.

        Args:
            predictions: List of predictions
            references: List of references

        Returns:
            QA metrics
        """
        logger.info("Running QA benchmark")

        metrics = self.qa_evaluator.evaluate_batch(predictions, references)

        # Add percentile information
        exact_match_count = sum(
            1 for p, r in zip(predictions, references)
            if self.qa_evaluator.exact_match(p, r)
        )

        metrics["exact_match_count"] = exact_match_count
        metrics["sample_accuracy_rate"] = exact_match_count / len(predictions)

        return metrics

    def run_hallucination_benchmark(
        self,
        predictions: List[str],
        sources: List[List[str]],
    ) -> Dict[str, Any]:
        """Run hallucination detection benchmark.

        Args:
            predictions: List of predictions
            sources: List of source documents

        Returns:
            Hallucination metrics
        """
        logger.info("Running hallucination benchmark")

        results = self.hallucination_detector.evaluate_batch_hallucinations(
            predictions, sources
        )

        # Add detailed analysis
        per_sample_hallucination = []
        for pred, source_docs in zip(predictions, sources):
            sample_result = self.hallucination_detector.detect_hallucinations(
                pred, source_docs
            )
            per_sample_hallucination.append(sample_result)

        results["per_sample_results"] = per_sample_hallucination
        results["high_hallucination_samples"] = sum(
            1 for r in per_sample_hallucination
            if r["hallucination_rate"] > 0.3
        )

        return results

    async def run_quality_benchmark(
        self,
        questions: List[str],
        predictions: List[str],
        references: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """Run response quality benchmark.

        Args:
            questions: List of questions
            predictions: List of predictions
            references: Optional reference answers

        Returns:
            Quality metrics
        """
        logger.info("Running quality benchmark")

        overall_metrics = await self.quality_evaluator.evaluate_batch_quality(
            questions, predictions, references
        )

        # Add per-response analysis
        per_response_quality = []
        for q, p in zip(questions, predictions):
            length_metrics = self.quality_evaluator.evaluate_response_length(p)
            language_metrics = self.quality_evaluator.evaluate_language_quality(p)

            per_response_quality.append({
                "length": length_metrics,
                "language": language_metrics,
            })

        overall_metrics["per_response_quality"] = per_response_quality

        return overall_metrics

    def _load_eval_dataset(self, dataset_path: str) -> List[Dict[str, Any]]:
        """Load evaluation dataset from JSONL.

        Args:
            dataset_path: Path to JSONL file

        Returns:
            List of evaluation examples
        """
        data = []

        try:
            with open(dataset_path, "r", encoding="utf-8") as f:
                for line in f:
                    if line.strip():
                        data.append(json.loads(line))

            logger.info(
                "Loaded evaluation dataset",
                extra={"size": len(data), "path": dataset_path},
            )

        except Exception as e:
            logger.error(
                "Failed to load evaluation dataset",
                extra={"path": dataset_path, "error": str(e)},
                exc_info=True,
            )

        return data

    def _calculate_overall_score(self, metrics: Dict[str, Dict]) -> float:
        """Calculate overall benchmark score.

        Args:
            metrics: Dictionary of metric categories

        Returns:
            Overall score (0-1)
        """
        scores = []

        # QA metrics (40% weight)
        if "qa_metrics" in metrics:
            qa_score = (
                metrics["qa_metrics"].get("exact_match", 0) * 0.4 +
                metrics["qa_metrics"].get("f1", 0) * 0.3 +
                metrics["qa_metrics"].get("bleu", 0) * 0.3
            )
            scores.append(qa_score * 0.4)

        # Quality metrics (40% weight)
        if "quality_metrics" in metrics:
            quality_score = metrics["quality_metrics"].get("overall", 2.5) / 5.0
            scores.append(quality_score * 0.4)

        # Hallucination metrics (20% weight)
        if "hallucination_metrics" in metrics:
            hallucination_score = (
                1.0 - metrics["hallucination_metrics"].get("average_hallucination_rate", 0.5)
            )
            scores.append(hallucination_score * 0.2)

        overall = sum(scores) if scores else 0.5

        return min(1.0, max(0.0, overall))

    def generate_benchmark_report(
        self,
        results: Dict[str, Any],
        output_file: Optional[str] = None,
    ) -> str:
        """Generate human-readable benchmark report.

        Args:
            results: Benchmark results
            output_file: Optional file to save report

        Returns:
            Report text
        """
        report_lines = []

        report_lines.append("=" * 80)
        report_lines.append("MODEL EVALUATION BENCHMARK REPORT")
        report_lines.append("=" * 80)
        report_lines.append("")

        # Timestamp
        if "timestamp" in results:
            report_lines.append(f"Evaluation Timestamp: {results['timestamp']}")
        report_lines.append(f"Samples Evaluated: {results.get('sample_count', 'N/A')}")
        report_lines.append("")

        # Overall Score
        if "overall_score" in results:
            report_lines.append("OVERALL SCORE")
            report_lines.append("-" * 80)
            report_lines.append(f"Overall Score: {results['overall_score']:.2f} / 1.00")
            report_lines.append("")

        # Metrics breakdown
        if "metrics" in results:
            metrics = results["metrics"]

            # QA Metrics
            if "qa_metrics" in metrics:
                report_lines.append("QA EVALUATION METRICS")
                report_lines.append("-" * 80)
                qa_m = metrics["qa_metrics"]
                report_lines.append(f"Exact Match: {qa_m.get('exact_match', 0):.2%}")
                report_lines.append(f"F1 Score: {qa_m.get('f1', 0):.4f}")
                report_lines.append(f"BLEU Score: {qa_m.get('bleu', 0):.4f}")
                report_lines.append("")

            # Hindi Metrics
            if "hindi_metrics" in metrics:
                report_lines.append("HINDI-SPECIFIC METRICS")
                report_lines.append("-" * 80)
                hindi_m = metrics["hindi_metrics"]
                report_lines.append(f"Hindi Exact Match: {hindi_m.get('exact_match_hindi', 0):.2%}")
                report_lines.append(f"Hindi F1: {hindi_m.get('f1_hindi', 0):.4f}")
                report_lines.append(f"Devanagari Consistency: {hindi_m.get('devanagari_consistency', 0):.2%}")
                report_lines.append("")

            # Hallucination Metrics
            if "hallucination_metrics" in metrics:
                report_lines.append("HALLUCINATION DETECTION")
                report_lines.append("-" * 80)
                hal_m = metrics["hallucination_metrics"]
                report_lines.append(f"Average Hallucination Rate: {hal_m.get('average_hallucination_rate', 0):.2%}")
                report_lines.append(f"Max Hallucination Rate: {hal_m.get('max_hallucination_rate', 0):.2%}")
                report_lines.append("")

            # Quality Metrics
            if "quality_metrics" in metrics:
                report_lines.append("RESPONSE QUALITY METRICS")
                report_lines.append("-" * 80)
                qual_m = metrics["quality_metrics"]
                report_lines.append(f"Relevance: {qual_m.get('relevance', 0):.2f} / 5.0")
                report_lines.append(f"Correctness: {qual_m.get('correctness', 0):.2f} / 5.0")
                report_lines.append(f"Completeness: {qual_m.get('completeness', 0):.2f} / 5.0")
                report_lines.append(f"Clarity: {qual_m.get('clarity', 0):.2f} / 5.0")
                report_lines.append("")

        report_lines.append("=" * 80)

        report = "\n".join(report_lines)

        # Optionally save to file
        if output_file:
            with open(output_file, "w", encoding="utf-8") as f:
                f.write(report)
            logger.info("Benchmark report saved", extra={"file": output_file})

        return report
