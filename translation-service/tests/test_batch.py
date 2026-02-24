"""Tests for batch translation endpoint"""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, AsyncMock

from app.main import app
from app.services.cache import translation_cache
from app.services.indictrans2_engine import indictrans2_engine


client = TestClient(app)


@pytest.fixture
def mock_batch_translate():
    """Mock the indictrans2_engine.translate_batch method"""
    with patch.object(
        indictrans2_engine, "translate_batch", new_callable=AsyncMock
    ) as mock:
        mock.return_value = ["अनुवाद 1", "अनुवाद 2", "अनुवाद 3"]
        yield mock


@pytest.fixture
def mock_cache():
    """Mock the translation cache"""
    with patch.object(translation_cache, "get", new_callable=AsyncMock) as mock_get:
        with patch.object(translation_cache, "set", new_callable=AsyncMock) as mock_set:
            mock_get.return_value = None
            mock_set.return_value = True
            yield {"get": mock_get, "set": mock_set}


def test_batch_translate_basic(mock_batch_translate, mock_cache):
    """Test basic batch translation"""
    response = client.post(
        "/translate/batch",
        json={
            "texts": ["Hello", "World", "Test"],
            "source_language": "en",
            "target_language": "hi",
        },
    )

    assert response.status_code == 200
    data = response.json()
    assert data["source_language"] == "en"
    assert data["target_language"] == "hi"
    assert len(data["translations"]) == 3
    assert all("text" in t and "cached" in t for t in data["translations"])


def test_batch_translate_empty_list():
    """Test batch translation with empty list"""
    response = client.post(
        "/translate/batch",
        json={
            "texts": [],
            "source_language": "en",
            "target_language": "hi",
        },
    )

    assert response.status_code == 400


def test_batch_translate_exceeds_max_size():
    """Test batch translation exceeding max batch size"""
    texts = ["text"] * 101  # Exceeds default max of 100
    response = client.post(
        "/translate/batch",
        json={
            "texts": texts,
            "source_language": "en",
            "target_language": "hi",
        },
    )

    assert response.status_code == 400
    data = response.json()
    assert data["error"]["code"] == "INVALID_REQUEST"


def test_batch_translate_invalid_source_language():
    """Test batch translation with invalid source language"""
    response = client.post(
        "/translate/batch",
        json={
            "texts": ["text1", "text2"],
            "source_language": "xx",  # Invalid
            "target_language": "hi",
        },
    )

    assert response.status_code == 400
    data = response.json()
    assert data["error"]["code"] == "INVALID_LANGUAGE"


def test_batch_translate_invalid_target_language():
    """Test batch translation with invalid target language"""
    response = client.post(
        "/translate/batch",
        json={
            "texts": ["text1", "text2"],
            "source_language": "en",
            "target_language": "xx",  # Invalid
        },
    )

    assert response.status_code == 400
    data = response.json()
    assert data["error"]["code"] == "INVALID_LANGUAGE"


def test_batch_translate_same_language():
    """Test batch translation when source and target are same"""
    texts = ["text1", "text2", "text3"]
    response = client.post(
        "/translate/batch",
        json={
            "texts": texts,
            "source_language": "en",
            "target_language": "en",
        },
    )

    assert response.status_code == 200
    data = response.json()
    assert len(data["translations"]) == 3
    for i, translation in enumerate(data["translations"]):
        assert translation["text"] == texts[i]
        assert translation["cached"] is True


def test_batch_translate_single_item(mock_batch_translate, mock_cache):
    """Test batch translation with single item"""
    response = client.post(
        "/translate/batch",
        json={
            "texts": ["Hello"],
            "source_language": "en",
            "target_language": "hi",
        },
    )

    assert response.status_code == 200
    data = response.json()
    assert len(data["translations"]) == 1


def test_batch_translate_request_id_propagation():
    """Test that X-Request-ID is propagated in batch translation"""
    request_id = "test-batch-request-id"
    response = client.post(
        "/translate/batch",
        json={
            "texts": ["Hello", "World"],
            "source_language": "en",
            "target_language": "hi",
        },
        headers={"X-Request-ID": request_id},
    )

    assert response.headers.get("X-Request-ID") == request_id


def test_batch_translate_missing_texts():
    """Test batch translation with missing texts field"""
    response = client.post(
        "/translate/batch",
        json={
            "source_language": "en",
            "target_language": "hi",
        },
    )

    assert response.status_code == 422  # Validation error


def test_batch_translate_missing_language():
    """Test batch translation with missing language fields"""
    response = client.post(
        "/translate/batch",
        json={
            "texts": ["Hello", "World"],
            "source_language": "en",
        },
    )

    assert response.status_code == 422  # Validation error


@pytest.mark.parametrize(
    "batch_size",
    [1, 5, 10, 50, 100],
)
def test_batch_translate_various_sizes(batch_size, mock_batch_translate, mock_cache):
    """Test batch translation with various batch sizes"""
    texts = [f"text{i}" for i in range(batch_size)]
    response = client.post(
        "/translate/batch",
        json={
            "texts": texts,
            "source_language": "en",
            "target_language": "hi",
        },
    )

    assert response.status_code == 200
    data = response.json()
    assert len(data["translations"]) == batch_size
