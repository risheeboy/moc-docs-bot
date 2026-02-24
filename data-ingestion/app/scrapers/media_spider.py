"""Media spider for extracting images and videos from websites."""

import structlog
from typing import List, Dict, Any
from urllib.parse import urljoin, urlparse
import asyncio

import httpx
from bs4 import BeautifulSoup

from app.config import settings
from app.scrapers.base_spider import BaseSpider
from app.parsers.media_metadata import MediaMetadataExtractor

logger = structlog.get_logger()


class MediaSpider(BaseSpider):
    """Spider for extracting images, videos, and multimedia metadata."""

    def __init__(
        self,
        target_url: str,
        job_id: str = None,
        max_pages: int = None,
    ):
        """Initialize media spider."""
        super().__init__(target_url, spider_type="media", job_id=job_id)

        self.max_pages = max_pages or settings.scraper_max_pages_per_site
        self.media_extractor = MediaMetadataExtractor()
        self.documents: List[Dict[str, Any]] = []

    async def crawl(self) -> List[Dict[str, Any]]:
        """Crawl website and extract media metadata.

        Returns:
            List of media documents
        """
        async with httpx.AsyncClient(
            timeout=settings.ingestion_request_timeout_seconds,
            headers={"User-Agent": settings.ingestion_user_agent},
        ) as client:
            document = await self._extract_media_from_page(client, self.target_url)

            if document:
                self.documents.append(document)
                self.documents_found += 1

            self.pages_crawled += 1

        logger.info(
            "media_spider_completed",
            media_items_found=self.documents_found,
            job_id=self.job_id,
        )

        return self.documents

    async def _extract_media_from_page(
        self, client: httpx.AsyncClient, url: str
    ) -> Dict[str, Any]:
        """Extract media metadata from a page.

        Args:
            client: HTTP client
            url: URL to extract media from

        Returns:
            Document with media metadata
        """
        try:
            response = await client.get(url, follow_redirects=True)
            response.raise_for_status()

            soup = BeautifulSoup(response.content, "html.parser")

            # Extract images
            images = await self._extract_images(soup, url)

            # Extract videos
            videos = await self._extract_videos(soup, url)

            # Extract media metadata
            media_metadata = await self.media_extractor.extract(soup)

            if not images and not videos:
                return None

            document = {
                "url": url,
                "title": f"Media from {urlparse(url).netloc}",
                "content": f"Extracted {len(images)} images and {len(videos)} videos",
                "content_type": "media",
                "metadata": {
                    "images_count": len(images),
                    "videos_count": len(videos),
                    "media_metadata": media_metadata,
                },
                "images": images,
                "videos": videos,
                "source_site": urlparse(url).netloc,
            }

            logger.debug(
                "media_extracted",
                url=url,
                images_count=len(images),
                videos_count=len(videos),
                job_id=self.job_id,
            )

            return document

        except Exception as e:
            logger.error(
                "media_extraction_error",
                url=url,
                error=str(e),
                job_id=self.job_id,
            )
            return None

    async def _extract_images(self, soup: BeautifulSoup, base_url: str) -> List[Dict]:
        """Extract image metadata from page.

        Args:
            soup: BeautifulSoup object
            base_url: Base URL for relative links

        Returns:
            List of image metadata
        """
        images = []

        try:
            for img in soup.find_all("img", limit=50):
                img_url = img.get("src")
                if not img_url:
                    continue

                # Convert relative URLs to absolute
                absolute_url = urljoin(base_url, img_url)

                # Skip data URIs and other non-http URLs
                if not absolute_url.startswith(("http://", "https://")):
                    continue

                images.append(
                    {
                        "type": "image",
                        "url": absolute_url,
                        "alt_text": img.get("alt", ""),
                        "title": img.get("title", ""),
                        "width": img.get("width"),
                        "height": img.get("height"),
                    }
                )

        except Exception as e:
            logger.warning(
                "image_extraction_error",
                error=str(e),
                job_id=self.job_id,
            )

        return images

    async def _extract_videos(self, soup: BeautifulSoup, base_url: str) -> List[Dict]:
        """Extract video metadata from page.

        Args:
            soup: BeautifulSoup object
            base_url: Base URL for relative links

        Returns:
            List of video metadata
        """
        videos = []

        try:
            # Extract from <video> tags
            for video in soup.find_all("video", limit=20):
                video_url = None

                # Try to find source in video tag
                source = video.find("source")
                if source and source.get("src"):
                    video_url = urljoin(base_url, source["src"])

                if not video_url and video.get("src"):
                    video_url = urljoin(base_url, video["src"])

                if video_url:
                    videos.append(
                        {
                            "type": "video",
                            "url": video_url,
                            "title": video.get("title", ""),
                            "poster": video.get("poster", ""),
                            "duration": video.get("data-duration"),
                        }
                    )

            # Extract from <iframe> tags (YouTube, Vimeo, etc.)
            for iframe in soup.find_all("iframe", limit=20):
                iframe_src = iframe.get("src")
                if iframe_src and any(
                    domain in iframe_src
                    for domain in ["youtube", "vimeo", "dailymotion"]
                ):
                    videos.append(
                        {
                            "type": "embedded_video",
                            "url": iframe_src,
                            "title": iframe.get("title", ""),
                            "width": iframe.get("width"),
                            "height": iframe.get("height"),
                        }
                    )

        except Exception as e:
            logger.warning(
                "video_extraction_error",
                error=str(e),
                job_id=self.job_id,
            )

        return videos
