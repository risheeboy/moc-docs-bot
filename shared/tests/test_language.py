"""Tests for Language enum."""

import pytest
from rag_shared.models.language import Language


def test_language_enum_values():
    """Test that all language codes are defined."""
    assert Language.HI.value == "hi"
    assert Language.EN.value == "en"
    assert Language.BN.value == "bn"
    assert Language.TE.value == "te"
    assert Language.MR.value == "mr"
    assert Language.TA.value == "ta"
    assert Language.UR.value == "ur"
    assert Language.GU.value == "gu"
    assert Language.KN.value == "kn"
    assert Language.ML.value == "ml"
    assert Language.OR.value == "or"
    assert Language.PA.value == "pa"


def test_language_validate():
    """Test language validation."""
    assert Language.validate("hi") == Language.HI
    assert Language.validate("en") == Language.EN
    assert Language.validate("bn") == Language.BN


def test_language_validate_invalid():
    """Test validation fails for invalid code."""
    with pytest.raises(ValueError):
        Language.validate("invalid")


def test_language_get_all_codes():
    """Test getting all language codes."""
    codes = Language.get_all_codes()
    assert "hi" in codes
    assert "en" in codes
    assert len(codes) == 23  # 22 Indian + English


def test_language_script():
    """Test language script property."""
    assert Language.HI.script == "Devanagari"
    assert Language.EN.script == "Latin"
    assert Language.TA.script == "Tamil"
    assert Language.UR.script == "Perso-Arabic"


def test_language_name_english():
    """Test language English name."""
    assert Language.HI.name_english == "Hindi"
    assert Language.EN.name_english == "English"
    assert Language.BN.name_english == "Bengali"


def test_language_is_indic():
    """Test Indic script detection."""
    assert Language.HI.is_indic is True
    assert Language.EN.is_indic is False
    assert Language.TA.is_indic is True
