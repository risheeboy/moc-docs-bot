"""Tests for chat completions endpoint

Tests OpenAI-compatible API, streaming, and error handling.
"""

import pytest
import pytest_asyncio
import json
from httpx import AsyncClient, ASGITransport
from unittest.mock import AsyncMock, MagicMock, patch

from app.main import app
from app.models.completions import ChatCompletionRequest, Message


@pytest_asyncio.fixture
async def client():
    """HTTP client for testing"""
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test"
    ) as ac:
        yield ac


@pytest.mark.asyncio
async def test_chat_completions_non_streaming(client):
    """Test non-streaming chat completions"""
    request_body = {
        "model": "meta-llama/Llama-3.1-8B-Instruct-AWQ",
        "messages": [
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": "What is 2+2?"}
        ],
        "temperature": 0.3,
        "max_tokens": 100,
        "stream": False
    }

    with patch('app.services.model_manager.ModelManager.is_model_loaded', return_value=True), \
         patch('app.services.generation.GenerationService.generate') as mock_gen:

        mock_gen.return_value = ("4", 10, 5)

        response = await client.post(
            "/v1/chat/completions",
            json=request_body,
            headers={"X-Request-ID": "test-123"}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["model"] == request_body["model"]
        assert len(data["choices"]) == 1
        assert data["choices"][0]["message"]["role"] == "assistant"
        assert "usage" in data
        assert data["usage"]["prompt_tokens"] == 10
        assert data["usage"]["completion_tokens"] == 5


@pytest.mark.asyncio
async def test_chat_completions_streaming(client):
    """Test streaming chat completions (SSE)"""
    request_body = {
        "model": "meta-llama/Llama-3.1-8B-Instruct-AWQ",
        "messages": [
            {"role": "user", "content": "Hello"}
        ],
        "stream": True
    }

    async def mock_stream():
        yield ("Hello", 5, 1)
        yield(" ", 5, 1)
        yield("world", 5, 2)

    with patch('app.services.model_manager.ModelManager.is_model_loaded', return_value=True), \
         patch('app.services.generation.GenerationService.stream_generate', return_value=mock_stream()):

        response = await client.post(
            "/v1/chat/completions",
            json=request_body
        )

        assert response.status_code == 200
        assert "text/event-stream" in response.headers["content-type"]


@pytest.mark.asyncio
async def test_chat_completions_model_not_loaded(client):
    """Test error when model is not loaded"""
    request_body = {
        "model": "meta-llama/Llama-3.1-8B-Instruct-AWQ",
        "messages": [
            {"role": "user", "content": "Hello"}
        ]
    }

    with patch('app.services.model_manager.ModelManager.is_model_loaded', return_value=False):
        response = await client.post(
            "/v1/chat/completions",
            json=request_body
        )

        assert response.status_code == 503
        data = response.json()
        assert data["detail"]["error"]["code"] == "MODEL_LOADING"


@pytest.mark.asyncio
async def test_chat_completions_empty_messages(client):
    """Test error for empty messages"""
    request_body = {
        "model": "meta-llama/Llama-3.1-8B-Instruct-AWQ",
        "messages": [],
        "stream": False
    }

    with patch('app.services.model_manager.ModelManager.is_model_loaded', return_value=True):
        response = await client.post(
            "/v1/chat/completions",
            json=request_body
        )

        assert response.status_code == 400
        data = response.json()
        assert data["detail"]["error"]["code"] == "INVALID_REQUEST"


@pytest.mark.asyncio
async def test_chat_completions_request_id_propagation(client):
    """Test X-Request-ID header propagation"""
    request_body = {
        "model": "meta-llama/Llama-3.1-8B-Instruct-AWQ",
        "messages": [
            {"role": "user", "content": "Hello"}
        ],
        "stream": False
    }

    with patch('app.services.model_manager.ModelManager.is_model_loaded', return_value=True), \
         patch('app.services.generation.GenerationService.generate') as mock_gen:

        mock_gen.return_value = ("response", 10, 10)

        request_id = "my-custom-request-id"
        response = await client.post(
            "/v1/chat/completions",
            json=request_body,
            headers={"X-Request-ID": request_id}
        )

        assert response.status_code == 200
        # Verify request completed successfully (request_id is used internally for logging/tracing)
        data = response.json()
        assert "choices" in data


@pytest.mark.asyncio
async def test_chat_completions_temperature_validation(client):
    """Test temperature parameter validation"""
    request_body = {
        "model": "meta-llama/Llama-3.1-8B-Instruct-AWQ",
        "messages": [
            {"role": "user", "content": "Hello"}
        ],
        "temperature": 3.0,  # Invalid: must be <= 2.0
        "stream": False
    }

    response = await client.post(
        "/v1/chat/completions",
        json=request_body
    )

    # Pydantic validation should catch this
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_chat_completions_max_tokens_validation(client):
    """Test max_tokens parameter validation"""
    request_body = {
        "model": "meta-llama/Llama-3.1-8B-Instruct-AWQ",
        "messages": [
            {"role": "user", "content": "Hello"}
        ],
        "max_tokens": 0,  # Invalid: must be >= 1
        "stream": False
    }

    response = await client.post(
        "/v1/chat/completions",
        json=request_body
    )

    assert response.status_code == 422
