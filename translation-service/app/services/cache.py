"""Redis-backed translation cache"""

import hashlib
from typing import Optional

import redis.asyncio as aioredis
import structlog
import json

from app.config import settings

logger = structlog.get_logger()


class TranslationCache:
    """
    Redis-backed cache for translations.

    Cache key format: `translation:{source_lang}:{target_lang}:{text_hash}`
    where text_hash = SHA256(text)

    Uses REDIS_DB_TRANSLATION (default: 3) from §3.2 Shared Contracts.
    """

    def __init__(self):
        self.redis: Optional[aioredis.Redis] = None
        self._connected = False

    async def connect(self):
        """Connect to Redis/ElastiCache"""
        if self._connected:
            return

        try:
            # Build Redis URL with SSL support
            protocol = "rediss" if settings.redis_ssl else "redis"
            redis_url = f"{protocol}://{settings.redis_host}:{settings.redis_port}/{settings.redis_db_translation}"

            # Build connection kwargs
            connection_kwargs = {
                "encoding": "utf8",
                "decode_responses": True,
            }

            if settings.redis_password:
                connection_kwargs["password"] = settings.redis_password

            if settings.redis_ssl:
                connection_kwargs["ssl"] = True

            self.redis = aioredis.from_url(redis_url, **connection_kwargs)

            # Test connection
            await self.redis.ping()
            self._connected = True
            logger.info(
                "Connected to Redis for translation cache",
                db=settings.redis_db_translation,
                ssl=settings.redis_ssl,
            )

        except Exception as e:
            logger.error("Failed to connect to Redis", error=str(e))
            raise

    async def disconnect(self):
        """Disconnect from Redis"""
        if self.redis:
            await self.redis.close()
            self._connected = False
            logger.info("Disconnected from Redis")

    @staticmethod
    def _make_key(
        text: str, source_lang: str, target_lang: str
    ) -> str:
        """Create a cache key from text and language pair"""
        text_hash = hashlib.sha256(text.encode()).hexdigest()
        return f"translation:{source_lang}:{target_lang}:{text_hash}"

    async def get(
        self, text: str, source_lang: str, target_lang: str
    ) -> Optional[str]:
        """
        Get cached translation.

        Returns:
            Translated text if in cache, None otherwise
        """
        if not self._connected or not self.redis:
            return None

        try:
            key = self._make_key(text, source_lang, target_lang)
            cached_value = await self.redis.get(key)

            if cached_value:
                logger.debug(
                    "Cache hit for translation",
                    source_lang=source_lang,
                    target_lang=target_lang,
                )
                return cached_value

            return None

        except Exception as e:
            logger.warning("Cache get failed", error=str(e))
            return None

    async def set(
        self,
        text: str,
        source_lang: str,
        target_lang: str,
        translation: str,
        ttl_seconds: int = 86400,
    ) -> bool:
        """
        Cache a translation.

        Args:
            text: Original text
            source_lang: Source language code
            target_lang: Target language code
            translation: Translated text
            ttl_seconds: Time to live in seconds (default 24 hours)

        Returns:
            True if successfully cached, False otherwise
        """
        if not self._connected or not self.redis:
            return False

        try:
            key = self._make_key(text, source_lang, target_lang)
            await self.redis.setex(key, ttl_seconds, translation)

            logger.debug(
                "Cached translation",
                source_lang=source_lang,
                target_lang=target_lang,
                ttl_seconds=ttl_seconds,
            )
            return True

        except Exception as e:
            logger.warning("Cache set failed", error=str(e))
            return False

    async def delete(
        self, text: str, source_lang: str, target_lang: str
    ) -> bool:
        """
        Delete a cached translation.

        Returns:
            True if key was deleted, False otherwise
        """
        if not self._connected or not self.redis:
            return False

        try:
            key = self._make_key(text, source_lang, target_lang)
            result = await self.redis.delete(key)
            return bool(result)

        except Exception as e:
            logger.warning("Cache delete failed", error=str(e))
            return False

    async def clear_all(self) -> bool:
        """
        Clear all translation cache entries.

        Warning: This clears the entire REDIS_DB_TRANSLATION database.
        """
        if not self._connected or not self.redis:
            return False

        try:
            await self.redis.flushdb()
            logger.info("Cleared all translation cache")
            return True

        except Exception as e:
            logger.warning("Cache clear_all failed", error=str(e))
            return False

    async def health_check(self) -> bool:
        """Check if Redis is healthy"""
        if not self._connected or not self.redis:
            return False

        try:
            await self.redis.ping()
            return True

        except Exception as e:
            logger.warning("Redis health check failed", error=str(e))
            return False

    async def get_stats(self) -> dict:
        """Get cache statistics"""
        if not self._connected or not self.redis:
            return {}

        try:
            info = await self.redis.info()
            return {
                "used_memory": info.get("used_memory", 0),
                "used_memory_human": info.get("used_memory_human", "0B"),
                "total_keys": await self.redis.dbsize(),
            }

        except Exception as e:
            logger.warning("Failed to get cache stats", error=str(e))
            return {}


# Global singleton instance
translation_cache = TranslationCache()
