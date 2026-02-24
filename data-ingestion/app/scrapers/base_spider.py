"""Base spider class with common scraping functionality."""

import structlog
from typing import Optional, List, Dict, Any
from datetime import datetime
from abc import ABC, abstractmethod
import asyncio

from app.config import settings
from app.utils.robots_checker import RobotsChecker

logger = structlog.get_logger()


class BaseSpider(ABC):
    """Base spider class for all scraping operations."""

    def __init__(
        self,
        target_url: str,
        spider_type: str = "static",
        job_id: Optional[str] = None,
    ):
        """Initialize spider.

        Args:
            target_url: Base URL to scrape
            spider_type: Type of spider (static, dynamic, pdf, media)
            job_id: Job ID for tracking
        """
        self.target_url = target_url
        self.spider_type = spider_type
        self.job_id = job_id
        self.robots_checker = RobotsChecker(
            respect_robots_txt=settings.ingestion_respect_robots_txt
        )

        self.pages_crawled = 0
        self.documents_found = 0
        self.errors = 0

        logger.info(
            "spider_initialized",
            spider_type=spider_type,
            target_url=target_url,
            job_id=job_id,
        )

    async def check_robots_txt(self, url: str) -> bool:
        """Check if URL is allowed by robots.txt.

        Args:
            url: URL to check

        Returns:
            True if allowed, False otherwise
        """
        if not settings.ingestion_respect_robots_txt:
            return True

        return await self.robots_checker.is_allowed(url, settings.ingestion_user_agent)

    async def should_crawl(self, url: str) -> bool:
        """Determine if a URL should be crawled.

        Args:
            url: URL to check

        Returns:
            True if should crawl, False otherwise
        """
        # Check robots.txt
        if not await self.check_robots_txt(url):
            logger.warning(
                "url_blocked_by_robots_txt",
                url=url,
                job_id=self.job_id,
            )
            return False

        # Check if URL is from target domain
        from urllib.parse import urlparse
        target_domain = urlparse(self.target_url).netloc
        url_domain = urlparse(url).netloc

        if url_domain != target_domain:
            return False

        return True

    @abstractmethod
    async def crawl(self) -> List[Dict[str, Any]]:
        """Crawl target URL and return documents.

        Returns:
            List of crawled documents with metadata
        """
        pass

    def get_stats(self) -> Dict[str, int]:
        """Get crawling statistics."""
        return {
            "pages_crawled": self.pages_crawled,
            "documents_found": self.documents_found,
            "errors": self.errors,
        }

    async def cleanup(self):
        """Cleanup resources."""
        logger.info(
            "spider_cleanup",
            spider_type=self.spider_type,
            job_id=self.job_id,
        )
