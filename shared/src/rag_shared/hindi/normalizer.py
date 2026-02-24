"""Unicode normalization for Devanagari (Hindi) text."""

import unicodedata
import re
from typing import Optional


class HindiNormalizer:
    """Normalizer for Hindi/Devanagari text.

    Provides Unicode normalization (NFC, NFD, NFKC, NFKD) and
    Hindi-specific text preprocessing.
    """

    # Devanagari Unicode ranges
    DEVANAGARI_RANGE = range(0x0900, 0x097F)

    # Combine character mappings (nukta forms)
    NUKTA_MAP = {
        "क़": "क",  # QA -> KA
        "ख़": "ख",  # KHHA -> KHA
        "ग़": "ग",  # GHHA -> GA
        "ज़": "ज",  # ZA -> JA
        "ड़": "ड",  # DDHA -> DDA
        "ढ़": "ढ",  # RHA -> DHA
        "प़": "प",  # PHA -> PA
        "फ़": "फ",  # FA -> PHA
        "य़": "य",  # YYA -> YA
    }

    # Variant forms
    VARIANT_MAP = {
        "ा": "ा",  # Normalize vowel signs
        "ि": "ि",
        "ु": "ु",
        "ृ": "ृ",
        "ृ": "ृ",
    }

    @classmethod
    def normalize_nfc(cls, text: str) -> str:
        """Apply NFC normalization (canonical composition).

        NFC is the default and recommended form for most purposes.

        Args:
            text: Input Devanagari text

        Returns:
            NFC normalized text
        """
        return unicodedata.normalize("NFC", text)

    @classmethod
    def normalize_nfd(cls, text: str) -> str:
        """Apply NFD normalization (canonical decomposition).

        Decomposes characters into base + combining marks.

        Args:
            text: Input text

        Returns:
            NFD normalized text
        """
        return unicodedata.normalize("NFD", text)

    @classmethod
    def normalize_nfkc(cls, text: str) -> str:
        """Apply NFKC normalization (compatibility composition).

        Converts compatibility characters to canonical form.

        Args:
            text: Input text

        Returns:
            NFKC normalized text
        """
        return unicodedata.normalize("NFKC", text)

    @classmethod
    def normalize_nfkd(cls, text: str) -> str:
        """Apply NFKD normalization (compatibility decomposition).

        Args:
            text: Input text

        Returns:
            NFKD normalized text
        """
        return unicodedata.normalize("NFKD", text)

    @classmethod
    def remove_nukta(cls, text: str) -> str:
        """Remove nukta diacritics (e.g., convert क़ to क).

        Args:
            text: Input Devanagari text

        Returns:
            Text with nukta forms normalized
        """
        for nukta_char, base_char in cls.NUKTA_MAP.items():
            text = text.replace(nukta_char, base_char)
        return text

    @classmethod
    def remove_accents(cls, text: str) -> str:
        """Remove accent marks and diacritics.

        Args:
            text: Input text

        Returns:
            Text without combining marks
        """
        # NFD decompose characters
        decomposed = unicodedata.normalize("NFD", text)

        # Filter out combining marks (category Mn = Mark, nonspacing)
        result = "".join(c for c in decomposed if unicodedata.category(c) != "Mn")

        return result

    @classmethod
    def normalize_whitespace(cls, text: str) -> str:
        """Normalize whitespace (multiple spaces to single).

        Args:
            text: Input text

        Returns:
            Text with normalized whitespace
        """
        # Replace multiple spaces with single space
        text = re.sub(r"\s+", " ", text)

        # Remove leading/trailing whitespace
        text = text.strip()

        return text

    @classmethod
    def normalize_quotes(cls, text: str) -> str:
        """Normalize quote characters to ASCII equivalents.

        Args:
            text: Input text

        Returns:
            Text with normalized quotes
        """
        # Unicode quotes to ASCII
        replacements = {
            """: '"',
            """: '"',
            "'": "'",
            "'": "'",
            "«": '"',
            "»": '"',
            "‹": "'",
            "›": "'",
        }

        for unicode_char, ascii_char in replacements.items():
            text = text.replace(unicode_char, ascii_char)

        return text

    @classmethod
    def normalize_numbers(cls, text: str) -> str:
        """Convert Devanagari digits to ASCII digits.

        Args:
            text: Input text with possible Devanagari digits

        Returns:
            Text with ASCII digits
        """
        # Devanagari digits (०-९) to ASCII (0-9)
        devanagari_digits = "०१२३४५६७८९"
        ascii_digits = "0123456789"

        for dev_digit, ascii_digit in zip(devanagari_digits, ascii_digits):
            text = text.replace(dev_digit, ascii_digit)

        return text

    @classmethod
    def is_hindi(cls, text: str) -> bool:
        """Check if text contains Hindi/Devanagari characters.

        Args:
            text: Input text

        Returns:
            True if text contains Devanagari characters
        """
        for char in text:
            if ord(char) in cls.DEVANAGARI_RANGE:
                return True
        return False

    @classmethod
    def normalize_full(
        cls,
        text: str,
        remove_nukta: bool = True,
        normalize_whitespace: bool = True,
        normalize_quotes: bool = True,
        normalize_numbers: bool = False,
    ) -> str:
        """Apply complete normalization pipeline.

        Args:
            text: Input text
            remove_nukta: Remove nukta diacritics
            normalize_whitespace: Normalize spaces
            normalize_quotes: Normalize quotes
            normalize_numbers: Convert Devanagari to ASCII digits

        Returns:
            Fully normalized text
        """
        # Start with NFC normalization
        text = cls.normalize_nfc(text)

        if remove_nukta:
            text = cls.remove_nukta(text)

        if normalize_quotes:
            text = cls.normalize_quotes(text)

        if normalize_numbers:
            text = cls.normalize_numbers(text)

        if normalize_whitespace:
            text = cls.normalize_whitespace(text)

        return text


# Module-level convenience function
def normalize_hindi(
    text: str,
    form: str = "NFC",
    remove_nukta: bool = True,
) -> str:
    """Normalize Hindi text.

    Args:
        text: Hindi text to normalize
        form: Normalization form (NFC, NFD, NFKC, NFKD)
        remove_nukta: Whether to remove nukta diacritics

    Returns:
        Normalized text
    """
    if form == "NFC":
        text = HindiNormalizer.normalize_nfc(text)
    elif form == "NFD":
        text = HindiNormalizer.normalize_nfd(text)
    elif form == "NFKC":
        text = HindiNormalizer.normalize_nfkc(text)
    elif form == "NFKD":
        text = HindiNormalizer.normalize_nfkd(text)

    if remove_nukta:
        text = HindiNormalizer.remove_nukta(text)

    return text
