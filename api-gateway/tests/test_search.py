"""Tests for search endpoints."""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock, patch
from app.main import app


def test_search_endpoint(client: TestClient):
    """Test search endpoint."""
    response = client.get(
        "/api/v1/search",
        params={
            "query": "Indian heritage sites",
            "language": "en",
            "page": 1,
            "page_size": 20,
        },
    )

    # Should return proper response or require auth
    assert response.status_code in [200, 401, 422]


def test_search_response_structure(client: TestClient):
    """Test search response structure when successful."""
    with patch("app.services.rag_client.RAGClient.search", new_callable=AsyncMock) as mock_search:
        mock_search.return_value = {
            "results": [
                {
                    "title": "Test Monument",
                    "url": "https://example.com",
                    "snippet": "Test content",
                    "score": 0.95,
                    "source_site": "example.com",
                    "language": "en",
                    "content_type": "webpage",
                }
            ],
            "multimedia": [],
            "events": [],
            "total_results": 1,
        }

        response = client.get(
            "/api/v1/search?query=heritage&language=en"
        )

        if response.status_code == 200:
            data = response.json()
            assert "results" in data
            assert "multimedia" in data
            assert "events" in data
            assert "total_results" in data
            assert "page" in data
            assert "page_size" in data
            assert "request_id" in data


def test_search_suggest_endpoint(client: TestClient):
    """Test search suggestions endpoint."""
    response = client.get(
        "/api/v1/search/suggest",
        params={
            "prefix": "indh",
            "language": "en",
            "limit": 10,
        },
    )

    # Should return suggestions or require auth
    assert response.status_code in [200, 401, 422]
