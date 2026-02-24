import logging
import json
import hashlib
from typing import Optional, Any, Dict
import redis
from app.config import settings
from app.models.response import QueryResponse, SearchResponse

logger = logging.getLogger(__name__)


class CacheService:
    """
    Redis caching layer for query and search results.

    Caches retrieval results with configurable TTL.
    Invalidates cache on document ingestion.
    """

    def __init__(self):
        try:
            self.redis_client = redis.Redis(
                host=settings.redis_host,
                port=settings.redis_port,
                password=settings.redis_password,
                db=settings.redis_db_cache,
                decode_responses=True,
                socket_connect_timeout=5
            )
            # Test connection
            self.redis_client.ping()
            logger.info(f"Connected to Redis at {settings.redis_host}:{settings.redis_port}")
        except Exception as e:
            logger.error(f"Redis connection error: {e}")
            self.redis_client = None

    def generate_cache_key(
        self,
        query: str,
        language: str,
        filters: Optional[Dict[str, Any]] = None,
        page: Optional[int] = None,
        page_size: Optional[int] = None
    ) -> str:
        """
        Generate a cache key from query and filters.

        Uses SHA256 hash to keep keys short.
        """
        key_parts = [query, language]

        if filters:
            if filters.get("source_sites"):
                key_parts.append("|".join(sorted(filters["source_sites"])))
            if filters.get("content_type"):
                key_parts.append(filters["content_type"])
            if filters.get("date_from"):
                key_parts.append(filters["date_from"])
            if filters.get("date_to"):
                key_parts.append(filters["date_to"])

        if page is not None:
            key_parts.append(f"page:{page}")
        if page_size is not None:
            key_parts.append(f"size:{page_size}")

        cache_key_str = "|".join(key_parts)
        cache_hash = hashlib.sha256(cache_key_str.encode()).hexdigest()
        return f"rag:query:{cache_hash}"

    def get(self, key: str) -> Optional[Any]:
        """
        Get cached result.

        Returns deserialized response object or None if not found.
        """
        if not self.redis_client:
            return None

        try:
            cached = self.redis_client.get(key)
            if cached:
                data = json.loads(cached)
                # Try to reconstruct response object
                if "context" in data:  # QueryResponse
                    return QueryResponse(**data)
                elif "results" in data:  # SearchResponse
                    return SearchResponse(**data)
                return data
            return None
        except Exception as e:
            logger.warning(f"Cache get error: {e}")
            return None

    def set(
        self,
        key: str,
        value: Any,
        ttl: int = 3600
    ) -> bool:
        """
        Cache a result.

        Args:
            key: Cache key
            value: Response object to cache
            ttl: Time-to-live in seconds

        Returns:
            True if successful, False otherwise
        """
        if not self.redis_client:
            return False

        try:
            # Serialize response
            if isinstance(value, (QueryResponse, SearchResponse)):
                json_data = json.dumps(value.model_dump())
            else:
                json_data = json.dumps(value)

            self.redis_client.setex(key, ttl, json_data)
            logger.debug(f"Cached result with key {key}")
            return True
        except Exception as e:
            logger.warning(f"Cache set error: {e}")
            return False

    def invalidate_all(self) -> bool:
        """
        Invalidate all RAG cache entries.

        Called after document ingestion to refresh results.
        """
        if not self.redis_client:
            return False

        try:
            # Delete all keys matching pattern
            pattern = "rag:query:*"
            cursor = 0
            deleted = 0

            while True:
                cursor, keys = self.redis_client.scan(cursor, match=pattern, count=100)
                if keys:
                    deleted += self.redis_client.delete(*keys)
                if cursor == 0:
                    break

            logger.info(f"Invalidated {deleted} cache entries")
            return True
        except Exception as e:
            logger.warning(f"Cache invalidation error: {e}")
            return False

    def invalidate_by_pattern(self, pattern: str) -> bool:
        """Invalidate cache entries matching a pattern."""
        if not self.redis_client:
            return False

        try:
            cursor = 0
            deleted = 0

            while True:
                cursor, keys = self.redis_client.scan(cursor, match=pattern, count=100)
                if keys:
                    deleted += self.redis_client.delete(*keys)
                if cursor == 0:
                    break

            logger.info(f"Invalidated {deleted} cache entries matching {pattern}")
            return True
        except Exception as e:
            logger.warning(f"Pattern cache invalidation error: {e}")
            return False
