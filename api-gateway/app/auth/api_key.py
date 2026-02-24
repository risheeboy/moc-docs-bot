"""API key management and validation."""

import hashlib
import secrets
from datetime import datetime, timedelta
from typing import Optional
import logging

logger = logging.getLogger(__name__)


class APIKeyManager:
    """Manage API keys for widget/consumer access."""

    @staticmethod
    def generate_key(name: str) -> tuple[str, str]:
        """Generate a new API key.

        Returns:
            (raw_key, key_hash) - raw key to give to user, hash to store in DB
        """
        raw_key = f"key_{secrets.token_urlsafe(32)}"
        key_hash = APIKeyManager.hash_key(raw_key)
        return raw_key, key_hash

    @staticmethod
    def hash_key(key: str) -> str:
        """Hash API key for storage."""
        return hashlib.sha256(key.encode()).hexdigest()

    @staticmethod
    def verify_key(raw_key: str, stored_hash: str) -> bool:
        """Verify that a raw key matches the stored hash."""
        return APIKeyManager.hash_key(raw_key) == stored_hash
