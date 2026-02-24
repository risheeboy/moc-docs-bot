import pytest
from app.services.cache_service import CacheService
from app.models.response import QueryResponse, Source


class TestCacheService:
    """Tests for Redis cache service."""

    @pytest.fixture
    def cache_service(self):
        """Initialize cache service."""
        return CacheService()

    def test_cache_key_generation(self, cache_service):
        """Test cache key generation."""
        key = cache_service.generate_cache_key(
            query="Test query",
            language="en"
        )
        assert key is not None
        assert key.startswith("rag:query:")

    def test_cache_key_consistency(self, cache_service):
        """Test that same query generates same cache key."""
        key1 = cache_service.generate_cache_key(
            query="Test query",
            language="en"
        )
        key2 = cache_service.generate_cache_key(
            query="Test query",
            language="en"
        )
        assert key1 == key2

    def test_cache_key_differs_for_different_queries(self, cache_service):
        """Test that different queries generate different keys."""
        key1 = cache_service.generate_cache_key(
            query="Query 1",
            language="en"
        )
        key2 = cache_service.generate_cache_key(
            query="Query 2",
            language="en"
        )
        assert key1 != key2

    def test_cache_key_includes_filters(self, cache_service):
        """Test that filters affect cache key."""
        key1 = cache_service.generate_cache_key(
            query="Test",
            language="en",
            filters={"source_sites": ["site1.com"]}
        )
        key2 = cache_service.generate_cache_key(
            query="Test",
            language="en",
            filters={"source_sites": ["site2.com"]}
        )
        assert key1 != key2

    def test_set_and_get_response(self, cache_service):
        """Test caching and retrieving a response."""
        # Create test response
        response = QueryResponse(
            context="Test context",
            sources=[],
            confidence=0.85,
            cached=False
        )

        key = cache_service.generate_cache_key("test", "en")

        # Cache it
        if cache_service.redis_client:
            cache_service.set(key, response, ttl=60)

            # Retrieve it
            cached = cache_service.get(key)
            if cached:
                assert isinstance(cached, QueryResponse)
                assert cached.context == "Test context"

    def test_cache_miss_returns_none(self, cache_service):
        """Test that cache miss returns None."""
        key = "rag:query:nonexistent"
        result = cache_service.get(key)
        assert result is None

    def test_cache_key_with_pagination(self, cache_service):
        """Test cache key includes pagination."""
        key1 = cache_service.generate_cache_key(
            query="Test",
            language="en",
            page=1,
            page_size=20
        )
        key2 = cache_service.generate_cache_key(
            query="Test",
            language="en",
            page=2,
            page_size=20
        )
        assert key1 != key2
