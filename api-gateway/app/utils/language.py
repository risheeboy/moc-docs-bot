"""Language detection utilities."""

from langdetect import detect, detect_langs
from langdetect.lang_detect_exception import LangDetectException
import logging

logger = logging.getLogger(__name__)


def detect_language(text: str) -> str:
    """
    Detect language from text.

    Handles code-mixed Hindi-English by returning most probable language.
    """
    if not text or len(text.strip()) < 2:
        return "en"

    try:
        # Get probabilities for all detected languages
        probs = detect_langs(text)
        if probs:
            # Return the most probable language
            lang = probs[0].lang
            # Map to our supported codes
            lang_map = {
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
            }
            return lang_map.get(lang, "en")
    except LangDetectException:
        pass

    return "en"


def is_code_mixed(text: str) -> bool:
    """Check if text is code-mixed (multiple languages)."""
    try:
        probs = detect_langs(text)
        # If confidence of top language < 0.8, likely code-mixed
        if probs and probs[0].prob < 0.8:
            return True
    except LangDetectException:
        pass
    return False
