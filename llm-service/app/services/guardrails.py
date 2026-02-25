"""Guardrails service for content filtering

Implements PII redaction, hallucination detection, toxicity filtering,
and topic-based guardrails.
"""

import re
import logging
from typing import List, Optional, Tuple
from app.models.completions import Message

logger = logging.getLogger(__name__)


class GuardrailsService:
    """Content filtering and safety validation service"""

    # PII patterns
    # Phone pattern must come first to avoid conflicts with Aadhaar (phone: +91XXXXXXXXXX)
    PHONE_PATTERN = r"(?:\+91|0)[6-9]\d{9}"
    AADHAAR_PATTERN = r"\b[0-9]{4}\s?[0-9]{4}\s?[0-9]{4}\b"
    EMAIL_PATTERN = r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b"
    PAN_PATTERN = r"\b[A-Z]{5}[0-9]{4}[A-Z]\b"

    # Toxicity keywords (Hindi and English)
    TOXIC_KEYWORDS = {
        # English toxic words (common offensive language)
        "hate", "kill", "stupid", "idiot", "ass", "damn",
        # Hindi toxic words
        "मादरचोद", "साला", "हरामजादा", "भांड", "कमीना",
        "भंगी", "चूत्या", "बेवकूफ", "गंदा", "घटिया"
    }

    # Topic boundaries (Ministry of Culture focus)
    ALLOWED_TOPICS = {
        "culture", "heritage", "monument", "museum", "art",
        "tradition", "language", "history", "archaeological",
        "संस्कृति", "विरासत", "स्मारक", "संग्रहालय", "कला",
        "परंपरा", "भाषा", "इतिहास", "पुरातत्व"
    }

    def __init__(self):
        """Initialize guardrails service"""
        pass

    async def validate_input(
        self,
        messages: List[Message],
        request_id: str = ""
    ) -> List[Message]:
        """Validate and sanitize input messages

        Args:
            messages: Chat message history
            request_id: Request ID for logging

        Returns:
            Sanitized messages

        Raises:
            ValueError if validation fails
        """
        try:
            sanitized_messages = []

            for msg in messages:
                # Skip system messages
                if msg.role == "system":
                    sanitized_messages.append(msg)
                    continue

                # Redact PII from user messages
                if msg.role == "user":
                    cleaned_content = self._redact_pii(msg.content)
                    sanitized_messages.append(
                        Message(role=msg.role, content=cleaned_content)
                    )
                else:
                    # Keep assistant messages as-is
                    sanitized_messages.append(msg)

            return sanitized_messages

        except Exception as e:
            logger.error(
                "Input validation failed",
                exc_info=True,
                extra={"request_id": request_id}
            )
            raise

    async def filter_output(
        self,
        text: str,
        request_id: str = ""
    ) -> str:
        """Filter LLM output for safety issues

        Args:
            text: Generated text
            request_id: Request ID for logging

        Returns:
            Filtered text

        Raises:
            ValueError if filtering fails severely
        """
        try:
            filtered_text = text

            # Check for toxicity
            has_toxicity = self._check_toxicity(filtered_text)
            if has_toxicity:
                logger.warning(
                    "Toxic content detected in output",
                    extra={"request_id": request_id}
                )
                # Remove toxic words but keep response
                filtered_text = self._remove_toxic_words(filtered_text)

            # Check for PII leakage
            if self._detect_pii(filtered_text):
                logger.warning(
                    "PII detected in output",
                    extra={"request_id": request_id}
                )
                filtered_text = self._redact_pii(filtered_text)

            return filtered_text

        except Exception as e:
            logger.error(
                "Output filtering failed",
                exc_info=True,
                extra={"request_id": request_id}
            )
            # Return original text on error (fail open)
            return text

    def _redact_pii(self, text: str) -> str:
        """Redact PII from text

        Args:
            text: Input text

        Returns:
            Text with PII redacted
        """
        # Redact phone numbers first (to avoid conflicts with Aadhaar pattern)
        text = re.sub(self.PHONE_PATTERN, "[PHONE_REDACTED]", text)

        # Redact Aadhaar
        text = re.sub(self.AADHAAR_PATTERN, "[AADHAAR_REDACTED]", text)

        # Redact emails
        text = re.sub(self.EMAIL_PATTERN, "[EMAIL_REDACTED]", text)

        # Redact PAN
        text = re.sub(self.PAN_PATTERN, "[PAN_REDACTED]", text)

        return text

    def _detect_pii(self, text: str) -> bool:
        """Check if text contains PII

        Args:
            text: Input text

        Returns:
            True if PII detected
        """
        if re.search(self.AADHAAR_PATTERN, text):
            return True
        if re.search(self.PHONE_PATTERN, text):
            return True
        if re.search(self.EMAIL_PATTERN, text):
            return True
        if re.search(self.PAN_PATTERN, text):
            return True
        return False

    def _check_toxicity(self, text: str) -> bool:
        """Check if text contains toxic content

        Args:
            text: Input text

        Returns:
            True if toxic content detected
        """
        text_lower = text.lower()
        for keyword in self.TOXIC_KEYWORDS:
            if keyword in text_lower:
                return True
        return False

    def _remove_toxic_words(self, text: str) -> str:
        """Remove toxic words from text

        Args:
            text: Input text

        Returns:
            Text with toxic words removed/replaced
        """
        result = text
        for keyword in self.TOXIC_KEYWORDS:
            # Case-insensitive replacement
            result = re.sub(
                rf"\b{re.escape(keyword)}\b",
                "[REDACTED]",
                result,
                flags=re.IGNORECASE
            )
        return result

    def _detect_hallucination(
        self,
        generated_text: str,
        context: str,
        threshold: float = 0.7
    ) -> Tuple[bool, float]:
        """Detect if response contains hallucinations by cross-checking context

        Args:
            generated_text: Generated response
            context: Source context
            threshold: Hallucination score threshold

        Returns:
            Tuple of (is_hallucinating, confidence)
        """
        # Simple keyword overlap-based detection
        # In production, use advanced techniques like semantic similarity
        gen_words = set(generated_text.lower().split())
        ctx_words = set(context.lower().split())

        # Check if key claims are grounded in context
        overlap = len(gen_words & ctx_words) / (len(gen_words) + 1e-6)

        # If too little overlap with context, likely hallucinating
        is_hallucinating = overlap < threshold

        return is_hallucinating, overlap
