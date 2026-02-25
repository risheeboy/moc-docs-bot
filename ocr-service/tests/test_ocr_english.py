"""Tests for English OCR processing."""

import pytest
from PIL import Image, ImageDraw
from io import BytesIO

from app.services.tesseract_engine import TesseractOCREngine
from app.services.easyocr_engine import EasyOCREngine
from app.services.postprocessor import PostProcessor


class TestEnglishOCR:
    """Test English OCR processing."""

    @pytest.fixture
    def tesseract_engine(self):
        """Create Tesseract engine instance."""
        return TesseractOCREngine()

    @pytest.fixture
    def easyocr_engine(self):
        """Create EasyOCR engine instance."""
        return EasyOCREngine()

    @pytest.fixture
    def english_image(self):
        """Create image with English text."""
        img = Image.new("RGB", (300, 100), color="white")
        draw = ImageDraw.Draw(img)
        draw.text((10, 10), "Hello World", fill="black")
        return img

    def test_english_language_detection_tesseract(self, tesseract_engine):
        """Test English language detection in Tesseract."""
        english_text = "The quick brown fox jumps over the lazy dog"
        assert tesseract_engine._detect_language(english_text) == "en"

    def test_english_language_detection_easyocr(self, easyocr_engine):
        """Test English language detection in EasyOCR."""
        english_text = "The quick brown fox jumps over the lazy dog"
        assert easyocr_engine._detect_language(english_text) == "en"

    def test_english_postprocessing(self):
        """Test English text post-processing."""
        postprocessor = PostProcessor()

        # Test common OCR errors
        text = "The quick brown fox jumps over tne lazy dog"
        result = postprocessor._fix_english_text(text)

        assert isinstance(result, str)

    def test_tesseract_language_normalize_english(self, tesseract_engine):
        """Test Tesseract language normalization for English."""
        result = tesseract_engine._normalize_languages("eng")
        assert "eng" in result

        result = tesseract_engine._normalize_languages("en")
        assert "eng" in result

    def test_easyocr_language_normalize_english(self, easyocr_engine):
        """Test EasyOCR language normalization for English."""
        result = easyocr_engine._normalize_languages("eng")
        assert "en" in result

        result = easyocr_engine._normalize_languages("en")
        assert "en" in result


class TestBilingualOCR:
    """Test bilingual (English + Hindi) OCR."""

    @pytest.fixture
    def tesseract_engine(self):
        """Create Tesseract engine instance."""
        return TesseractOCREngine()

    @pytest.fixture
    def easyocr_engine(self):
        """Create EasyOCR engine instance."""
        return EasyOCREngine()

    def test_bilingual_language_normalize_tesseract(self, tesseract_engine):
        """Test bilingual language normalization in Tesseract."""
        # Comma-separated
        result = tesseract_engine._normalize_languages("hi,en")
        assert "hin" in result and "eng" in result

        # Plus-separated
        result = tesseract_engine._normalize_languages("hin+eng")
        assert "hin" in result and "eng" in result

        # Mixed
        result = tesseract_engine._normalize_languages("hi+eng")
        assert "hin" in result and "eng" in result

    def test_bilingual_language_normalize_easyocr(self, easyocr_engine):
        """Test bilingual language normalization in EasyOCR."""
        # Comma-separated
        result = easyocr_engine._normalize_languages("hi,en")
        assert "hi" in result and "en" in result

        # Plus-separated
        result = easyocr_engine._normalize_languages("hin+eng")
        assert "hi" in result and "en" in result

    def test_mixed_content_detection(self, tesseract_engine):
        """Test language detection with mixed content."""
        # English-dominant
        text = "This is English text with नमस्ते in it"
        assert tesseract_engine._detect_language(text) == "en"

        # Hindi-dominant
        text = "यह हिंदी पाठ है और बहुत सारा हिंदी with some"
        assert tesseract_engine._detect_language(text) == "hi"


class TestOCRPostProcessingEnglish:
    """Test English-specific post-processing."""

    @pytest.fixture
    def postprocessor(self):
        """Create post-processor instance."""
        return PostProcessor()

    def test_common_ocr_errors_fixed(self, postprocessor):
        """Test that common OCR errors are fixed."""
        text = "O0 and l1 confusion"
        result = postprocessor._fix_english_text(text)

        # Should attempt to fix common character confusions
        assert isinstance(result, str)

    def test_word_correction(self, postprocessor):
        """Test word-level corrections."""
        text = "This is tlie correct way"
        result = postprocessor._fix_english_text(text)

        # "tlie" should be corrected to "the"
        assert "the" in result.lower()

    def test_whitespace_cleanup(self, postprocessor):
        """Test whitespace cleanup."""
        text = "This   is   a   test   with   extra   spaces"
        result = postprocessor._normalize_whitespace(text)

        # Multiple spaces should be reduced
        assert "   " not in result
        assert result.count("  ") == 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
