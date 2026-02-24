"""Dynamic JavaScript spider using Playwright for SPA websites."""

import structlog
from typing import List, Dict, Any
import asyncio

from playwright.async_api import async_playwright, Page
from bs4 import BeautifulSoup
from urllib.parse import urlparse

from app.config import settings
from app.scrapers.base_spider import BaseSpider
from app.parsers.html_parser import HtmlParser
from app.parsers.metadata_extractor import MetadataExtractor

logger = structlog.get_logger()


class DynamicSpider(BaseSpider):
    """Spider for crawling JavaScript-rendered SPA websites."""

    def __init__(
        self,
        target_url: str,
        job_id: str = None,
        max_pages: int = None,
    ):
        """Initialize dynamic spider."""
        super().__init__(target_url, spider_type="dynamic", job_id=job_id)

        self.max_pages = max_pages or settings.scraper_max_pages_per_site
        self.html_parser = HtmlParser()
        self.metadata_extractor = MetadataExtractor()
        self.documents: List[Dict[str, Any]] = []

    async def crawl(self) -> List[Dict[str, Any]]:
        """Crawl dynamic JavaScript website using Playwright.

        Returns:
            List of documents found
        """
        async with async_playwright() as p:
            browser = await p.chromium.launch(
                headless=settings.playwright_headless
            )
            page = await browser.new_page()

            try:
                await self._crawl_page(page, self.target_url)

                logger.info(
                    "dynamic_spider_completed",
                    pages_crawled=self.pages_crawled,
                    documents_found=self.documents_found,
                    errors=self.errors,
                    job_id=self.job_id,
                )

            finally:
                await browser.close()

        return self.documents

    async def _crawl_page(self, page: Page, url: str):
        """Crawl a single dynamic page.

        Args:
            page: Playwright page object
            url: URL to crawl
        """
        if self.pages_crawled >= self.max_pages:
            return

        if not await self.should_crawl(url):
            return

        try:
            logger.debug(
                "dynamic_spider_visiting",
                url=url,
                job_id=self.job_id,
            )

            # Navigate and wait for content
            await page.goto(url, wait_until=settings.playwright_wait_for_load_state)

            # Wait for dynamic content
            await asyncio.sleep(2)

            # Get rendered HTML
            content = await page.content()

            # Parse and extract text
            text = await self.html_parser.extract_text(content)

            if text and len(text.strip()) >= 50:
                soup = BeautifulSoup(content, "html.parser")

                # Extract metadata
                metadata = await self.metadata_extractor.extract(soup, url)

                # Extract images
                images = []
                for img in soup.find_all("img", limit=10):
                    img_url = img.get("src")
                    if img_url:
                        images.append(
                            {
                                "url": img_url,
                                "alt_text": img.get("alt", ""),
                                "title": img.get("title", ""),
                            }
                        )

                document = {
                    "url": url,
                    "title": metadata.get("title", ""),
                    "content": text,
                    "content_type": "webpage",
                    "metadata": metadata,
                    "images": images,
                    "source_site": urlparse(url).netloc,
                }

                self.documents.append(document)
                self.documents_found += 1

            self.pages_crawled += 1

        except Exception as e:
            logger.error(
                "dynamic_spider_error",
                url=url,
                error=str(e),
                job_id=self.job_id,
            )
            self.errors += 1

        # Rate limiting
        await asyncio.sleep(settings.scraper_download_delay)
