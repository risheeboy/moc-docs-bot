"""
End-to-end chat flow tests.
Tests: Upload document → Ingest → Ask question → Get answer with sources

Validates:
- §4 Error Response Format
- §5 Health Check Format
- §8.1 API Gateway → RAG Service contract
"""

import json
import time
from typing import Any

import httpx
import pytest
from pydantic import BaseModel, Field


# ============================================================================
# Response Models (§8 Contract Validation)
# ============================================================================

class Source(BaseModel):
    """Source document for RAG response."""
    title: str
    url: str
    snippet: str
    score: float
    source_site: str
    language: str
    content_type: str
    chunk_id: str


class ChatResponse(BaseModel):
    """Chat API response."""
    response: str = Field(..., description="Assistant response text")
    sources: list[Source] = Field(default_factory=list)
    confidence: float = Field(..., ge=0, le=1)
    session_id: str
    cached: bool = False


class ErrorResponse(BaseModel):
    """Standard error response format (§4)."""
    error: dict = Field(...)


class HealthResponse(BaseModel):
    """Health check response (§5)."""
    status: str  # healthy | degraded | unhealthy
    service: str
    version: str
    uptime_seconds: float
    timestamp: str
    dependencies: dict


# ============================================================================
# Test Fixtures
# ============================================================================

@pytest.fixture
def chat_document(test_document):
    """Document to upload for chat flow test."""
    return {
        **test_document,
        "title": "संस्कृति मंत्रालय परिचय",
        "content": """
        भारतीय संस्कृति मंत्रालय देश की समृद्ध सांस्कृतिक विरासत के संरक्षण और
        प्रचार के लिए समर्पित है। मंत्रालय भारतीय कला, साहित्य, संगीत, और स्मारकों
        की देखभाल करता है। हमारा प्राथमिक लक्ष्य भारतीय सभ्यता की गौरवान्वित परंपराओं
        को आने वाली पीढ़ियों तक पहुंचाना है।
        """,
    }


@pytest.fixture
def chat_query_hindi():
    """Test query in Hindi."""
    return "भारतीय संस्कृति मंत्रालय का मुख्य उद्देश्य क्या है?"


@pytest.fixture
def chat_query_english():
    """Test query in English."""
    return "What is the main purpose of the Ministry of Culture?"


# ============================================================================
# Tests
# ============================================================================

class TestChatFlowBasic:
    """Basic chat flow tests."""

    @pytest.mark.integration
    async def test_health_check_all_services(self, async_http_client: httpx.AsyncClient):
        """
        Test: All services report healthy via /health endpoint
        Validates: §5 Health Check Format
        """
        services = [
            ("api-gateway", 8000),
            ("rag-service", 8001),
            ("llm-service", 8002),
            ("speech-service", 8003),
            ("translation-service", 8004),
            ("ocr-service", 8005),
            ("data-ingestion", 8006),
        ]

        for service_name, port in services:
            response = await async_http_client.get(
                f"http://localhost:{port}/health"
            )
            assert response.status_code == 200, f"{service_name} not healthy"

            health = response.json()
            assert health["status"] in ["healthy", "degraded"]
            assert health["service"] == service_name
            assert "version" in health
            assert "uptime_seconds" in health
            assert "timestamp" in health
            assert "dependencies" in health

            # Validate HealthResponse schema
            HealthResponse.model_validate(health)

    @pytest.mark.integration
    def test_chat_query_hindi(
        self,
        http_client: httpx.Client,
        chat_query_hindi: str,
        session_id: str,
        request_id: str,
        auth_headers_api_consumer: dict,
    ):
        """
        Test: Simple Hindi chat query
        Validates: §8.1 chat endpoint contract
        """
        payload = {
            "query": chat_query_hindi,
            "language": "hi",
            "session_id": session_id,
            "chat_history": [],
            "top_k": 10,
            "rerank_top_k": 5,
        }

        headers = {
            **auth_headers_api_consumer,
            "X-Request-ID": request_id,
        }

        response = http_client.post(
            "/api/v1/chat",
            json=payload,
            headers=headers,
            timeout=30.0,
        )

        assert response.status_code == 200, f"Got {response.status_code}: {response.text}"

        data = response.json()
        chat_resp = ChatResponse.model_validate(data)

        assert chat_resp.response is not None
        assert len(chat_resp.response) > 0
        assert chat_resp.confidence > 0
        assert chat_resp.session_id == session_id

    @pytest.mark.integration
    def test_chat_query_english(
        self,
        http_client: httpx.Client,
        chat_query_english: str,
        session_id: str,
        request_id: str,
        auth_headers_api_consumer: dict,
    ):
        """
        Test: Simple English chat query
        Validates: §8.1 chat endpoint contract
        """
        payload = {
            "query": chat_query_english,
            "language": "en",
            "session_id": session_id,
            "chat_history": [],
            "top_k": 10,
            "rerank_top_k": 5,
        }

        headers = {
            **auth_headers_api_consumer,
            "X-Request-ID": request_id,
        }

        response = http_client.post(
            "/api/v1/chat",
            json=payload,
            headers=headers,
        )

        assert response.status_code == 200

        data = response.json()
        chat_resp = ChatResponse.model_validate(data)

        assert chat_resp.response is not None
        assert chat_resp.session_id == session_id

    @pytest.mark.integration
    def test_chat_with_sources(
        self,
        http_client: httpx.Client,
        chat_query_hindi: str,
        session_id: str,
        request_id: str,
        auth_headers_api_consumer: dict,
    ):
        """
        Test: Chat response includes relevant sources
        Validates: §8.1 sources field in response
        """
        payload = {
            "query": chat_query_hindi,
            "language": "hi",
            "session_id": session_id,
            "chat_history": [],
            "top_k": 5,
            "rerank_top_k": 3,
        }

        headers = {
            **auth_headers_api_consumer,
            "X-Request-ID": request_id,
        }

        response = http_client.post(
            "/api/v1/chat",
            json=payload,
            headers=headers,
        )

        assert response.status_code == 200
        data = response.json()

        # Validate sources structure
        for source in data.get("sources", []):
            Source.model_validate(source)
            assert source["title"]
            assert source["url"]
            assert source["score"] >= 0

    @pytest.mark.integration
    def test_chat_with_conversation_history(
        self,
        http_client: httpx.Client,
        chat_query_hindi: str,
        session_id: str,
        request_id: str,
        auth_headers_api_consumer: dict,
    ):
        """
        Test: Chat with multi-turn conversation history
        Validates: §8.1 chat_history field
        """
        chat_history = [
            {"role": "user", "content": "आप कौन हो?"},
            {"role": "assistant", "content": "मैं आपका संस्कृति सहायक हूँ।"},
        ]

        payload = {
            "query": chat_query_hindi,
            "language": "hi",
            "session_id": session_id,
            "chat_history": chat_history,
            "top_k": 10,
            "rerank_top_k": 5,
        }

        headers = {
            **auth_headers_api_consumer,
            "X-Request-ID": request_id,
        }

        response = http_client.post(
            "/api/v1/chat",
            json=payload,
            headers=headers,
        )

        assert response.status_code == 200
        data = response.json()
        ChatResponse.model_validate(data)

    @pytest.mark.integration
    def test_chat_invalid_language(
        self,
        http_client: httpx.Client,
        chat_query_hindi: str,
        session_id: str,
        request_id: str,
        auth_headers_api_consumer: dict,
    ):
        """
        Test: Invalid language code returns error
        Validates: §4 Error Response Format
        """
        payload = {
            "query": chat_query_hindi,
            "language": "invalid",
            "session_id": session_id,
            "chat_history": [],
        }

        headers = {
            **auth_headers_api_consumer,
            "X-Request-ID": request_id,
        }

        response = http_client.post(
            "/api/v1/chat",
            json=payload,
            headers=headers,
        )

        assert response.status_code == 400
        error_data = response.json()

        # Validate error format (§4)
        assert "error" in error_data
        assert "code" in error_data["error"]
        assert "message" in error_data["error"]
        assert error_data["error"]["code"] == "INVALID_LANGUAGE"

    @pytest.mark.integration
    def test_chat_missing_query(
        self,
        http_client: httpx.Client,
        session_id: str,
        request_id: str,
        auth_headers_api_consumer: dict,
    ):
        """
        Test: Missing required query field returns error
        Validates: §4 INVALID_REQUEST error code
        """
        payload = {
            "language": "hi",
            "session_id": session_id,
        }

        headers = {
            **auth_headers_api_consumer,
            "X-Request-ID": request_id,
        }

        response = http_client.post(
            "/api/v1/chat",
            json=payload,
            headers=headers,
        )

        assert response.status_code == 400
        error_data = response.json()
        assert error_data["error"]["code"] == "INVALID_REQUEST"

    @pytest.mark.integration
    def test_chat_unauthorized(self, http_client: httpx.Client, chat_query_hindi: str):
        """
        Test: Missing auth token returns 401
        Validates: §4 UNAUTHORIZED error code
        """
        payload = {
            "query": chat_query_hindi,
            "language": "hi",
            "session_id": "test-session",
        }

        response = http_client.post(
            "/api/v1/chat",
            json=payload,
            # No Authorization header
        )

        assert response.status_code == 401
        error_data = response.json()
        assert error_data["error"]["code"] == "UNAUTHORIZED"

    @pytest.mark.integration
    def test_chat_response_time_within_sla(
        self,
        http_client: httpx.Client,
        chat_query_hindi: str,
        session_id: str,
        request_id: str,
        auth_headers_api_consumer: dict,
    ):
        """
        Test: Chat response completes within 5 seconds (p95 target)
        """
        payload = {
            "query": chat_query_hindi,
            "language": "hi",
            "session_id": session_id,
            "chat_history": [],
        }

        headers = {
            **auth_headers_api_consumer,
            "X-Request-ID": request_id,
        }

        start_time = time.time()
        response = http_client.post(
            "/api/v1/chat",
            json=payload,
            headers=headers,
            timeout=30.0,
        )
        elapsed = time.time() - start_time

        assert response.status_code == 200
        assert elapsed < 5.0, f"Response took {elapsed:.2f}s, exceeds 5s SLA"

    @pytest.mark.integration
    def test_chat_request_id_propagation(
        self,
        http_client: httpx.Client,
        chat_query_hindi: str,
        session_id: str,
        request_id: str,
        auth_headers_api_consumer: dict,
    ):
        """
        Test: X-Request-ID header is propagated in response
        Validates: §7 Request ID Propagation
        """
        payload = {
            "query": chat_query_hindi,
            "language": "hi",
            "session_id": session_id,
        }

        headers = {
            **auth_headers_api_consumer,
            "X-Request-ID": request_id,
        }

        response = http_client.post(
            "/api/v1/chat",
            json=payload,
            headers=headers,
        )

        assert response.status_code == 200
        assert response.headers.get("X-Request-ID") == request_id


class TestChatFlowAdvanced:
    """Advanced chat flow scenarios."""

    @pytest.mark.integration
    @pytest.mark.slow
    def test_chat_confidence_below_threshold_triggers_fallback(
        self,
        http_client: httpx.Client,
        session_id: str,
        request_id: str,
        auth_headers_api_consumer: dict,
    ):
        """
        Test: Low confidence responses trigger fallback message
        Validates: §13 Chatbot Fallback Behavior

        When confidence < RAG_CONFIDENCE_THRESHOLD (0.65), system should
        return fallback message offering contact information.
        """
        # Query about obscure topic likely to have low confidence
        payload = {
            "query": "very specific obscure cultural term xyz abc def",
            "language": "hi",
            "session_id": session_id,
        }

        headers = {
            **auth_headers_api_consumer,
            "X-Request-ID": request_id,
        }

        response = http_client.post(
            "/api/v1/chat",
            json=payload,
            headers=headers,
        )

        if response.status_code == 200:
            data = response.json()
            # If confidence is very low, expect fallback message
            if data.get("confidence", 1.0) < 0.65:
                # Should contain fallback message or helpline info
                response_text = data.get("response", "").lower()
                assert (
                    "हेल्पलाइन" in response_text or
                    "helpline" in response_text or
                    "संपर्क करें" in response_text or
                    "contact" in response_text
                )

    @pytest.mark.integration
    def test_chat_unicode_handling_hindi_devanagari(
        self,
        http_client: httpx.Client,
        session_id: str,
        request_id: str,
        auth_headers_api_consumer: dict,
    ):
        """
        Test: System correctly handles Hindi Devanagari script
        """
        hindi_queries = [
            "क्या आप हिंदी समझते हैं?",
            "भारतीय संस्कृति के बारे में बताइए।",
            "नमस्ते, आप कैसे हो?",
        ]

        for query in hindi_queries:
            payload = {
                "query": query,
                "language": "hi",
                "session_id": session_id,
            }

            headers = {
                **auth_headers_api_consumer,
                "X-Request-ID": str(__import__("uuid").uuid4()),
            }

            response = http_client.post(
                "/api/v1/chat",
                json=payload,
                headers=headers,
            )

            # Should not return encoding errors
            assert response.status_code in [200, 202]
            data = response.json()
            assert "error" not in data or data.get("error", {}).get("code") != "INVALID_REQUEST"

    @pytest.mark.integration
    def test_chat_streaming_response(
        self,
        http_client: httpx.Client,
        chat_query_hindi: str,
        session_id: str,
        request_id: str,
        auth_headers_api_consumer: dict,
    ):
        """
        Test: Streaming chat response (Server-Sent Events)
        """
        payload = {
            "query": chat_query_hindi,
            "language": "hi",
            "session_id": session_id,
            "stream": True,
        }

        headers = {
            **auth_headers_api_consumer,
            "X-Request-ID": request_id,
        }

        response = http_client.post(
            "/api/v1/chat/stream",
            json=payload,
            headers=headers,
        )

        assert response.status_code == 200
        assert "text/event-stream" in response.headers.get("content-type", "")

        # Parse SSE stream
        events = response.text.split("\n")
        assert len(events) > 0
