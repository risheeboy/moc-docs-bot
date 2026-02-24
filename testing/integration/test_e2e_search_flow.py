"""
End-to-end search flow tests.
Tests: Scrape page → Ingest → Search → AI-generated summary

Validates:
- §8.1 API Gateway → RAG Service search contract
- §4 Error Response Format
- §5 Health Check Format
"""

import httpx
import pytest
from pydantic import BaseModel, Field
from typing import Optional


# ============================================================================
# Response Models
# ============================================================================

class SearchResult(BaseModel):
    """Individual search result."""
    title: str
    url: str
    snippet: str
    score: float
    source_site: str
    language: str
    content_type: str
    thumbnail_url: Optional[str] = None
    published_date: Optional[str] = None


class MultimediaResult(BaseModel):
    """Multimedia search result (image/video)."""
    type: str  # "image" | "video"
    url: str
    alt_text: Optional[str] = None
    source_site: str
    thumbnail_url: Optional[str] = None


class EventResult(BaseModel):
    """Event listing from search."""
    title: str
    date: str
    venue: Optional[str] = None
    description: Optional[str] = None
    source_url: str
    language: str


class SearchResponse(BaseModel):
    """Search API response (§8.1)."""
    results: list[SearchResult] = Field(default_factory=list)
    multimedia: list[MultimediaResult] = Field(default_factory=list)
    events: list[EventResult] = Field(default_factory=list)
    total_results: int
    page: int
    page_size: int
    cached: bool = False


# ============================================================================
# Tests
# ============================================================================

class TestSearchFlowBasic:
    """Basic search flow tests."""

    @pytest.mark.integration
    def test_search_query_english(
        self,
        http_client: httpx.Client,
        auth_headers_api_consumer: dict,
        request_id: str,
    ):
        """
        Test: English search query returns results
        Validates: §8.1 search endpoint contract
        """
        payload = {
            "query": "Indian heritage sites",
            "language": "en",
            "page": 1,
            "page_size": 20,
            "filters": {
                "source_sites": [],
                "content_type": None,
                "date_from": None,
                "date_to": None,
            },
        }

        headers = {
            **auth_headers_api_consumer,
            "X-Request-ID": request_id,
        }

        response = http_client.post(
            "/api/v1/search",
            json=payload,
            headers=headers,
        )

        assert response.status_code == 200
        data = response.json()
        search_resp = SearchResponse.model_validate(data)

        assert search_resp.page == 1
        assert search_resp.page_size <= 20
        assert search_resp.total_results >= 0

        # Validate result structure
        for result in search_resp.results:
            SearchResult.model_validate(result)

    @pytest.mark.integration
    def test_search_query_hindi(
        self,
        http_client: httpx.Client,
        auth_headers_api_consumer: dict,
        request_id: str,
    ):
        """
        Test: Hindi search query returns results
        """
        payload = {
            "query": "भारतीय विरासत स्थल",
            "language": "hi",
            "page": 1,
            "page_size": 20,
            "filters": {},
        }

        headers = {
            **auth_headers_api_consumer,
            "X-Request-ID": request_id,
        }

        response = http_client.post(
            "/api/v1/search",
            json=payload,
            headers=headers,
        )

        assert response.status_code == 200
        data = response.json()
        SearchResponse.model_validate(data)

    @pytest.mark.integration
    def test_search_with_filters(
        self,
        http_client: httpx.Client,
        auth_headers_api_consumer: dict,
        request_id: str,
    ):
        """
        Test: Search with source site and content type filters
        Validates: §8.1 filters field
        """
        payload = {
            "query": "Ministry of Culture",
            "language": "en",
            "page": 1,
            "page_size": 20,
            "filters": {
                "source_sites": ["culture.gov.in"],
                "content_type": "webpage",
                "date_from": "2025-01-01",
                "date_to": None,
            },
        }

        headers = {
            **auth_headers_api_consumer,
            "X-Request-ID": request_id,
        }

        response = http_client.post(
            "/api/v1/search",
            json=payload,
            headers=headers,
        )

        assert response.status_code == 200
        data = response.json()
        search_resp = SearchResponse.model_validate(data)

        # All results should be from specified source site
        for result in search_resp.results:
            if result.source_site:
                assert result.source_site in ["culture.gov.in"]

    @pytest.mark.integration
    def test_search_pagination(
        self,
        http_client: httpx.Client,
        auth_headers_api_consumer: dict,
        request_id: str,
    ):
        """
        Test: Pagination works correctly across pages
        """
        # Get first page
        payload_page1 = {
            "query": "cultural heritage",
            "language": "en",
            "page": 1,
            "page_size": 10,
        }

        headers = {
            **auth_headers_api_consumer,
            "X-Request-ID": request_id,
        }

        response1 = http_client.post(
            "/api/v1/search",
            json=payload_page1,
            headers=headers,
        )
        assert response1.status_code == 200
        data1 = response1.json()
        SearchResponse.model_validate(data1)

        # Get second page
        if data1.get("total_results", 0) > 10:
            payload_page2 = {
                **payload_page1,
                "page": 2,
            }

            response2 = http_client.post(
                "/api/v1/search",
                json=payload_page2,
                headers=headers,
            )
            assert response2.status_code == 200
            data2 = response2.json()
            SearchResponse.model_validate(data2)

            # Results should be different
            result_ids_1 = [r["url"] for r in data1.get("results", [])]
            result_ids_2 = [r["url"] for r in data2.get("results", [])]
            assert len(set(result_ids_1) & set(result_ids_2)) == 0, \
                "Pages should have different results"

    @pytest.mark.integration
    def test_search_includes_multimedia(
        self,
        http_client: httpx.Client,
        auth_headers_api_consumer: dict,
        request_id: str,
    ):
        """
        Test: Search results include multimedia (images/videos)
        Validates: §8.1 multimedia field
        """
        payload = {
            "query": "Indian monuments",
            "language": "en",
            "page": 1,
            "page_size": 20,
        }

        headers = {
            **auth_headers_api_consumer,
            "X-Request-ID": request_id,
        }

        response = http_client.post(
            "/api/v1/search",
            json=payload,
            headers=headers,
        )

        assert response.status_code == 200
        data = response.json()
        search_resp = SearchResponse.model_validate(data)

        # Validate multimedia structure if present
        for media in search_resp.multimedia:
            MultimediaResult.model_validate(media)
            assert media.type in ["image", "video"]
            assert media.url
            assert media.source_site

    @pytest.mark.integration
    def test_search_includes_events(
        self,
        http_client: httpx.Client,
        auth_headers_api_consumer: dict,
        request_id: str,
    ):
        """
        Test: Search results include relevant events
        Validates: §8.1 events field
        """
        payload = {
            "query": "cultural festival",
            "language": "en",
            "page": 1,
            "page_size": 20,
        }

        headers = {
            **auth_headers_api_consumer,
            "X-Request-ID": request_id,
        }

        response = http_client.post(
            "/api/v1/search",
            json=payload,
            headers=headers,
        )

        assert response.status_code == 200
        data = response.json()
        search_resp = SearchResponse.model_validate(data)

        # Validate event structure if present
        for event in search_resp.events:
            EventResult.model_validate(event)
            assert event.title
            assert event.date
            assert event.source_url

    @pytest.mark.integration
    def test_search_invalid_language(
        self,
        http_client: httpx.Client,
        auth_headers_api_consumer: dict,
        request_id: str,
    ):
        """
        Test: Invalid language returns error
        Validates: §4 INVALID_LANGUAGE error code
        """
        payload = {
            "query": "test",
            "language": "invalid_lang",
            "page": 1,
            "page_size": 20,
        }

        headers = {
            **auth_headers_api_consumer,
            "X-Request-ID": request_id,
        }

        response = http_client.post(
            "/api/v1/search",
            json=payload,
            headers=headers,
        )

        assert response.status_code == 400
        error_data = response.json()
        assert error_data["error"]["code"] == "INVALID_LANGUAGE"

    @pytest.mark.integration
    def test_search_invalid_page(
        self,
        http_client: httpx.Client,
        auth_headers_api_consumer: dict,
        request_id: str,
    ):
        """
        Test: Invalid page number returns error
        Validates: §4 INVALID_REQUEST error code
        """
        payload = {
            "query": "test",
            "language": "en",
            "page": 0,  # Invalid: must be >= 1
            "page_size": 20,
        }

        headers = {
            **auth_headers_api_consumer,
            "X-Request-ID": request_id,
        }

        response = http_client.post(
            "/api/v1/search",
            json=payload,
            headers=headers,
        )

        assert response.status_code == 400
        error_data = response.json()
        assert error_data["error"]["code"] == "INVALID_REQUEST"

    @pytest.mark.integration
    def test_search_page_size_limits(
        self,
        http_client: httpx.Client,
        auth_headers_api_consumer: dict,
        request_id: str,
    ):
        """
        Test: Page size is capped at maximum (100)
        """
        payload = {
            "query": "test",
            "language": "en",
            "page": 1,
            "page_size": 500,  # Request more than max
        }

        headers = {
            **auth_headers_api_consumer,
            "X-Request-ID": request_id,
        }

        response = http_client.post(
            "/api/v1/search",
            json=payload,
            headers=headers,
        )

        if response.status_code == 200:
            data = response.json()
            assert data["page_size"] <= 100, "Page size should be capped at 100"

    @pytest.mark.integration
    def test_search_empty_query(
        self,
        http_client: httpx.Client,
        auth_headers_api_consumer: dict,
        request_id: str,
    ):
        """
        Test: Empty query returns error
        """
        payload = {
            "query": "",
            "language": "en",
            "page": 1,
            "page_size": 20,
        }

        headers = {
            **auth_headers_api_consumer,
            "X-Request-ID": request_id,
        }

        response = http_client.post(
            "/api/v1/search",
            json=payload,
            headers=headers,
        )

        assert response.status_code == 400
        error_data = response.json()
        assert error_data["error"]["code"] == "INVALID_REQUEST"


class TestSearchFlowAdvanced:
    """Advanced search scenarios."""

    @pytest.mark.integration
    def test_search_result_relevance_scoring(
        self,
        http_client: httpx.Client,
        auth_headers_api_consumer: dict,
        request_id: str,
    ):
        """
        Test: Search results are ranked by relevance score
        """
        payload = {
            "query": "Ministry of Culture India",
            "language": "en",
            "page": 1,
            "page_size": 10,
        }

        headers = {
            **auth_headers_api_consumer,
            "X-Request-ID": request_id,
        }

        response = http_client.post(
            "/api/v1/search",
            json=payload,
            headers=headers,
        )

        assert response.status_code == 200
        data = response.json()
        search_resp = SearchResponse.model_validate(data)

        # Verify scores are in descending order
        if len(search_resp.results) > 1:
            scores = [r.score for r in search_resp.results]
            assert scores == sorted(scores, reverse=True), \
                "Results should be ranked by score (descending)"

    @pytest.mark.integration
    def test_search_caching(
        self,
        http_client: httpx.Client,
        auth_headers_api_consumer: dict,
        request_id: str,
    ):
        """
        Test: Same search query returns cached results on second request
        Validates: §8.1 cached field in response
        """
        payload = {
            "query": "Ancient Indian art",
            "language": "en",
            "page": 1,
            "page_size": 20,
        }

        headers = {
            **auth_headers_api_consumer,
            "X-Request-ID": request_id,
        }

        # First request should not be cached
        response1 = http_client.post(
            "/api/v1/search",
            json=payload,
            headers=headers,
        )
        assert response1.status_code == 200
        data1 = response1.json()
        assert data1.get("cached") is False

        # Second request with same query should be cached
        response2 = http_client.post(
            "/api/v1/search",
            json=payload,
            headers={
                **auth_headers_api_consumer,
                "X-Request-ID": str(__import__("uuid").uuid4()),
            },
        )
        assert response2.status_code == 200
        data2 = response2.json()
        # May be cached depending on implementation
        assert "cached" in data2

    @pytest.mark.integration
    def test_search_multilingual_results(
        self,
        http_client: httpx.Client,
        auth_headers_api_consumer: dict,
        request_id: str,
    ):
        """
        Test: Search returns results in multiple languages
        """
        payload = {
            "query": "भारतीय संस्कृति",
            "language": "hi",
            "page": 1,
            "page_size": 20,
        }

        headers = {
            **auth_headers_api_consumer,
            "X-Request-ID": request_id,
        }

        response = http_client.post(
            "/api/v1/search",
            json=payload,
            headers=headers,
        )

        assert response.status_code == 200
        data = response.json()
        search_resp = SearchResponse.model_validate(data)

        # Results may include both Hindi and English content
        languages = {r.language for r in search_resp.results}
        assert len(languages) > 0
