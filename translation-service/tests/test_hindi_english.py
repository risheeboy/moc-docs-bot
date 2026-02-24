"""Integration tests for Hindi-English translation"""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, AsyncMock

from app.main import app
from app.services.cache import translation_cache
from app.services.indictrans2_engine import indictrans2_engine


client = TestClient(app)


@pytest.fixture
def mock_hindi_english_translate():
    """Mock translation for Hindi-English language pair"""
    async def mock_translate(text, source_language, target_language):
        # Simple mock translations for testing
        translations = {
            "en_hi": {
                "Ministry of Culture promotes Indian heritage": "संस्कृति मंत्रालय भारतीय विरासत को बढ़ावा देता है",
                "Hello": "नमस्ते",
                "Good morning": "सुप्रभात",
            },
            "hi_en": {
                "नमस्ते": "Hello",
                "भारतीय संस्कृति": "Indian culture",
                "सुप्रभात": "Good morning",
            },
        }
        key = f"{source_language}_{target_language}"
        return translations.get(key, {}).get(text, f"[translated: {text}]")

    with patch.object(
        indictrans2_engine, "translate", new_callable=AsyncMock
    ) as mock:
        mock.side_effect = mock_translate
        yield mock


@pytest.fixture
def mock_cache():
    """Mock the translation cache"""
    with patch.object(translation_cache, "get", new_callable=AsyncMock) as mock_get:
        with patch.object(translation_cache, "set", new_callable=AsyncMock) as mock_set:
            mock_get.return_value = None
            mock_set.return_value = True
            yield {"get": mock_get, "set": mock_set}


def test_english_to_hindi_translation(mock_hindi_english_translate, mock_cache):
    """Test English to Hindi translation"""
    response = client.post(
        "/translate/",
        json={
            "text": "Hello",
            "source_language": "en",
            "target_language": "hi",
        },
    )

    assert response.status_code == 200
    data = response.json()
    assert data["source_language"] == "en"
    assert data["target_language"] == "hi"
    assert "translated_text" in data
    assert data["cached"] is False


def test_hindi_to_english_translation(mock_hindi_english_translate, mock_cache):
    """Test Hindi to English translation"""
    response = client.post(
        "/translate/",
        json={
            "text": "नमस्ते",
            "source_language": "hi",
            "target_language": "en",
        },
    )

    assert response.status_code == 200
    data = response.json()
    assert data["source_language"] == "hi"
    assert data["target_language"] == "en"
    assert "translated_text" in data
    assert data["cached"] is False


def test_ministry_of_culture_translation(mock_hindi_english_translate, mock_cache):
    """Test translating Ministry of Culture related text"""
    response = client.post(
        "/translate/",
        json={
            "text": "Ministry of Culture promotes Indian heritage",
            "source_language": "en",
            "target_language": "hi",
        },
    )

    assert response.status_code == 200
    data = response.json()
    assert data["source_language"] == "en"
    assert data["target_language"] == "hi"
    assert len(data["translated_text"]) > 0


def test_long_hindi_english_text(mock_hindi_english_translate, mock_cache):
    """Test with longer Hindi-English text"""
    long_text = "The Ministry of Culture of the Government of India is responsible for preservation and promotion of Indian heritage. " * 3

    response = client.post(
        "/translate/",
        json={
            "text": long_text,
            "source_language": "en",
            "target_language": "hi",
        },
    )

    assert response.status_code == 200
    data = response.json()
    assert data["source_language"] == "en"
    assert data["target_language"] == "hi"
    assert len(data["translated_text"]) > 0


def test_hindi_english_batch_translation(mock_hindi_english_translate, mock_cache):
    """Test batch translation of Hindi and English texts"""
    with patch.object(
        indictrans2_engine, "translate_batch", new_callable=AsyncMock
    ) as mock_batch:
        async def mock_batch_translate(texts, source_language, target_language):
            return [f"[translated: {t}]" for t in texts]

        mock_batch.side_effect = mock_batch_translate

        response = client.post(
            "/translate/batch",
            json={
                "texts": ["Hello", "World", "India"],
                "source_language": "en",
                "target_language": "hi",
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert len(data["translations"]) == 3
        assert all("text" in t for t in data["translations"])


def test_detect_hindi_language():
    """Test detecting Hindi language"""
    response = client.post(
        "/detect",
        json={
            "text": "यह हिंदी में लिखा गया है",
        },
    )

    assert response.status_code == 200
    data = response.json()
    assert "language" in data
    assert "confidence" in data
    assert "script" in data
    assert 0 <= data["confidence"] <= 1


def test_detect_english_language():
    """Test detecting English language"""
    response = client.post(
        "/detect",
        json={
            "text": "This is written in English",
        },
    )

    assert response.status_code == 200
    data = response.json()
    assert "language" in data
    assert "confidence" in data
    assert "script" in data
    assert 0 <= data["confidence"] <= 1


def test_round_trip_translation(mock_hindi_english_translate, mock_cache):
    """Test round-trip translation (en -> hi -> en)"""
    original_text = "Hello world"

    # First translation: en -> hi
    response1 = client.post(
        "/translate/",
        json={
            "text": original_text,
            "source_language": "en",
            "target_language": "hi",
        },
    )
    assert response1.status_code == 200
    hindi_text = response1.json()["translated_text"]

    # Second translation: hi -> en
    response2 = client.post(
        "/translate/",
        json={
            "text": hindi_text,
            "source_language": "hi",
            "target_language": "en",
        },
    )
    assert response2.status_code == 200
    # Note: Due to nature of machine translation, exact match is not guaranteed
    assert len(response2.json()["translated_text"]) > 0
