"""Language detection and classification for documents."""

import structlog
from typing import Optional, Tuple

logger = structlog.get_logger()


class LanguageClassifier:
    """Classifier for detecting document language."""

    def __init__(self, min_confidence: float = 0.7):
        """Initialize language classifier.

        Args:
            min_confidence: Minimum confidence threshold
        """
        self.min_confidence = min_confidence

    async def classify(self, content: str) -> Tuple[Optional[str], float]:
        """Classify language of content.

        Args:
            content: Text content to classify

        Returns:
            Tuple of (language_code, confidence)
        """
        if not content or len(content.strip()) < 10:
            return None, 0.0

        try:
            # Try langdetect first
            language, confidence = await self._detect_with_langdetect(content)

            if confidence >= self.min_confidence:
                return language, confidence

            # Fallback to textblob
            language, confidence = await self._detect_with_textblob(content)

            if confidence >= self.min_confidence:
                return language, confidence

            logger.warning(
                "low_confidence_language_detection",
                detected_language=language,
                confidence=confidence,
            )

            return language, confidence

        except Exception as e:
            logger.error(
                "language_detection_error",
                error=str(e),
            )
            return None, 0.0

    async def _detect_with_langdetect(
        self, content: str
    ) -> Tuple[Optional[str], float]:
        """Detect language using langdetect library.

        Args:
            content: Text content

        Returns:
            Tuple of (language_code, confidence)
        """
        try:
            from langdetect import detect, detect_langs

            # Get all probabilities
            probs = detect_langs(content)

            if probs:
                # Get highest probability
                lang_prob = probs[0]
                language = lang_prob.lang
                confidence = lang_prob.prob

                # Map language codes if needed
                language = self._normalize_language_code(language)

                return language, confidence

        except Exception as e:
            logger.debug("langdetect_error", error=str(e))

        return None, 0.0

    async def _detect_with_textblob(
        self, content: str
    ) -> Tuple[Optional[str], float]:
        """Detect language using textblob (fallback).

        Args:
            content: Text content

        Returns:
            Tuple of (language_code, confidence)
        """
        try:
            from textblob import TextBlob

            blob = TextBlob(content)
            language = blob.detect_language()

            # TextBlob doesn't provide confidence, assume reasonable value
            confidence = 0.8

            language = self._normalize_language_code(language)

            return language, confidence

        except Exception as e:
            logger.debug("textblob_error", error=str(e))

        return None, 0.0

    @staticmethod
    def _normalize_language_code(code: str) -> str:
        """Normalize language code to ISO 639-1 format.

        Args:
            code: Language code

        Returns:
            Normalized language code
        """
        # Map of common language code variations
        mapping = {
            "hi-in": "hi",
            "en-us": "en",
            "en-gb": "en",
            "pt-br": "pt",
            "zh-cn": "zh",
            "zh-tw": "zh",
        }

        code_lower = code.lower()

        if code_lower in mapping:
            return mapping[code_lower]

        # Return first part if hyphenated
        if "-" in code_lower:
            return code_lower.split("-")[0]

        return code_lower


class LanguageDetectionValidator:
    """Validator for checking language detection results."""

    # Define expected scripts for each language
    SCRIPT_MAPPING = {
        "hi": ["Devanagari"],
        "en": ["Latin"],
        "bn": ["Bengali"],
        "te": ["Telugu"],
        "mr": ["Devanagari"],
        "ta": ["Tamil"],
        "ur": ["Perso-Arabic"],
        "gu": ["Gujarati"],
        "kn": ["Kannada"],
        "ml": ["Malayalam"],
        "or": ["Odia"],
        "pa": ["Gurmukhi"],
        "as": ["Bengali"],
    }

    @staticmethod
    async def detect_script(content: str) -> Optional[str]:
        """Detect script/writing system used in content.

        Args:
            content: Text content

        Returns:
            Script name or None
        """
        try:
            # Check for specific Unicode ranges
            for char in content:
                code = ord(char)

                # Devanagari
                if 0x0900 <= code <= 0x097F:
                    return "Devanagari"

                # Bengali
                if 0x0980 <= code <= 0x09FF:
                    return "Bengali"

                # Gurmukhi
                if 0x0A00 <= code <= 0x0A7F:
                    return "Gurmukhi"

                # Tamil
                if 0x0B80 <= code <= 0x0BFF:
                    return "Tamil"

                # Telugu
                if 0x0C00 <= code <= 0x0C7F:
                    return "Telugu"

                # Kannada
                if 0x0C80 <= code <= 0x0CFF:
                    return "Kannada"

                # Malayalam
                if 0x0D00 <= code <= 0x0D7F:
                    return "Malayalam"

                # Odia
                if 0x0B00 <= code <= 0x0B7F:
                    return "Odia"

                # Arabic/Perso-Arabic
                if 0x0600 <= code <= 0x06FF:
                    return "Perso-Arabic"

        except Exception as e:
            logger.debug("script_detection_error", error=str(e))

        return None
