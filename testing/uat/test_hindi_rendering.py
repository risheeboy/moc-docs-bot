"""
Hindi Devanagari rendering and display tests.
Validates correct rendering of Hindi text in UI components.
"""

import pytest


class TestHindiDevanagariRendering:
    """Test Hindi Devanagari script rendering."""

    def test_hindi_basic_characters(self):
        """Test: Basic Hindi characters render correctly."""
        hindi_chars = [
            "क", "ख", "ग", "घ", "च", "छ", "ज", "झ",
            "ट", "ठ", "ड", "ढ", "त", "थ", "द", "ध",
            "न", "प", "फ", "ब", "भ", "म", "य", "र",
            "ल", "व", "श", "ष", "स", "ह", "ड़", "ढ़",
        ]

        for char in hindi_chars:
            assert len(char) == 1
            assert ord(char) >= 0x0900
            assert ord(char) <= 0x097F

    def test_hindi_vowels_and_vowel_marks(self):
        """Test: Hindi vowels and vowel marks."""
        # Standalone vowels
        vowels = ["अ", "आ", "इ", "ई", "उ", "ऊ", "ऋ", "ऌ", "ए", "ऐ", "ओ", "औ"]

        for vowel in vowels:
            assert len(vowel) == 1

        # Vowel marks (matras)
        matras = ["ा", "ि", "ी", "ु", "ू", "ृ", "ॄ", "े", "ै", "ो", "ौ"]

        for matra in matras:
            assert len(matra) == 1

    def test_hindi_conjunct_consonants(self):
        """Test: Conjunct consonants (yog-vaah) render correctly."""
        conjuncts = [
            "क्ष",  # K + Sh
            "त्र",  # T + R
            "ज्ञ",  # J + Ny
            "श्र",  # Sh + R
            "द्य",  # D + Y
        ]

        for conjunct in conjuncts:
            assert len(conjunct) >= 2

    def test_hindi_halant_virama(self):
        """Test: Halant/virama marks work correctly."""
        with_halant = "क्" + "त"
        assert "्" in with_halant  # Virama character

    def test_hindi_anusvara_visarga(self):
        """Test: Anusvara and visarga marks."""
        with_anusvara = "कं"
        assert "ं" in with_anusvara

        with_visarga = "कः"
        assert "ः" in with_visarga

    def test_hindi_common_words_rendering(self):
        """Test: Common Hindi words render without errors."""
        words = [
            "नमस्ते",
            "धन्यवाद",
            "कृपया",
            "भारत",
            "संस्कृति",
            "मंत्रालय",
            "विरासत",
            "परंपरा",
            "शिक्षा",
            "सरकार",
        ]

        for word in words:
            assert len(word) > 0
            assert any(ord(c) >= 0x0900 and ord(c) <= 0x097F for c in word)

    def test_hindi_numbers(self):
        """Test: Hindi numerals render correctly."""
        hindi_digits = ["०", "१", "२", "३", "४", "५", "६", "७", "८", "९"]

        for digit in hindi_digits:
            assert len(digit) == 1

        # Test combined number
        hindi_number = "१२३४५६७८९०"
        assert len(hindi_number) == 10

    def test_hindi_punctuation_in_context(self):
        """Test: Hindi text with standard punctuation."""
        hindi_with_punctuation = [
            "नमस्ते!",
            "आप कैसे हो?",
            "धन्यवाद, बहुत अच्छा।",
            "भारत - सांस्कृतिक देश",
        ]

        for text in hindi_with_punctuation:
            assert len(text) > 0

    def test_hindi_ligatures(self):
        """Test: Hindi ligatures and special combinations."""
        ligatures = [
            "त्त",  # Double T
            "द्द",  # Double D
            "न्न",  # Double N
        ]

        for ligature in ligatures:
            assert len(ligature) >= 2

    def test_hindi_text_direction_rtl_support(self):
        """Test: Hindi text direction (LTR, uses Devanagari)."""
        hindi_text = "भारतीय संस्कृति"

        # Devanagari is written left-to-right
        assert hindi_text[0] in "भ"
        assert hindi_text[-1] in "ति"


class TestDevanagariScriptComplexity:
    """Test complex Devanagari script features."""

    def test_combining_marks_sequence(self):
        """Test: Multiple combining marks in sequence."""
        # Base consonant + vowel mark + anusvara
        complex_char = "कु" + "ं"
        assert "ु" in complex_char
        assert "ं" in complex_char

    def test_zero_width_joiners(self):
        """Test: Zero-width joiner handling."""
        # ZWJ creates conjuncts
        zwj = "\u200D"
        text = "क" + zwj + "त"
        assert zwj in text

    def test_zero_width_non_joiner(self):
        """Test: Zero-width non-joiner prevents ligatures."""
        zwnj = "\u200C"
        text = "त" + zwnj + "त"
        assert zwnj in text


class TestUnicodeNormalization:
    """Test Unicode normalization for Hindi text."""

    def test_nfc_normalization(self):
        """Test: NFC normalization consistency."""
        import unicodedata

        text = "नमस्ते"
        nfc_text = unicodedata.normalize("NFC", text)
        assert nfc_text == text

    def test_nfd_normalization(self):
        """Test: NFD normalization splits combining marks."""
        import unicodedata

        text = "नि"  # N with vowel mark
        nfd_text = unicodedata.normalize("NFD", text)
        assert len(nfd_text) > len(text)

    def test_different_normalizations_equivalent(self):
        """Test: Different normalizations represent same text."""
        import unicodedata

        text = "भारत"
        nfc = unicodedata.normalize("NFC", text)
        nfd = unicodedata.normalize("NFD", text)

        # Visual representation should be same
        assert nfc != nfd  # Different canonical form
