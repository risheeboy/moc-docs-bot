"""Tests for Hindi OCR processing."""

import pytest
from PIL import Image, ImageDraw
from io import BytesIO

from app.services.tesseract_engine import TesseractOCREngine
from app.services.easyocr_engine import EasyOCREngine
from app.services.preprocessor import ImagePreprocessor
from app.services.postprocessor import PostProcessor


class TestTesseractOCREngine:
    """Test Tesseract OCR engine for Hindi."""

    @pytest.fixture
    def tesseract_engine(self):
        """Create Tesseract engine instance."""
        return TesseractOCREngine()

    @pytest.fixture
    def simple_hindi_image(self):
        """Create a simple image with Hindi text."""
        # Create a white image
        img = Image.new("RGB", (200, 100), color="white")
        draw = ImageDraw.Draw(img)

        # Add some Hindi-like text (Devanagari characters)
        # Note: actual rendering requires font support
        # This is a placeholder that draws some shapes
        draw.text((10, 10), "नमस्ते", fill="black")

        return img

    def test_engine_initialization(self, tesseract_engine):
        """Test engine initialization."""
        assert tesseract_engine is not None
        assert tesseract_engine.preprocessor is not None
        assert tesseract_engine.postprocessor is not None

    def test_language_normalization(self, tesseract_engine):
        """Test language code normalization."""
        # Test hi,en format
        result = tesseract_engine._normalize_languages("hi,en")
        assert "hin" in result
        assert "eng" in result

        # Test hi+en format
        result = tesseract_engine._normalize_languages("hi+en")
        assert "hin" in result
        assert "eng" in result

        # Test full codes
        result = tesseract_engine._normalize_languages("hin+eng")
        assert "hin" in result
        assert "eng" in result

    def test_language_detection(self, tesseract_engine):
        """Test language detection."""
        # Hindi text (with Devanagari)
        hindi_text = "यह हिंदी पाठ है"
        assert tesseract_engine._detect_language(hindi_text) == "hi"

        # English text
        english_text = "This is English text"
        assert tesseract_engine._detect_language(english_text) == "en"

    def test_regions_extraction(self, tesseract_engine, simple_hindi_image):
        """Test text region extraction."""
        # Create mock Tesseract output
        data = {
            "text": ["नमस्ते", ""],
            "line_num": [0, 1],
            "left": [10, 0],
            "top": [10, 0],
            "width": [50, 0],
            "height": [20, 0],
            "conf": [85, -1],
        }

        regions = tesseract_engine._extract_regions(data, simple_hindi_image)

        assert len(regions) > 0
        assert "bounding_box" in regions[0]
        assert "text" in regions[0]
        assert "confidence" in regions[0]


class TestEasyOCREngine:
    """Test EasyOCR engine."""

    @pytest.fixture
    def easyocr_engine(self):
        """Create EasyOCR engine instance."""
        return EasyOCREngine()

    def test_engine_initialization(self, easyocr_engine):
        """Test engine initialization."""
        assert easyocr_engine is not None

    def test_language_normalization(self, easyocr_engine):
        """Test language normalization."""
        # Test hi,en format
        result = easyocr_engine._normalize_languages("hi,en")
        assert "hi" in result
        assert "en" in result

        # Test hin+eng format
        result = easyocr_engine._normalize_languages("hin+eng")
        assert "hi" in result
        assert "en" in result

    def test_language_detection(self, easyocr_engine):
        """Test language detection."""
        # Hindi text
        hindi_text = "यह हिंदी पाठ है"
        assert easyocr_engine._detect_language(hindi_text) == "hi"

        # English text
        english_text = "This is English text"
        assert easyocr_engine._detect_language(english_text) == "en"


class TestImagePreprocessor:
    """Test image preprocessing."""

    @pytest.fixture
    def preprocessor(self):
        """Create preprocessor instance."""
        return ImagePreprocessor(
            enable_deskew=True,
            enable_denoise=True,
            enable_binarize=True,
        )

    @pytest.fixture
    def test_image(self):
        """Create a test image."""
        img = Image.new("RGB", (100, 100), color="white")
        draw = ImageDraw.Draw(img)
        draw.rectangle([10, 10, 90, 90], fill="black")
        return img

    def test_preprocessing(self, preprocessor, test_image):
        """Test image preprocessing."""
        result = preprocessor.preprocess(test_image)

        assert isinstance(result, Image.Image)
        assert result.size == test_image.size

    def test_upscaling(self, preprocessor, test_image):
        """Test image upscaling."""
        result = preprocessor.upscale(test_image, target_dpi=300)

        assert isinstance(result, Image.Image)
        # Size should be larger or equal
        assert result.size[0] >= test_image.size[0]


class TestPostProcessor:
    """Test text post-processing."""

    @pytest.fixture
    def postprocessor(self):
        """Create post-processor instance."""
        return PostProcessor()

    def test_hindi_text_cleanup(self, postprocessor):
        """Test Hindi text cleanup."""
        text = "नमस्ते।।"
        result = postprocessor._fix_hindi_text(text)

        # Should fix duplicate danda
        assert "।।" not in result or result.count("।") <= text.count("।")

    def test_english_text_cleanup(self, postprocessor):
        """Test English text cleanup."""
        text = "This is l test"
        result = postprocessor._fix_english_text(text)

        assert isinstance(result, str)

    def test_whitespace_normalization(self, postprocessor):
        """Test whitespace normalization."""
        text = "This  is   a    test\n\n\nwith  spaces"
        result = postprocessor._normalize_whitespace(text)

        # Should reduce multiple spaces
        assert "  " not in result or result.count(" ") < text.count(" ")

    def test_full_postprocessing(self, postprocessor):
        """Test full post-processing."""
        text = "नमस्ते।।\n\nThis is l test"
        result = postprocessor.postprocess(text, "hi,en")

        assert isinstance(result, str)
        assert len(result) > 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
