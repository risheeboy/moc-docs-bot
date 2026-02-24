"""Post-processing for OCR text output."""

import re
import structlog

logger = structlog.get_logger()


class PostProcessor:
    """Post-process OCR text output (fixes, cleanups, language-specific corrections)."""

    # Hindi ligatures and common OCR errors
    HINDI_CORRECTIONS = {
        # Common OCR mistakes for Hindi
        "।।": "।",  # Duplicate danda
        "॥॥": "॥",  # Duplicate double danda
        "०": "0",  # Devanagari zero to ASCII zero (when in numbers)
        "१": "1",  # Devanagari one to ASCII one
        "२": "2",
        "३": "3",
        "४": "4",
        "५": "5",
        "६": "6",
        "७": "7",
        "८": "8",
        "९": "9",
    }

    # English common OCR errors
    ENGLISH_CORRECTIONS = {
        r"\bl\b": "I",  # lowercase 'l' to uppercase 'I' in isolation
        r"rn": "m",  # 'rn' sometimes looks like 'm'
        r"0l": "01",  # zero-ell to zero-one
    }

    def __init__(self):
        """Initialize post-processor."""
        pass

    def postprocess(self, text: str, languages: str) -> str:
        """
        Post-process OCR text.

        Args:
            text: Raw OCR output text
            languages: Language codes (e.g., "hi,en")

        Returns:
            Cleaned and corrected text
        """
        try:
            # Apply general cleanup
            text = self._cleanup_text(text)

            # Language-specific corrections
            if "hi" in languages or "hin" in languages:
                text = self._fix_hindi_text(text)

            if "en" in languages or "eng" in languages:
                text = self._fix_english_text(text)

            # Remove excessive whitespace
            text = self._normalize_whitespace(text)

            return text

        except Exception as e:
            logger.warning("postprocessing_error", error=str(e))
            return text

    def _cleanup_text(self, text: str) -> str:
        """
        General text cleanup.

        Args:
            text: Raw text

        Returns:
            Cleaned text
        """
        # Remove control characters except newline and tab
        text = "".join(c for c in text if ord(c) >= 32 or c in "\n\t\r")

        # Fix common OCR artifacts
        text = text.replace("||", "|")  # Double pipes
        text = text.replace("--", "–")  # Double hyphens

        return text

    def _fix_hindi_text(self, text: str) -> str:
        """
        Fix Hindi-specific OCR errors.

        Args:
            text: Hindi text

        Returns:
            Corrected text
        """
        # Apply Hindi corrections
        for error, correction in self.HINDI_CORRECTIONS.items():
            text = text.replace(error, correction)

        # Fix common Hindi ligature errors
        text = re.sub(r"([क-ह])\s+्\s+([य-ज])", r"\1्\2", text)

        # Fix matra placement (virama placement errors)
        # This is a simplified fix; real implementation would need
        # more sophisticated text analysis
        text = re.sub(r"्\s+", "्", text)

        # Fix spacing around common punctuation
        text = re.sub(r"(\s)*।(\s)*", " । ", text)
        text = re.sub(r"(\s)*॥(\s)*", " ॥ ", text)

        return text

    def _fix_english_text(self, text: str) -> str:
        """
        Fix English-specific OCR errors.

        Args:
            text: English text

        Returns:
            Corrected text
        """
        # Common OCR corrections
        corrections = {
            r"\bl\b": "I",  # 'l' to 'I' in isolation
            r"O([0-9])": r"0\1",  # 'O' followed by digit to '0'
            r"I([0-9]+)": r"1\1",  # 'I' at start of number to '1'
        }

        for pattern, replacement in corrections.items():
            text = re.sub(pattern, replacement, text, flags=re.IGNORECASE)

        # Fix common word errors
        word_corrections = {
            "tlie": "the",
            "tne": "the",
            "tn": "th",
            "citv": "city",
            "govemment": "government",
            "informatoin": "information",
        }

        for wrong, correct in word_corrections.items():
            text = re.sub(r"\b" + wrong + r"\b", correct, text, flags=re.IGNORECASE)

        return text

    def _normalize_whitespace(self, text: str) -> str:
        """
        Normalize whitespace in text.

        Args:
            text: Text with potentially irregular whitespace

        Returns:
            Text with normalized whitespace
        """
        # Remove leading/trailing whitespace from each line
        lines = [line.strip() for line in text.split("\n")]

        # Remove empty lines (but keep some structure)
        non_empty = []
        prev_empty = False
        for line in lines:
            if line.strip():
                non_empty.append(line)
                prev_empty = False
            elif not prev_empty:
                # Keep one empty line for paragraph breaks
                non_empty.append("")
                prev_empty = True

        # Remove trailing empty lines
        while non_empty and not non_empty[-1]:
            non_empty.pop()

        text = "\n".join(non_empty)

        # Normalize multiple spaces to single space
        text = re.sub(r" {2,}", " ", text)

        # Normalize tabs to spaces
        text = text.replace("\t", "  ")

        return text
