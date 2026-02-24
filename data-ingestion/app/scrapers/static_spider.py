"""Static HTML spider using Scrapy for government websites."""

import structlog
from typing import List, Dict, Any, Set
from urllib.parse import urljoin, urlparse
import asyncio

import httpx
from bs4 import BeautifulSoup

from app.config import settings
from app.scrapers.base_spider import BaseSpider
from app.parsers.html_parser import HtmlParser
from app.parsers.metadata_extractor import MetadataExtractor

logger = structlog.get_logger()


class StaticSpider(BaseSpider):
    """Spider for crawling static HTML websites."""

    def __init__(
        self,
        target_url: str,
        job_id: str = None,
        max_pages: int = None,
        depth_limit: int = None,
    ):
        """Initialize static spider."""
        super().__init__(target_url, spider_type="static", job_id=job_id)

        self.max_pages = max_pages or settings.scraper_max_pages_per_site
        self.depth_limit = depth_limit or settings.scraper_depth_limit

        self.html_parser = HtmlParser()
        self.metadata_extractor = MetadataExtractor()

        self.visited_urls: Set[str] = set()
        self.to_visit: List[tuple[str, int]] = [(target_url, 0)]
        self.documents: List[Dict[str, Any]] = []

    async def crawl(self) -> List[Dict[str, Any]]:
        """Crawl static HTML website.

        Returns:
            List of documents found
        """
        async with httpx.AsyncClient(
            timeout=settings.ingestion_request_timeout_seconds,
            headers={"User-Agent": settings.ingestion_user_agent},
        ) as client:
            while self.to_visit and self.pages_crawled < self.max_pages:
                url, depth = self.to_visit.pop(0)

                if url in self.visited_urls:
                    continue

                if not await self.should_crawl(url):
                    continue

                self.visited_urls.add(url)

                try:
                    document = await self._fetch_and_parse(client, url, depth)

                    if document:
                        self.documents.append(document)
                        self.documents_found += 1

                        # Extract links for crawling
                        if depth < self.depth_limit:
                            links = await self._extract_links(document["content"])
                            for link in links:
                                if link not in self.visited_urls:
                                    self.to_visit.append((link, depth + 1))

                    self.pages_crawled += 1

                except Exception as e:
                    logger.error(
                        "static_spider_error",
                        url=url,
                        error=str(e),
                        job_id=self.job_id,
                    )
                    self.errors += 1

                # Rate limiting
                await asyncio.sleep(settings.scraper_download_delay)

        logger.info(
            "static_spider_completed",
            pages_crawled=self.pages_crawled,
            documents_found=self.documents_found,
            errors=self.errors,
            job_id=self.job_id,
        )

        return self.documents

    async def _fetch_and_parse(
        self, client: httpx.AsyncClient, url: str, depth: int
    ) -> Dict[str, Any]:
        """Fetch and parse a single page.

        Args:
            client: HTTP client
            url: URL to fetch
            depth: Current depth in crawl

        Returns:
            Document dictionary or None if parsing fails
        """
        try:
            response = await client.get(url, follow_redirects=True)
            response.raise_for_status()

            # Parse HTML
            soup = BeautifulSoup(response.content, "html.parser")

            # Extract clean text
            text = await self.html_parser.extract_text(response.text)

            if not text or len(text.strip()) < 50:
                return None

            # Extract metadata
            metadata = await self.metadata_extractor.extract(soup, url)

            # Extract images
            images = await self._extract_images(soup, url)

            document = {
                "url": url,
                "title": metadata.get("title", ""),
                "content": text,
                "content_type": "webpage",
                "metadata": metadata,
                "images": images,
                "depth": depth,
                "source_site": urlparse(url).netloc,
            }

            logger.debug(
                "page_parsed",
                url=url,
                content_length=len(text),
                job_id=self.job_id,
            )

            return document

        except Exception as e:
            logger.error(
                "fetch_and_parse_error",
                url=url,
                error=str(e),
                job_id=self.job_id,
            )
            return None

    async def _extract_links(self, html_content: str) -> List[str]:
        """Extract all links from HTML content.

        Args:
            html_content: HTML content

        Returns:
            List of URLs found
        """
        links = []
        try:
            soup = BeautifulSoup(html_content, "html.parser")

            for link in soup.find_all("a", href=True):
                href = link["href"]

                # Convert relative URLs to absolute
                absolute_url = urljoin(self.target_url, href)

                # Filter out anchors and query strings
                if "#" in absolute_url:
                    absolute_url = absolute_url.split("#")[0]

                if absolute_url not in self.visited_urls:
                    links.append(absolute_url)

        except Exception as e:
            logger.warning(
                "link_extraction_error",
                error=str(e),
                job_id=self.job_id,
            )

        return links[:50]  # Limit extracted links

    async def _extract_images(self, soup: BeautifulSoup, base_url: str) -> List[Dict]:
        """Extract images from page.

        Args:
            soup: BeautifulSoup object
            base_url: Base URL for relative links

        Returns:
            List of image dictionaries
        """
        images = []

        try:
            for img in soup.find_all("img", limit=10):
                img_url = img.get("src")
                if not img_url:
                    continue

                # Convert relative URLs to absolute
                absolute_url = urljoin(base_url, img_url)

                images.append(
                    {
                        "url": absolute_url,
                        "alt_text": img.get("alt", ""),
                        "title": img.get("title", ""),
                    }
                )

        except Exception as e:
            logger.warning(
                "image_extraction_error",
                error=str(e),
                job_id=self.job_id,
            )

        return images
