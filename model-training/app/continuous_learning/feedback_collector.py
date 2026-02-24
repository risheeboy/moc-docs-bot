"""Collect user feedback for continuous learning."""

import json
from pathlib import Path
from typing import Dict, List, Any, Optional
from datetime import datetime

from app.utils.logging_config import setup_json_logging


logger = setup_json_logging("feedback_collector")


class FeedbackCollector:
    """Collect and process user feedback for retraining."""

    def __init__(self, feedback_dir: str = "/app/data/feedback"):
        """Initialize feedback collector.

        Args:
            feedback_dir: Directory to store feedback
        """
        self.feedback_dir = Path(feedback_dir)
        self.feedback_dir.mkdir(parents=True, exist_ok=True)

    def collect_feedback(
        self,
        user_query: str,
        model_response: str,
        rating: int,
        feedback_type: str = "general",
        corrected_response: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Collect user feedback.

        Args:
            user_query: User's input query
            model_response: Model's response
            rating: User rating (1-5)
            feedback_type: Type of feedback (general, correction, insufficient)
            corrected_response: Corrected response (if applicable)
            metadata: Additional metadata

        Returns:
            Feedback record
        """
        feedback = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "user_query": user_query,
            "model_response": model_response,
            "rating": rating,
            "feedback_type": feedback_type,
            "corrected_response": corrected_response,
            "metadata": metadata or {},
        }

        # Save feedback
        feedback_file = self.feedback_dir / f"feedback_{datetime.utcnow().timestamp()}.json"

        with open(feedback_file, "w", encoding="utf-8") as f:
            json.dump(feedback, f, ensure_ascii=False, indent=2)

        logger.info(
            "Feedback collected",
            extra={
                "rating": rating,
                "feedback_type": feedback_type,
                "file": str(feedback_file),
            },
        )

        return feedback

    def collect_batch_feedback(
        self,
        feedback_records: List[Dict[str, Any]],
    ) -> int:
        """Collect batch feedback.

        Args:
            feedback_records: List of feedback records

        Returns:
            Number of feedback records saved
        """
        saved_count = 0

        for record in feedback_records:
            try:
                feedback_file = self.feedback_dir / f"feedback_{datetime.utcnow().timestamp()}.json"

                with open(feedback_file, "w", encoding="utf-8") as f:
                    json.dump(record, f, ensure_ascii=False, indent=2)

                saved_count += 1
            except Exception as e:
                logger.warning(
                    "Failed to save feedback record",
                    extra={"error": str(e)},
                )

        logger.info(
            "Batch feedback collected",
            extra={"total": len(feedback_records), "saved": saved_count},
        )

        return saved_count

    def aggregate_feedback(self, min_rating: int = 3) -> Dict[str, Any]:
        """Aggregate feedback data.

        Args:
            min_rating: Minimum rating to consider as positive feedback

        Returns:
            Aggregated feedback statistics
        """
        all_feedback = []

        for feedback_file in self.feedback_dir.glob("feedback_*.json"):
            try:
                with open(feedback_file, "r", encoding="utf-8") as f:
                    feedback = json.load(f)
                    all_feedback.append(feedback)
            except Exception as e:
                logger.warning(
                    "Failed to read feedback file",
                    extra={"file": str(feedback_file), "error": str(e)},
                )

        # Aggregate statistics
        if not all_feedback:
            return {
                "total_feedback": 0,
                "average_rating": 0.0,
                "positive_feedback": 0,
                "negative_feedback": 0,
            }

        ratings = [f["rating"] for f in all_feedback if "rating" in f]
        feedback_types = [f["feedback_type"] for f in all_feedback if "feedback_type" in f]

        aggregate = {
            "total_feedback": len(all_feedback),
            "average_rating": sum(ratings) / len(ratings) if ratings else 0.0,
            "positive_feedback": sum(1 for r in ratings if r >= min_rating),
            "negative_feedback": sum(1 for r in ratings if r < min_rating),
            "feedback_type_distribution": self._count_occurrences(feedback_types),
            "negative_samples": self._collect_negative_samples(all_feedback),
        }

        logger.info(
            "Feedback aggregated",
            extra={
                "total": aggregate["total_feedback"],
                "avg_rating": aggregate["average_rating"],
                "positive": aggregate["positive_feedback"],
            },
        )

        return aggregate

    def _count_occurrences(self, items: List[str]) -> Dict[str, int]:
        """Count occurrences of items.

        Args:
            items: List of items

        Returns:
            Dictionary of counts
        """
        counts = {}
        for item in items:
            counts[item] = counts.get(item, 0) + 1
        return counts

    def _collect_negative_samples(
        self,
        feedback: List[Dict[str, Any]],
        threshold: int = 2,
    ) -> List[Dict[str, str]]:
        """Collect negative feedback samples for retraining.

        Args:
            feedback: All feedback records
            threshold: Rating threshold for negative samples

        Returns:
            List of negative samples (query + correction)
        """
        negative_samples = []

        for record in feedback:
            if (
                record.get("rating", 5) <= threshold
                and record.get("corrected_response")
            ):
                sample = {
                    "query": record.get("user_query", ""),
                    "correction": record.get("corrected_response", ""),
                    "original_response": record.get("model_response", ""),
                    "reason": record.get("feedback_type", "general"),
                }
                negative_samples.append(sample)

        logger.info(
            "Collected negative samples",
            extra={"count": len(negative_samples)},
        )

        return negative_samples

    def generate_retraining_dataset(
        self,
        min_rating: int = 3,
        output_file: str = "/app/data/feedback_based_retraining.jsonl",
    ) -> str:
        """Generate retraining dataset from negative feedback.

        Args:
            min_rating: Minimum rating for inclusion
            output_file: Output file path

        Returns:
            Path to generated dataset
        """
        all_feedback = []

        for feedback_file in self.feedback_dir.glob("feedback_*.json"):
            try:
                with open(feedback_file, "r", encoding="utf-8") as f:
                    feedback = json.load(f)
                    all_feedback.append(feedback)
            except Exception as e:
                logger.warning(
                    "Failed to read feedback file",
                    extra={"file": str(feedback_file), "error": str(e)},
                )

        # Create retraining examples from negative feedback
        retraining_examples = []

        for feedback in all_feedback:
            if feedback.get("rating", 5) < min_rating:
                # Use corrected response if available, otherwise skip
                if feedback.get("corrected_response"):
                    example = {
                        "instruction": "Correct the following response based on user feedback.",
                        "input": f"Query: {feedback.get('user_query', '')}\nIncorrect Response: {feedback.get('model_response', '')}",
                        "output": feedback.get("corrected_response", ""),
                        "metadata": {
                            "feedback_type": feedback.get("feedback_type", ""),
                            "original_rating": feedback.get("rating", 0),
                        },
                    }
                    retraining_examples.append(example)

        # Save retraining dataset
        output_path = Path(output_file)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        with open(output_path, "w", encoding="utf-8") as f:
            for example in retraining_examples:
                f.write(json.dumps(example, ensure_ascii=False) + "\n")

        logger.info(
            "Generated retraining dataset from feedback",
            extra={
                "sample_count": len(retraining_examples),
                "output_file": output_file,
            },
        )

        return output_file

    def export_feedback_as_qa_pairs(
        self,
        output_file: str = "/app/data/feedback_qa_pairs.jsonl",
    ) -> str:
        """Export feedback as QA pairs for training.

        Args:
            output_file: Output file path

        Returns:
            Path to generated QA pairs
        """
        all_feedback = []

        for feedback_file in self.feedback_dir.glob("feedback_*.json"):
            try:
                with open(feedback_file, "r", encoding="utf-8") as f:
                    all_feedback.append(json.load(f))
            except Exception as e:
                logger.warning(
                    "Failed to read feedback file",
                    extra={"file": str(feedback_file), "error": str(e)},
                )

        # Create QA pairs
        qa_pairs = []

        for feedback in all_feedback:
            qa_pair = {
                "question": feedback.get("user_query", ""),
                "answer": feedback.get("corrected_response") or feedback.get("model_response", ""),
                "rating": feedback.get("rating", 3),
                "language": "hi",  # Default to Hindi
                "source": "user_feedback",
                "metadata": feedback.get("metadata", {}),
            }
            qa_pairs.append(qa_pair)

        # Save QA pairs
        output_path = Path(output_file)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        with open(output_path, "w", encoding="utf-8") as f:
            for qa in qa_pairs:
                f.write(json.dumps(qa, ensure_ascii=False) + "\n")

        logger.info(
            "Exported feedback as QA pairs",
            extra={"pair_count": len(qa_pairs), "output_file": output_file},
        )

        return output_file
