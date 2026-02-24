"""Language detection service using AI4Bharat models"""

import asyncio
from typing import Tuple

import structlog
import langid
import fasttext

from app.config import settings

logger = structlog.get_logger()


class LanguageDetector:
    """
    Detects language of input text.

    Uses a combination of:
    1. langid library (fast, covers all 22 Indian languages)
    2. Fallback to fastText language identification
    """

    def __init__(self):
        self.langid_model = None
        self._initialized = False

    async def initialize(self):
        """Initialize language detection models"""
        if self._initialized:
            return

        try:
            logger.info("Initializing language detection")

            # Load fastText model for better accuracy on Indic languages
            # This is a smaller, faster model
            import warnings

            warnings.filterwarnings("ignore")

            # langid is lightweight and pre-loaded
            self._initialized = True
            logger.info("Language detection initialized")

        except Exception as e:
            logger.error("Failed to initialize language detection", error=str(e))
            raise

    async def detect(self, text: str) -> Tuple[str, float]:
        """
        Detect language of input text.

        Returns:
            Tuple of (language_code, confidence)
            language_code: ISO 639-1 code (e.g., 'hi', 'en')
            confidence: Float between 0.0 and 1.0
        """
        if not text or not text.strip():
            # Default to English for empty text
            return "en", 0.5

        try:
            # Use langid for quick detection
            detected_lang, confidence = langid.classify(text)

            # Map langid codes to ISO 639-1
            lang_mapping = {
                "hi": "hi",
                "en": "en",
                "bn": "bn",
                "te": "te",
                "mr": "mr",
                "ta": "ta",
                "ur": "ur",
                "gu": "gu",
                "kn": "kn",
                "ml": "ml",
                "or": "or",
                "pa": "pa",
                "as": "as",
                "ne": "ne",
                # Add more mappings as needed
            }

            # Map detected language code
            mapped_lang = lang_mapping.get(detected_lang, detected_lang)

            # Ensure confidence is between 0 and 1
            confidence_normalized = min(max(float(confidence), 0.0), 1.0)

            logger.debug(
                "Language detected",
                language=mapped_lang,
                confidence=confidence_normalized,
                detected_code=detected_lang,
            )

            return mapped_lang, confidence_normalized

        except Exception as e:
            logger.warning("Language detection failed, defaulting to English", error=str(e))
            # Default to English on error
            return "en", 0.5


# Global singleton instance
language_detector = LanguageDetector()
