import pytest
from pydantic import ValidationError
from app.models.request import (
    QueryRequest, SearchRequest, IngestRequest,
    ChatMessage, QueryFilters, SearchFilters
)
from app.models.response import (
    QueryResponse, SearchResponse, IngestResponse,
    Source, SearchResult, HealthResponse
)


class TestRequestModels:
    """Tests for request validation models."""

    def test_query_request_valid(self):
        """Test valid QueryRequest."""
        data = {
            "query": "Test query",
            "language": "en",
            "session_id": "session-123",
            "chat_history": [],
            "top_k": 10,
            "rerank_top_k": 5
        }
        request = QueryRequest(**data)
        assert request.query == "Test query"
        assert request.language == "en"

    def test_query_request_missing_required(self):
        """Test QueryRequest with missing required fields."""
        data = {
            "query": "Test query",
            "language": "en"
            # Missing session_id
        }
        with pytest.raises(ValidationError):
            QueryRequest(**data)

    def test_search_request_valid(self):
        """Test valid SearchRequest."""
        data = {
            "query": "Test search",
            "language": "en",
            "page": 1,
            "page_size": 20
        }
        request = SearchRequest(**data)
        assert request.query == "Test search"
        assert request.page == 1

    def test_search_request_invalid_page(self):
        """Test SearchRequest with invalid page."""
        data = {
            "query": "Test",
            "language": "en",
            "page": 0  # Invalid: must be >= 1
        }
        with pytest.raises(ValidationError):
            SearchRequest(**data)

    def test_ingest_request_valid(self):
        """Test valid IngestRequest."""
        data = {
            "document_id": "doc-123",
            "title": "Test Document",
            "source_url": "https://example.com",
            "source_site": "example.com",
            "content": "Document content",
            "content_type": "webpage",
            "language": "en"
        }
        request = IngestRequest(**data)
        assert request.document_id == "doc-123"
        assert request.title == "Test Document"

    def test_chat_message_valid(self):
        """Test valid ChatMessage."""
        message = ChatMessage(role="user", content="Hello")
        assert message.role == "user"
        assert message.content == "Hello"


class TestResponseModels:
    """Tests for response validation models."""

    def test_source_valid(self):
        """Test valid Source."""
        source = Source(
            title="Test",
            url="https://example.com",
            snippet="Test snippet",
            score=0.95,
            source_site="example.com",
            language="en",
            content_type="webpage",
            chunk_id="chunk-123"
        )
        assert source.title == "Test"
        assert source.score == 0.95

    def test_query_response_valid(self):
        """Test valid QueryResponse."""
        response = QueryResponse(
            context="Test context",
            sources=[],
            confidence=0.85,
            cached=False
        )
        assert response.context == "Test context"
        assert response.confidence == 0.85

    def test_search_result_valid(self):
        """Test valid SearchResult."""
        result = SearchResult(
            title="Test",
            url="https://example.com",
            snippet="Test snippet",
            score=0.9,
            source_site="example.com",
            language="en",
            content_type="webpage"
        )
        assert result.title == "Test"

    def test_ingest_response_valid(self):
        """Test valid IngestResponse."""
        response = IngestResponse(
            document_id="doc-123",
            chunk_count=5,
            embedding_status="completed",
            milvus_ids=["id1", "id2", "id3"]
        )
        assert response.document_id == "doc-123"
        assert response.chunk_count == 5

    def test_search_response_valid(self):
        """Test valid SearchResponse."""
        response = SearchResponse(
            results=[],
            total_results=0,
            page=1,
            page_size=20,
            cached=False
        )
        assert response.page == 1
        assert response.page_size == 20

    def test_health_response_valid(self):
        """Test valid HealthResponse."""
        from datetime import datetime
        from app.models.response import DependencyHealth

        response = HealthResponse(
            status="healthy",
            service="rag-service",
            version="1.0.0",
            uptime_seconds=100.5,
            timestamp=datetime.utcnow(),
            dependencies={
                "milvus": DependencyHealth(status="healthy", latency_ms=5.0)
            }
        )
        assert response.status == "healthy"
        assert response.service == "rag-service"
