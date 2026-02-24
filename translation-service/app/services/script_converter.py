"""Script and transliteration utilities"""

import structlog
from typing import Optional

logger = structlog.get_logger()


class ScriptConverter:
    """
    Handles transliteration between different Indic scripts.

    Currently provides basic support for common script conversions.
    For production use, integrate with indic-nlp-library or similar.
    """

    # Common script mappings
    SCRIPT_MAPPING = {
        "hi": "Devanagari",
        "en": "Latin",
        "bn": "Bengali",
        "te": "Telugu",
        "mr": "Devanagari",
        "ta": "Tamil",
        "ur": "Perso-Arabic",
        "gu": "Gujarati",
        "kn": "Kannada",
        "ml": "Malayalam",
        "or": "Odia",
        "pa": "Gurmukhi",
        "as": "Bengali",
        "mai": "Devanagari",
        "sa": "Devanagari",
        "ne": "Devanagari",
        "sd": "Perso-Arabic",
        "kok": "Devanagari",
        "doi": "Devanagari",
        "mni": "Meitei",
        "sat": "Ol Chiki",
        "bo": "Devanagari",
        "ks": "Perso-Arabic",
    }

    @staticmethod
    def get_script(language_code: str) -> str:
        """Get the script used by a language"""
        return ScriptConverter.SCRIPT_MAPPING.get(language_code, "Unknown")

    @staticmethod
    def transliterate_devanagari_to_latin(text: str) -> str:
        """
        Simple Devanagari to Latin transliteration.

        For production use, integrate with indic-nlp-library:
        from indic_nlp.transliterate import unicode_transliterate
        """
        # This is a simplified version
        # In production, use indic-nlp-library for better accuracy
        try:
            from indic_nlp.transliterate import unicode_transliterate

            return unicode_transliterate.romanize("hin", text)
        except ImportError:
            logger.warning(
                "indic-nlp-library not available, returning original text"
            )
            return text
        except Exception as e:
            logger.warning(
                "Devanagari to Latin transliteration failed",
                error=str(e),
            )
            return text

    @staticmethod
    def transliterate_latin_to_devanagari(text: str) -> str:
        """
        Simple Latin to Devanagari transliteration (phonetic).

        For production use, integrate with proper transliteration library.
        """
        try:
            from indic_nlp.transliterate import unicode_transliterate

            return unicode_transliterate.transliterate("hin", text)
        except ImportError:
            logger.warning(
                "indic-nlp-library not available, returning original text"
            )
            return text
        except Exception as e:
            logger.warning(
                "Latin to Devanagari transliteration failed",
                error=str(e),
            )
            return text

    @staticmethod
    def normalize_text(text: str, language: str) -> str:
        """
        Normalize text for the given language.

        Handles Unicode normalization and script-specific normalization.
        """
        import unicodedata

        try:
            # NFD normalization (decomposed form)
            normalized = unicodedata.normalize("NFKD", text)

            # Remove zero-width characters and other invisible Unicode
            cleaned = "".join(
                c
                for c in normalized
                if unicodedata.category(c) not in ("Cf", "Cc")
                and c.strip()
            )

            return cleaned
        except Exception as e:
            logger.warning("Text normalization failed", error=str(e))
            return text


# Global singleton instance
script_converter = ScriptConverter()
