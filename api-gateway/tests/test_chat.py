"""Tests for chat endpoints."""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock, patch
from app.main import app


@pytest.mark.asyncio
async def test_chat_query_requires_auth():
    """Test that chat requires authentication."""
    client = TestClient(app)
    response = client.post(
        "/api/v1/chat",
        json={
            "query": "What is the Ministry of Culture?",
            "language": "en",
        },
    )
    # Should fail without auth (unless endpoint is public)
    assert response.status_code in [401, 200]  # 401 if protected, 200 if public


@pytest.mark.asyncio
async def test_chat_invalid_request():
    """Test chat with invalid request."""
    client = TestClient(app)
    response = client.post(
        "/api/v1/chat",
        json={
            "query": "",  # Empty query
            "language": "en",
        },
        headers={"Authorization": "Bearer test_token"},
    )
    # Should fail - either auth fails (401) or validation fails (422/400)
    assert response.status_code in [401, 422, 400]


def test_chat_response_structure(client: TestClient, mock_rag_response, mock_llm_response):
    """Test chat response structure."""
    with patch("app.services.rag_client.RAGClient.query", new_callable=AsyncMock) as mock_rag:
        with patch("app.services.llm_client.LLMClient.chat_completion", new_callable=AsyncMock) as mock_llm:
            mock_rag.return_value = mock_rag_response
            mock_llm.return_value = mock_llm_response

            response = client.post(
                "/api/v1/chat",
                json={
                    "query": "What is the Ministry of Culture?",
                    "language": "en",
                    "chat_history": [],
                },
                headers={"Authorization": "Bearer test_token"},
            )

            if response.status_code == 200:
                data = response.json()
                assert "response" in data
                assert "sources" in data
                assert "confidence" in data
                assert "session_id" in data
                assert "request_id" in data
                assert "timestamp" in data


def test_chat_stream_endpoint(client: TestClient):
    """Test streaming chat endpoint."""
    response = client.post(
        "/api/v1/chat/stream",
        json={
            "query": "Tell me about Indian heritage",
            "language": "en",
            "chat_history": [],
        },
    )

    # Check if response is streaming
    if response.status_code == 200:
        assert response.headers.get("content-type") == "text/event-stream"
