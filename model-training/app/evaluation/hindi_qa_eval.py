"""Hindi QA evaluation metrics."""

import re
from typing import Dict, List, Tuple
from collections import Counter

import nltk
from nltk.translate.bleu_score import sentence_bleu, corpus_bleu

from app.utils.logging_config import setup_json_logging


logger = setup_json_logging("hindi_qa_eval")

# Download required NLTK data
try:
    nltk.data.find("tokenizers/punkt")
except LookupError:
    nltk.download("punkt", quiet=True)


class HindiQAEvaluator:
    """Evaluate QA performance with Hindi-specific metrics."""

    def __init__(self):
        """Initialize evaluator."""
        pass

    def exact_match(self, prediction: str, reference: str) -> bool:
        """Calculate exact match.

        Args:
            prediction: Predicted answer
            reference: Reference answer

        Returns:
            True if exact match, False otherwise
        """
        # Normalize: lowercase, strip whitespace, remove punctuation
        pred_norm = self._normalize_text(prediction)
        ref_norm = self._normalize_text(reference)
        return pred_norm == ref_norm

    def f1_score(self, prediction: str, reference: str) -> float:
        """Calculate F1 score based on token overlap.

        Args:
            prediction: Predicted answer
            reference: Reference answer

        Returns:
            F1 score (0.0-1.0)
        """
        pred_tokens = self._tokenize(prediction)
        ref_tokens = self._tokenize(reference)

        common_tokens = Counter(pred_tokens) & Counter(ref_tokens)
        num_common = sum(common_tokens.values())

        if len(pred_tokens) == 0 or len(ref_tokens) == 0:
            return int(pred_tokens == ref_tokens)

        if num_common == 0:
            return 0.0

        precision = num_common / len(pred_tokens)
        recall = num_common / len(ref_tokens)

        f1 = (2 * precision * recall) / (precision + recall)
        return f1

    def bleu_score(self, prediction: str, references: List[str]) -> float:
        """Calculate BLEU score.

        Args:
            prediction: Predicted answer
            references: List of reference answers

        Returns:
            BLEU score (0.0-1.0)
        """
        pred_tokens = self._tokenize(prediction)

        # Calculate sentence BLEU
        reference_tokens = [self._tokenize(ref) for ref in references]

        if not pred_tokens:
            return 0.0

        # Use weights appropriate for short sequences
        weights = (0.5, 0.5) if len(pred_tokens) < 10 else (0.25, 0.25, 0.25, 0.25)

        try:
            bleu = sentence_bleu(reference_tokens, pred_tokens, weights=weights)
            return bleu
        except Exception as e:
            logger.warning("BLEU calculation failed", extra={"error": str(e)})
            return 0.0

    def evaluate_batch(
        self,
        predictions: List[str],
        references: List[str],
    ) -> Dict[str, float]:
        """Evaluate a batch of predictions.

        Args:
            predictions: List of predicted answers
            references: List of reference answers

        Returns:
            Dictionary with metrics
        """
        if len(predictions) != len(references):
            raise ValueError("Predictions and references must have same length")

        exact_matches = 0
        f1_scores = []
        bleu_scores = []

        for pred, ref in zip(predictions, references):
            # Exact match
            if self.exact_match(pred, ref):
                exact_matches += 1

            # F1 score
            f1 = self.f1_score(pred, ref)
            f1_scores.append(f1)

            # BLEU score
            bleu = self.bleu_score(pred, [ref])
            bleu_scores.append(bleu)

        metrics = {
            "exact_match": exact_matches / len(predictions),
            "f1": sum(f1_scores) / len(f1_scores),
            "bleu": sum(bleu_scores) / len(bleu_scores),
            "sample_count": len(predictions),
        }

        return metrics

    def _normalize_text(self, text: str) -> str:
        """Normalize text for comparison.

        Args:
            text: Input text

        Returns:
            Normalized text
        """
        # Remove extra whitespace
        text = " ".join(text.split())

        # Convert to lowercase
        text = text.lower()

        # Remove punctuation (but keep spaces)
        text = re.sub(r"[^\w\s]", "", text)

        return text

    def _tokenize(self, text: str) -> List[str]:
        """Tokenize text (works with Hindi and English).

        Args:
            text: Input text

        Returns:
            List of tokens
        """
        # Simple whitespace tokenization (handles both Hindi and English)
        text = text.strip()
        tokens = text.split()
        return tokens

    def hindi_specific_evaluation(
        self,
        predictions: List[str],
        references: List[str],
    ) -> Dict[str, float]:
        """Perform Hindi-specific evaluation.

        Args:
            predictions: List of predicted answers (in Hindi)
            references: List of reference answers (in Hindi)

        Returns:
            Dictionary with Hindi-specific metrics
        """
        metrics = self.evaluate_batch(predictions, references)

        # Add Hindi-specific metrics
        hindi_metrics = {
            "exact_match_hindi": metrics["exact_match"],
            "f1_hindi": metrics["f1"],
            "bleu_hindi": metrics["bleu"],
        }

        # Check for Devanagari script presence
        devanagari_pred = sum(
            1 for pred in predictions
            if self._has_devanagari(pred)
        ) / len(predictions)

        devanagari_ref = sum(
            1 for ref in references
            if self._has_devanagari(ref)
        ) / len(references)

        hindi_metrics["devanagari_consistency"] = (
            devanagari_pred if devanagari_ref > 0 else 0.0
        )

        return hindi_metrics

    def _has_devanagari(self, text: str) -> bool:
        """Check if text contains Devanagari script.

        Args:
            text: Input text

        Returns:
            True if contains Devanagari, False otherwise
        """
        # Devanagari Unicode range: U+0900 to U+097F
        for char in text:
            if "\u0900" <= char <= "\u097f":
                return True
        return False

    def token_overlap_ratio(self, prediction: str, reference: str) -> float:
        """Calculate token overlap ratio.

        Args:
            prediction: Predicted answer
            reference: Reference answer

        Returns:
            Overlap ratio (0.0-1.0)
        """
        pred_tokens = set(self._tokenize(prediction))
        ref_tokens = set(self._tokenize(reference))

        if len(ref_tokens) == 0:
            return 0.0

        overlap = len(pred_tokens & ref_tokens)
        return overlap / len(ref_tokens)

    def semantic_similarity_basic(self, prediction: str, reference: str) -> float:
        """Basic semantic similarity based on word overlap.

        Args:
            prediction: Predicted answer
            reference: Reference answer

        Returns:
            Similarity score (0.0-1.0)
        """
        pred_tokens = set(self._tokenize(self._normalize_text(prediction)))
        ref_tokens = set(self._tokenize(self._normalize_text(reference)))

        if len(ref_tokens) == 0:
            return 0.0

        intersection = len(pred_tokens & ref_tokens)
        union = len(pred_tokens | ref_tokens)

        if union == 0:
            return 0.0

        return intersection / union
