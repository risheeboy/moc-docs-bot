"""Detect data drift to trigger retraining."""

import json
from pathlib import Path
from typing import Dict, List, Any, Tuple
from collections import Counter
from datetime import datetime, timedelta

from app.utils.logging_config import setup_json_logging


logger = setup_json_logging("data_drift_detector")


class DataDriftDetector:
    """Detect data drift in Ministry of Culture content."""

    def __init__(self):
        """Initialize drift detector."""
        pass

    def compute_baseline_statistics(
        self,
        documents: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        """Compute baseline statistics from initial documents.

        Args:
            documents: List of documents

        Returns:
            Baseline statistics
        """
        if not documents:
            return {}

        # Extract features
        languages = [d.get("language", "en") for d in documents]
        content_lengths = [len(d.get("content", "").split()) for d in documents]
        source_sites = [d.get("source_site", "") for d in documents]

        baseline = {
            "document_count": len(documents),
            "language_distribution": dict(Counter(languages)),
            "avg_content_length": sum(content_lengths) / len(content_lengths) if content_lengths else 0,
            "min_content_length": min(content_lengths) if content_lengths else 0,
            "max_content_length": max(content_lengths) if content_lengths else 0,
            "unique_source_sites": len(set(source_sites)),
            "source_site_distribution": dict(Counter(source_sites)),
            "timestamp": datetime.utcnow().isoformat() + "Z",
        }

        logger.info(
            "Computed baseline statistics",
            extra={
                "document_count": baseline["document_count"],
                "avg_length": baseline["avg_content_length"],
            },
        )

        return baseline

    def detect_drift(
        self,
        current_documents: List[Dict[str, Any]],
        baseline_stats: Dict[str, Any],
        drift_threshold: float = 0.2,
    ) -> Dict[str, Any]:
        """Detect data drift compared to baseline.

        Args:
            current_documents: Current documents
            baseline_stats: Baseline statistics
            drift_threshold: Threshold for drift detection (0-1)

        Returns:
            Drift detection results
        """
        if not baseline_stats or not current_documents:
            return {
                "drift_detected": False,
                "drift_score": 0.0,
                "drift_indicators": {},
            }

        # Compute current statistics
        languages = [d.get("language", "en") for d in current_documents]
        content_lengths = [len(d.get("content", "").split()) for d in current_documents]
        source_sites = [d.get("source_site", "") for d in current_documents]

        current_stats = {
            "document_count": len(current_documents),
            "language_distribution": dict(Counter(languages)),
            "avg_content_length": sum(content_lengths) / len(content_lengths) if content_lengths else 0,
            "unique_source_sites": len(set(source_sites)),
            "source_site_distribution": dict(Counter(source_sites)),
        }

        # Compare statistics
        drift_indicators = {}

        # Check document count drift
        baseline_count = baseline_stats.get("document_count", 1)
        count_drift = abs(
            current_stats["document_count"] - baseline_count
        ) / baseline_count
        drift_indicators["document_count_drift"] = count_drift

        # Check content length drift
        baseline_avg_length = baseline_stats.get("avg_content_length", 1)
        length_drift = abs(
            current_stats["avg_content_length"] - baseline_avg_length
        ) / baseline_avg_length
        drift_indicators["content_length_drift"] = length_drift

        # Check language distribution drift
        baseline_lang = baseline_stats.get("language_distribution", {})
        current_lang = current_stats["language_distribution"]
        lang_drift = self._compute_distribution_drift(baseline_lang, current_lang)
        drift_indicators["language_distribution_drift"] = lang_drift

        # Check source site drift
        baseline_sources = baseline_stats.get("source_site_distribution", {})
        current_sources = current_stats["source_site_distribution"]
        source_drift = self._compute_distribution_drift(baseline_sources, current_sources)
        drift_indicators["source_site_distribution_drift"] = source_drift

        # Detect new domains/sites
        baseline_site_set = set(baseline_stats.get("source_site_distribution", {}).keys())
        current_site_set = set(current_stats["source_site_distribution"].keys())
        new_sites = current_site_set - baseline_site_set
        drift_indicators["new_source_sites"] = list(new_sites)

        # Calculate overall drift score
        drift_scores = [
            count_drift,
            length_drift,
            lang_drift,
            source_drift,
        ]
        overall_drift_score = sum(drift_scores) / len(drift_scores)

        drift_detected = overall_drift_score > drift_threshold

        logger.info(
            "Data drift detection completed",
            extra={
                "drift_detected": drift_detected,
                "drift_score": overall_drift_score,
                "indicators": drift_indicators,
            },
        )

        return {
            "drift_detected": drift_detected,
            "drift_score": overall_drift_score,
            "drift_threshold": drift_threshold,
            "drift_indicators": drift_indicators,
            "new_sites": list(new_sites),
            "timestamp": datetime.utcnow().isoformat() + "Z",
        }

    def _compute_distribution_drift(
        self,
        baseline_dist: Dict[str, int],
        current_dist: Dict[str, int],
    ) -> float:
        """Compute drift between two distributions using KL divergence approximation.

        Args:
            baseline_dist: Baseline distribution
            current_dist: Current distribution

        Returns:
            Drift score (0-1)
        """
        if not baseline_dist or not current_dist:
            return 0.0

        # Normalize distributions
        baseline_total = sum(baseline_dist.values()) or 1
        current_total = sum(current_dist.values()) or 1

        baseline_normalized = {k: v / baseline_total for k, v in baseline_dist.items()}
        current_normalized = {k: v / current_total for k, v in current_dist.items()}

        # Calculate KL divergence approximation
        all_keys = set(baseline_normalized.keys()) | set(current_normalized.keys())
        drift = 0.0

        for key in all_keys:
            baseline_p = baseline_normalized.get(key, 1e-10)
            current_p = current_normalized.get(key, 1e-10)

            # Simple L1 distance as approximation
            drift += abs(baseline_p - current_p) / 2

        return min(1.0, drift)

    def detect_content_divergence(
        self,
        new_documents: List[Dict[str, Any]],
        training_documents: List[Dict[str, Any]],
        similarity_threshold: float = 0.7,
    ) -> Dict[str, Any]:
        """Detect divergence between new content and training data.

        Args:
            new_documents: New documents
            training_documents: Training documents
            similarity_threshold: Similarity threshold

        Returns:
            Divergence detection results
        """
        if not new_documents or not training_documents:
            return {
                "divergence_detected": False,
                "divergence_score": 0.0,
            }

        # Extract keywords from documents
        training_keywords = self._extract_keywords(training_documents)
        new_keywords = self._extract_keywords(new_documents)

        # Calculate overlap
        keyword_overlap = len(
            set(training_keywords) & set(new_keywords)
        ) / max(len(set(training_keywords)), len(set(new_keywords)), 1)

        divergence_score = 1.0 - keyword_overlap
        divergence_detected = keyword_overlap < similarity_threshold

        logger.info(
            "Content divergence detection completed",
            extra={
                "divergence_detected": divergence_detected,
                "keyword_overlap": keyword_overlap,
                "divergence_score": divergence_score,
            },
        )

        return {
            "divergence_detected": divergence_detected,
            "divergence_score": divergence_score,
            "keyword_overlap": keyword_overlap,
            "similarity_threshold": similarity_threshold,
            "new_keywords_count": len(set(new_keywords)),
            "training_keywords_count": len(set(training_keywords)),
        }

    def _extract_keywords(self, documents: List[Dict[str, Any]]) -> List[str]:
        """Extract keywords from documents.

        Args:
            documents: Documents

        Returns:
            List of keywords
        """
        keywords = []

        for doc in documents:
            content = doc.get("content", "")
            title = doc.get("title", "")

            # Extract words longer than 5 characters (likely meaningful)
            words = (content + " " + title).split()
            for word in words:
                if len(word) > 5:
                    keywords.append(word.lower())

        return keywords

    def should_trigger_retraining(
        self,
        current_drift_score: float,
        new_document_count: int,
        drift_threshold: float = 0.25,
        new_document_threshold: int = 100,
    ) -> Tuple[bool, str]:
        """Determine if retraining should be triggered.

        Args:
            current_drift_score: Current drift score
            new_document_count: Number of new documents
            drift_threshold: Drift threshold
            new_document_threshold: New document threshold

        Returns:
            Tuple of (should_retrain, reason)
        """
        reasons = []

        # Check drift
        if current_drift_score > drift_threshold:
            reasons.append(f"Data drift detected (score: {current_drift_score:.2f})")

        # Check new document volume
        if new_document_count > new_document_threshold:
            reasons.append(f"New document volume threshold exceeded ({new_document_count} docs)")

        should_retrain = len(reasons) > 0

        logger.info(
            "Retraining trigger evaluation",
            extra={
                "should_retrain": should_retrain,
                "drift_score": current_drift_score,
                "new_documents": new_document_count,
                "reasons": reasons,
            },
        )

        reason = " | ".join(reasons) if reasons else "No retraining needed"

        return should_retrain, reason
