"""Tests for single text translation endpoint"""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, AsyncMock

from app.main import app
from app.services.cache import translation_cache
from app.services.indictrans2_engine import indictrans2_engine


client = TestClient(app)


@pytest.fixture
def mock_translate():
    """Mock the indictrans2_engine.translate method"""
    with patch.object(
        indictrans2_engine, "translate", new_callable=AsyncMock
    ) as mock:
        mock.return_value = "अनुवादित पाठ"
        yield mock


@pytest.fixture
def mock_cache():
    """Mock the translation cache"""
    with patch.object(translation_cache, "get", new_callable=AsyncMock) as mock_get:
        with patch.object(translation_cache, "set", new_callable=AsyncMock) as mock_set:
            mock_get.return_value = None
            mock_set.return_value = True
            yield {"get": mock_get, "set": mock_set}


def test_translate_english_to_hindi(mock_translate, mock_cache):
    """Test translating English text to Hindi"""
    response = client.post(
        "/translate/",
        json={
            "text": "Hello world",
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


def test_translate_invalid_source_language():
    """Test translation with invalid source language"""
    response = client.post(
        "/translate/",
        json={
            "text": "Test text",
            "source_language": "xx",  # Invalid
            "target_language": "hi",
        },
    )

    assert response.status_code == 400
    data = response.json()
    assert data["detail"]["error"]["code"] == "INVALID_LANGUAGE"


def test_translate_invalid_target_language():
    """Test translation with invalid target language"""
    response = client.post(
        "/translate/",
        json={
            "text": "Test text",
            "source_language": "en",
            "target_language": "xx",  # Invalid
        },
    )

    assert response.status_code == 400
    data = response.json()
    assert data["detail"]["error"]["code"] == "INVALID_LANGUAGE"


def test_translate_same_language():
    """Test when source and target language are the same"""
    test_text = "Same language test"
    response = client.post(
        "/translate/",
        json={
            "text": test_text,
            "source_language": "en",
            "target_language": "en",
        },
    )

    assert response.status_code == 200
    data = response.json()
    assert data["translated_text"] == test_text
    assert data["cached"] is True  # Returns as-is, considered cached


def test_translate_empty_text():
    """Test with empty text"""
    response = client.post(
        "/translate/",
        json={
            "text": "",
            "source_language": "en",
            "target_language": "hi",
        },
    )

    assert response.status_code == 422


def test_translate_text_too_long():
    """Test with text exceeding max length"""
    long_text = "a" * 10000
    response = client.post(
        "/translate/",
        json={
            "text": long_text,
            "source_language": "en",
            "target_language": "hi",
        },
    )

    assert response.status_code == 422


def test_translate_missing_text():
    """Test with missing text field"""
    response = client.post(
        "/translate/",
        json={
            "source_language": "en",
            "target_language": "hi",
        },
    )

    assert response.status_code == 422  # Validation error


def test_translate_request_id_propagation():
    """Test that X-Request-ID is propagated"""
    request_id = "test-request-id-12345"
    response = client.post(
        "/translate/",
        json={
            "text": "Test",
            "source_language": "en",
            "target_language": "hi",
        },
        headers={"X-Request-ID": request_id},
    )

    assert response.headers.get("X-Request-ID") == request_id


@pytest.mark.parametrize(
    "source_lang,target_lang",
    [
        ("en", "hi"),
        ("en", "bn"),
        ("en", "ta"),
        ("en", "te"),
        ("hi", "en"),
    ],
)
def test_translate_supported_language_pairs(source_lang, target_lang, mock_translate, mock_cache):
    """Test various supported language pairs"""
    response = client.post(
        "/translate/",
        json={
            "text": "Test text",
            "source_language": source_lang,
            "target_language": target_lang,
        },
    )

    assert response.status_code == 200
    data = response.json()
    assert data["source_language"] == source_lang
    assert data["target_language"] == target_lang
