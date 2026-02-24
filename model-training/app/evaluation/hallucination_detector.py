"""Detect hallucinated facts in model outputs."""

from typing import Dict, List, Tuple, Optional
import re

from app.utils.logging_config import setup_json_logging


logger = setup_json_logging("hallucination_detector")


class HallucinationDetector:
    """Detect hallucinations in model responses."""

    def __init__(self):
        """Initialize detector."""
        self.patterns = {
            "numbers": r"\d+",
            "dates": r"\d{1,2}[-/]\d{1,2}[-/]\d{2,4}",
            "named_entities": r"[A-Z][a-z]+",
            "urls": r"https?://[^\s]+",
            "hindi_text": r"[\u0900-\u097f]+",
        }

    def detect_hallucinations(
        self,
        prediction: str,
        source_documents: List[str],
    ) -> Dict[str, float]:
        """Detect hallucinations in prediction against sources.

        Args:
            prediction: Model prediction
            source_documents: List of source documents

        Returns:
            Dictionary with hallucination metrics
        """
        source_text = " ".join(source_documents)

        # Extract facts from prediction
        facts = self._extract_facts(prediction)

        # Check each fact against sources
        supported_facts = 0
        total_facts = len(facts)

        for fact in facts:
            if self._fact_supported(fact, source_text):
                supported_facts += 1
            else:
                logger.debug(
                    "Unsupported fact detected",
                    extra={"fact": fact},
                )

        hallucination_rate = (
            0.0 if total_facts == 0
            else 1.0 - (supported_facts / total_facts)
        )

        return {
            "hallucination_rate": hallucination_rate,
            "total_facts": total_facts,
            "supported_facts": supported_facts,
            "hallucinated_facts": total_facts - supported_facts,
            "confidence_score": 1.0 - hallucination_rate,
        }

    def _extract_facts(self, text: str) -> List[str]:
        """Extract facts from text.

        Args:
            text: Input text

        Returns:
            List of extracted facts (simple extraction)
        """
        facts = []

        # Extract sentences as basic facts
        sentences = re.split(r"[.!?]+", text)
        for sentence in sentences:
            sentence = sentence.strip()
            if len(sentence.split()) >= 3:  # At least 3 words
                facts.append(sentence)

        return facts

    def _fact_supported(self, fact: str, source_text: str) -> bool:
        """Check if fact is supported by source text.

        Args:
            fact: Fact to check
            source_text: Source text

        Returns:
            True if supported, False otherwise
        """
        # Simple keyword-based check
        fact_lower = fact.lower()
        source_lower = source_text.lower()

        # Extract key terms from fact
        words = fact_lower.split()

        # Check if at least 70% of key terms appear in source
        key_words = [w for w in words if len(w) > 4]

        if not key_words:
            return True  # No meaningful terms to check

        matches = sum(1 for word in key_words if word in source_lower)

        return matches / len(key_words) >= 0.7

    def check_factual_consistency(
        self,
        prediction: str,
        reference: str,
    ) -> Dict[str, float]:
        """Check factual consistency between prediction and reference.

        Args:
            prediction: Model prediction
            reference: Reference answer

        Returns:
            Consistency metrics
        """
        pred_facts = self._extract_facts(prediction)
        ref_facts = self._extract_facts(reference)

        # Simple consistency check based on fact overlap
        consistent_facts = 0

        for pred_fact in pred_facts:
            for ref_fact in ref_facts:
                if self._facts_similar(pred_fact, ref_fact):
                    consistent_facts += 1
                    break

        consistency_score = (
            1.0 if len(pred_facts) == 0
            else consistent_facts / len(pred_facts)
        )

        return {
            "factual_consistency": consistency_score,
            "prediction_facts": len(pred_facts),
            "reference_facts": len(ref_facts),
            "consistent_facts": consistent_facts,
        }

    def _facts_similar(self, fact1: str, fact2: str) -> bool:
        """Check if two facts are similar.

        Args:
            fact1: First fact
            fact2: Second fact

        Returns:
            True if similar, False otherwise
        """
        words1 = set(fact1.lower().split())
        words2 = set(fact2.lower().split())

        if not words1 or not words2:
            return False

        intersection = len(words1 & words2)
        union = len(words1 | words2)

        similarity = intersection / union if union > 0 else 0.0

        return similarity >= 0.5  # 50% word overlap threshold

    def detect_contradictions(
        self,
        predictions: List[str],
    ) -> List[Tuple[int, int, str]]:
        """Detect contradictions among multiple predictions.

        Args:
            predictions: List of predictions

        Returns:
            List of (idx1, idx2, contradiction) tuples
        """
        contradictions = []

        for i in range(len(predictions)):
            for j in range(i + 1, len(predictions)):
                if self._contains_contradiction(predictions[i], predictions[j]):
                    contradictions.append((i, j, "Contradiction detected"))

        return contradictions

    def _contains_contradiction(self, text1: str, text2: str) -> bool:
        """Check if two texts contain contradictions.

        Args:
            text1: First text
            text2: Second text

        Returns:
            True if contradiction detected, False otherwise
        """
        # Simple negation-based contradiction detection
        negation_words = ["not", "no", "never", "नहीं", "कभी नहीं"]

        for neg_word in negation_words:
            if neg_word in text1.lower() and neg_word not in text2.lower():
                # Extract what is negated in text1
                negated_phrase = self._extract_negated_phrase(text1, neg_word)
                if negated_phrase and negated_phrase in text2.lower():
                    return True

        return False

    def _extract_negated_phrase(self, text: str, negation_word: str) -> Optional[str]:
        """Extract the phrase being negated.

        Args:
            text: Input text
            negation_word: Negation word

        Returns:
            Negated phrase or None
        """
        text_lower = text.lower()
        pos = text_lower.find(negation_word)

        if pos == -1:
            return None

        # Get words after negation
        after_negation = text[pos + len(negation_word):].strip()
        words = after_negation.split()

        # Return first 2-3 words after negation
        return " ".join(words[:3]) if words else None

    def evaluate_batch_hallucinations(
        self,
        predictions: List[str],
        sources: List[List[str]],
    ) -> Dict[str, float]:
        """Evaluate hallucinations in a batch.

        Args:
            predictions: List of predictions
            sources: List of source documents per prediction

        Returns:
            Aggregated metrics
        """
        all_hallucination_rates = []

        for pred, source_docs in zip(predictions, sources):
            result = self.detect_hallucinations(pred, source_docs)
            all_hallucination_rates.append(result["hallucination_rate"])

        avg_hallucination_rate = (
            sum(all_hallucination_rates) / len(all_hallucination_rates)
            if all_hallucination_rates
            else 0.0
        )

        return {
            "average_hallucination_rate": avg_hallucination_rate,
            "max_hallucination_rate": max(all_hallucination_rates) if all_hallucination_rates else 0.0,
            "min_hallucination_rate": min(all_hallucination_rates) if all_hallucination_rates else 0.0,
            "sample_count": len(predictions),
        }
