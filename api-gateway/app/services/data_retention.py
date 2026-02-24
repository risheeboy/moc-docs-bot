"""Data retention and purging service."""

import logging
from datetime import datetime, timedelta
from typing import Optional
import asyncpg

logger = logging.getLogger(__name__)


class DataRetentionService:
    """Manage data retention policies and auto-purge."""

    def __init__(
        self,
        db_pool: asyncpg.Pool,
        retention_days: dict[str, int],
    ):
        """
        Initialize retention service.

        Args:
            db_pool: asyncpg connection pool
            retention_days: Dict mapping table -> retention days
        """
        self.db_pool = db_pool
        self.retention_days = retention_days

    async def purge_conversations(self) -> int:
        """Delete conversations older than retention period."""
        days = self.retention_days.get("conversations", 90)
        cutoff_date = datetime.utcnow() - timedelta(days=days)

        try:
            async with self.db_pool.acquire() as conn:
                count = await conn.execute(
                    "DELETE FROM conversations WHERE created_at < $1", cutoff_date
                )
            logger.info(f"Purged {count} conversations older than {days} days")
            return count
        except Exception as e:
            logger.error(f"Conversation purge error: {e}")
            return 0

    async def purge_feedback(self) -> int:
        """Delete feedback older than retention period."""
        days = self.retention_days.get("feedback", 365)
        cutoff_date = datetime.utcnow() - timedelta(days=days)

        try:
            async with self.db_pool.acquire() as conn:
                count = await conn.execute(
                    "DELETE FROM feedback WHERE created_at < $1", cutoff_date
                )
            logger.info(f"Purged {count} feedback records older than {days} days")
            return count
        except Exception as e:
            logger.error(f"Feedback purge error: {e}")
            return 0

    async def purge_audit_logs(self) -> int:
        """Delete audit logs older than retention period."""
        days = self.retention_days.get("audit_log", 730)
        cutoff_date = datetime.utcnow() - timedelta(days=days)

        try:
            async with self.db_pool.acquire() as conn:
                count = await conn.execute(
                    "DELETE FROM audit_log WHERE created_at < $1", cutoff_date
                )
            logger.info(f"Purged {count} audit logs older than {days} days")
            return count
        except Exception as e:
            logger.error(f"Audit log purge error: {e}")
            return 0

    async def purge_analytics(self) -> int:
        """Delete analytics records older than retention period."""
        days = self.retention_days.get("analytics", 365)
        cutoff_date = datetime.utcnow() - timedelta(days=days)

        try:
            async with self.db_pool.acquire() as conn:
                count = await conn.execute(
                    "DELETE FROM analytics WHERE created_at < $1", cutoff_date
                )
            logger.info(f"Purged {count} analytics records older than {days} days")
            return count
        except Exception as e:
            logger.error(f"Analytics purge error: {e}")
            return 0

    async def run_all_purges(self) -> dict[str, int]:
        """Run all retention purges."""
        logger.info("Starting data retention purges")
        results = {
            "conversations": await self.purge_conversations(),
            "feedback": await self.purge_feedback(),
            "audit_log": await self.purge_audit_logs(),
            "analytics": await self.purge_analytics(),
        }
        logger.info(f"Data retention complete: {results}")
        return results
