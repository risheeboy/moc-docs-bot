"""Tests for evaluation module."""

import pytest

from app.evaluation.hindi_qa_eval import HindiQAEvaluator
from app.evaluation.hallucination_detector import HallucinationDetector
from app.evaluation.benchmark_suite import BenchmarkSuite


@pytest.fixture
def hindi_evaluator():
    """Provide HindiQAEvaluator instance."""
    return HindiQAEvaluator()


@pytest.fixture
def hallucination_detector():
    """Provide HallucinationDetector instance."""
    return HallucinationDetector()


def test_exact_match(hindi_evaluator):
    """Test exact match metric."""
    pred = "The Ministry of Culture"
    ref = "The Ministry of Culture"

    assert hindi_evaluator.exact_match(pred, ref)

    pred2 = "The Ministry"
    assert not hindi_evaluator.exact_match(pred2, ref)


def test_f1_score(hindi_evaluator):
    """Test F1 score calculation."""
    pred = "The quick brown fox jumps"
    ref = "The quick brown fox jumps"

    f1 = hindi_evaluator.f1_score(pred, ref)
    assert f1 == 1.0  # Perfect match

    pred2 = "The quick fox"
    f1_2 = hindi_evaluator.f1_score(pred2, ref)
    assert 0 < f1_2 < 1.0  # Partial match


def test_hindi_evaluation(hindi_evaluator):
    """Test Hindi-specific evaluation."""
    predictions = [
        "भारतीय संस्कृति मंत्रालय",
        "भारत की विरासत",
    ]
    references = [
        "भारतीय संस्कृति मंत्रालय",
        "भारतीय विरासत",
    ]

    metrics = hindi_evaluator.hindi_specific_evaluation(predictions, references)

    assert "exact_match_hindi" in metrics
    assert "devanagari_consistency" in metrics
    assert 0 <= metrics["devanagari_consistency"] <= 1.0


def test_hallucination_detection(hallucination_detector):
    """Test hallucination detection."""
    prediction = "The Ministry of Culture promotes Indian heritage and traditions."
    sources = [
        "The Ministry of Culture is responsible for promoting Indian heritage.",
        "It works to preserve traditions across the country.",
    ]

    result = hallucination_detector.detect_hallucinations(prediction, sources)

    assert "hallucination_rate" in result
    assert "total_facts" in result
    assert 0 <= result["hallucination_rate"] <= 1.0


def test_factual_consistency(hallucination_detector):
    """Test factual consistency check."""
    pred = "The Ministry promotes Indian heritage."
    ref = "The Ministry of Culture promotes Indian heritage."

    result = hallucination_detector.check_factual_consistency(pred, ref)

    assert "factual_consistency" in result
    assert 0 <= result["factual_consistency"] <= 1.0


def test_benchmark_suite():
    """Test benchmark suite initialization."""
    suite = BenchmarkSuite()

    assert suite.qa_evaluator is not None
    assert suite.hallucination_detector is not None
    assert suite.quality_evaluator is not None
