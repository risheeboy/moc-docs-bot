"""LLM-as-judge response quality evaluation."""

import asyncio
import json
from typing import Dict, List, Optional

from app.utils.logging_config import setup_json_logging


logger = setup_json_logging("response_quality")


class ResponseQualityEvaluator:
    """Evaluate response quality using LLM-as-judge approach."""

    def __init__(self, llm_service_url: str = "http://llm-service:8002"):
        """Initialize response quality evaluator.

        Args:
            llm_service_url: URL of LLM service
        """
        self.llm_service_url = llm_service_url

    async def evaluate_response_quality(
        self,
        question: str,
        response: str,
        reference: Optional[str] = None,
        context: Optional[str] = None,
    ) -> Dict[str, float]:
        """Evaluate response quality using LLM as judge.

        Args:
            question: Input question
            response: Model response to evaluate
            reference: Reference answer (optional)
            context: Source context (optional)

        Returns:
            Quality metrics (0-5 scale)
        """
        evaluation_prompt = self._build_evaluation_prompt(
            question, response, reference, context
        )

        try:
            llm_judgment = await self._get_llm_judgment(evaluation_prompt)
            metrics = self._parse_judgment(llm_judgment)
            return metrics

        except Exception as e:
            logger.error(
                "LLM judgment failed",
                extra={"error": str(e), "question": question[:100]},
                exc_info=True,
            )
            # Return default scores on failure
            return {
                "relevance": 2.5,
                "correctness": 2.5,
                "completeness": 2.5,
                "clarity": 2.5,
                "overall": 2.5,
            }

    def _build_evaluation_prompt(
        self,
        question: str,
        response: str,
        reference: Optional[str],
        context: Optional[str],
    ) -> str:
        """Build evaluation prompt for LLM judge.

        Args:
            question: Input question
            response: Model response
            reference: Reference answer
            context: Source context

        Returns:
            Evaluation prompt
        """
        prompt = f"""Evaluate the quality of the following response on a scale of 1-5 for each criterion.

Question: {question}

Response to evaluate:
{response}

"""

        if reference:
            prompt += f"Reference answer:\n{reference}\n\n"

        if context:
            prompt += f"Source context:\n{context}\n\n"

        prompt += """Evaluate on these criteria:
1. Relevance (1-5): How relevant is the response to the question?
2. Correctness (1-5): Is the information factually correct?
3. Completeness (1-5): Does it fully address the question?
4. Clarity (1-5): Is the response clear and well-structured?

Provide scores in JSON format:
{
  "relevance": <score 1-5>,
  "correctness": <score 1-5>,
  "completeness": <score 1-5>,
  "clarity": <score 1-5>,
  "reasoning": "<brief explanation>"
}"""

        return prompt

    async def _get_llm_judgment(self, prompt: str) -> str:
        """Get judgment from LLM service.

        Args:
            prompt: Evaluation prompt

        Returns:
            LLM judgment (JSON string)
        """
        import httpx

        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.llm_service_url}/v1/chat/completions",
                json={
                    "model": "meta-llama/Llama-3.1-8B-Instruct-AWQ",
                    "messages": [
                        {"role": "system", "content": "You are an expert evaluator of response quality."},
                        {"role": "user", "content": prompt},
                    ],
                    "temperature": 0.3,
                    "max_tokens": 500,
                },
                timeout=30.0,
            )
            response.raise_for_status()

            result = response.json()
            return result["choices"][0]["message"]["content"]

    def _parse_judgment(self, judgment_text: str) -> Dict[str, float]:
        """Parse LLM judgment into metrics.

        Args:
            judgment_text: LLM judgment text

        Returns:
            Metrics dictionary
        """
        try:
            # Extract JSON from response
            import re
            json_match = re.search(r"\{.*\}", judgment_text, re.DOTALL)

            if json_match:
                judgment_json = json.loads(json_match.group())

                # Extract scores
                relevance = float(judgment_json.get("relevance", 2.5))
                correctness = float(judgment_json.get("correctness", 2.5))
                completeness = float(judgment_json.get("completeness", 2.5))
                clarity = float(judgment_json.get("clarity", 2.5))

                # Calculate overall score (average)
                overall = (relevance + correctness + completeness + clarity) / 4

                return {
                    "relevance": min(5.0, max(1.0, relevance)),
                    "correctness": min(5.0, max(1.0, correctness)),
                    "completeness": min(5.0, max(1.0, completeness)),
                    "clarity": min(5.0, max(1.0, clarity)),
                    "overall": min(5.0, max(1.0, overall)),
                }

        except Exception as e:
            logger.warning(
                "Failed to parse judgment",
                extra={"error": str(e)},
            )

        # Default scores
        return {
            "relevance": 2.5,
            "correctness": 2.5,
            "completeness": 2.5,
            "clarity": 2.5,
            "overall": 2.5,
        }

    async def evaluate_batch_quality(
        self,
        questions: List[str],
        responses: List[str],
        references: Optional[List[str]] = None,
    ) -> Dict[str, float]:
        """Evaluate quality of a batch of responses.

        Args:
            questions: List of questions
            responses: List of responses
            references: Optional list of references

        Returns:
            Aggregated quality metrics
        """
        if len(questions) != len(responses):
            raise ValueError("Questions and responses must have equal length")

        all_metrics = []

        for i, (question, response) in enumerate(zip(questions, responses)):
            reference = references[i] if references and i < len(references) else None

            metrics = await self.evaluate_response_quality(
                question, response, reference
            )
            all_metrics.append(metrics)

        # Aggregate metrics
        aggregated = {
            "relevance": sum(m["relevance"] for m in all_metrics) / len(all_metrics),
            "correctness": sum(m["correctness"] for m in all_metrics) / len(all_metrics),
            "completeness": sum(m["completeness"] for m in all_metrics) / len(all_metrics),
            "clarity": sum(m["clarity"] for m in all_metrics) / len(all_metrics),
            "overall": sum(m["overall"] for m in all_metrics) / len(all_metrics),
            "sample_count": len(all_metrics),
        }

        return aggregated

    def evaluate_response_length(self, response: str) -> Dict[str, float]:
        """Evaluate response length appropriateness.

        Args:
            response: Model response

        Returns:
            Length metrics
        """
        words = len(response.split())
        sentences = len(response.split("."))

        # Ideal response: 50-200 words
        length_score = 1.0
        if words < 20:
            length_score = 0.5  # Too short
        elif words > 300:
            length_score = 0.7  # Too long but acceptable

        return {
            "word_count": words,
            "sentence_count": sentences,
            "avg_sentence_length": words / max(1, sentences),
            "length_score": length_score,
        }

    def evaluate_language_quality(self, response: str) -> Dict[str, float]:
        """Evaluate language quality (grammar, fluency).

        Args:
            response: Model response

        Returns:
            Language quality metrics
        """
        # Simple language quality check
        words = response.split()
        sentences = [s.strip() for s in response.split(".") if s.strip()]

        # Check for common issues
        repeated_words = self._check_repeated_words(response)
        fragment_sentences = sum(1 for s in sentences if len(s.split()) < 3)
        long_sentences = sum(1 for s in sentences if len(s.split()) > 30)

        quality_score = 1.0
        if repeated_words > 3:
            quality_score -= 0.2
        if fragment_sentences > len(sentences) * 0.3:
            quality_score -= 0.1
        if long_sentences > len(sentences) * 0.5:
            quality_score -= 0.1

        return {
            "grammar_score": max(0.0, quality_score),
            "repeated_words": repeated_words,
            "fragment_sentences": fragment_sentences,
            "long_sentences": long_sentences,
            "sentence_count": len(sentences),
        }

    def _check_repeated_words(self, text: str) -> int:
        """Check for repeated words.

        Args:
            text: Input text

        Returns:
            Number of repeated word instances
        """
        words = text.lower().split()
        word_counts = {}

        for word in words:
            word_counts[word] = word_counts.get(word, 0) + 1

        # Count words that appear more than 3 times
        repeated = sum(1 for count in word_counts.values() if count > 3)

        return repeated
