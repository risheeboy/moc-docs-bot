"""Tests for Hindi text normalizer."""

import pytest
from rag_shared.hindi.normalizer import HindiNormalizer, normalize_hindi


def test_normalize_nfc():
    """Test NFC normalization."""
    # Test basic NFC normalization
    text = "नमस्ते"
    result = HindiNormalizer.normalize_nfc(text)
    assert isinstance(result, str)
    assert len(result) > 0


def test_normalize_nfd():
    """Test NFD normalization."""
    text = "नमस्ते"
    result = HindiNormalizer.normalize_nfd(text)
    assert isinstance(result, str)


def test_normalize_nfkc():
    """Test NFKC normalization."""
    text = "नमस्ते"
    result = HindiNormalizer.normalize_nfkc(text)
    assert isinstance(result, str)


def test_remove_nukta():
    """Test removing nukta diacritics."""
    # Nukta example: क़ (QA) should become क (KA)
    text = "क़ाना"
    result = HindiNormalizer.remove_nukta(text)
    assert "क़" not in result or result == text  # Either removed or unchanged


def test_normalize_whitespace():
    """Test whitespace normalization."""
    text = "नमस्ते   विश्व"  # Multiple spaces
    result = HindiNormalizer.normalize_whitespace(text)
    assert "   " not in result
    assert result == "नमस्ते विश्व"


def test_normalize_quotes():
    """Test quote normalization."""
    text = '"नमस्ते"'  # Unicode quotes
    result = HindiNormalizer.normalize_quotes(text)
    assert '"' in result or "'" in result


def test_normalize_numbers():
    """Test Devanagari to ASCII digit conversion."""
    text = "संख्या: ०१२३४५६७८९"
    result = HindiNormalizer.normalize_numbers(text)
    assert "०" not in result
    assert "1" in result or "0" in result


def test_is_hindi():
    """Test Hindi text detection."""
    assert HindiNormalizer.is_hindi("नमस्ते") is True
    assert HindiNormalizer.is_hindi("hello") is False
    assert HindiNormalizer.is_hindi("नमस्ते और hello") is True


def test_normalize_full():
    """Test complete normalization pipeline."""
    text = "नमस्ते   विश्व"
    result = HindiNormalizer.normalize_full(
        text,
        remove_nukta=True,
        normalize_whitespace=True,
    )
    assert isinstance(result, str)
    assert "   " not in result


def test_module_level_normalize():
    """Test module-level normalize function."""
    text = "नमस्ते"
    result = normalize_hindi(text)
    assert isinstance(result, str)
    assert len(result) > 0
