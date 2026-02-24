"""PDF discovery and download spider."""

import structlog
from typing import List, Dict, Any
from urllib.parse import urljoin, urlparse
import asyncio

import httpx
from bs4 import BeautifulSoup

from app.config import settings
from app.scrapers.base_spider import BaseSpider
from app.parsers.marker_pdf_parser import MarkerPdfParser

logger = structlog.get_logger()


class PdfSpider(BaseSpider):
    """Spider for discovering and downloading PDF documents."""

    def __init__(
        self,
        target_url: str,
        job_id: str = None,
        max_pdfs: int = None,
    ):
        """Initialize PDF spider."""
        super().__init__(target_url, spider_type="pdf", job_id=job_id)

        self.max_pdfs = max_pdfs or 100
        self.pdf_parser = MarkerPdfParser()
        self.documents: List[Dict[str, Any]] = []

    async def crawl(self) -> List[Dict[str, Any]]:
        """Crawl website and download PDFs.

        Returns:
            List of extracted PDF documents
        """
        async with httpx.AsyncClient(
            timeout=settings.pdf_timeout_seconds,
            headers={"User-Agent": settings.ingestion_user_agent},
        ) as client:
            # First, fetch the main page to find PDF links
            pdf_urls = await self._discover_pdfs(client, self.target_url)

            logger.info(
                "pdfs_discovered",
                count=len(pdf_urls),
                job_id=self.job_id,
            )

            # Download and parse each PDF
            for pdf_url in pdf_urls[: self.max_pdfs]:
                try:
                    if not await self.should_crawl(pdf_url):
                        continue

                    document = await self._download_and_parse_pdf(client, pdf_url)

                    if document:
                        self.documents.append(document)
                        self.documents_found += 1

                    self.pages_crawled += 1

                except Exception as e:
                    logger.error(
                        "pdf_download_error",
                        url=pdf_url,
                        error=str(e),
                        job_id=self.job_id,
                    )
                    self.errors += 1

                # Rate limiting
                await asyncio.sleep(settings.scraper_download_delay)

        logger.info(
            "pdf_spider_completed",
            pdfs_found=self.documents_found,
            errors=self.errors,
            job_id=self.job_id,
        )

        return self.documents

    async def _discover_pdfs(
        self, client: httpx.AsyncClient, url: str
    ) -> List[str]:
        """Discover PDF links on a website.

        Args:
            client: HTTP client
            url: URL to search for PDFs

        Returns:
            List of PDF URLs
        """
        pdf_urls = []

        try:
            response = await client.get(url, follow_redirects=True)
            response.raise_for_status()

            soup = BeautifulSoup(response.content, "html.parser")

            # Find all links ending with .pdf
            for link in soup.find_all("a", href=True):
                href = link["href"]

                if href.lower().endswith(".pdf"):
                    absolute_url = urljoin(url, href)
                    pdf_urls.append(absolute_url)

                    if len(pdf_urls) >= self.max_pdfs:
                        break

        except Exception as e:
            logger.warning(
                "pdf_discovery_error",
                url=url,
                error=str(e),
                job_id=self.job_id,
            )

        return pdf_urls

    async def _download_and_parse_pdf(
        self, client: httpx.AsyncClient, pdf_url: str
    ) -> Dict[str, Any]:
        """Download and parse a PDF file.

        Args:
            client: HTTP client
            pdf_url: URL of PDF to download

        Returns:
            Document dictionary or None
        """
        try:
            # Download PDF
            response = await client.get(pdf_url, follow_redirects=True)
            response.raise_for_status()

            pdf_content = response.content

            # Check file size
            file_size_kb = len(pdf_content) / 1024
            if file_size_kb < settings.pdf_min_file_size_kb:
                logger.debug(
                    "pdf_too_small",
                    url=pdf_url,
                    size_kb=file_size_kb,
                    job_id=self.job_id,
                )
                return None

            if file_size_kb > settings.pdf_max_file_size_mb * 1024:
                logger.warning(
                    "pdf_too_large",
                    url=pdf_url,
                    size_kb=file_size_kb,
                    job_id=self.job_id,
                )
                return None

            # Parse PDF using Marker
            text = await self.pdf_parser.parse_bytes(pdf_content)

            if not text or len(text.strip()) < 50:
                return None

            # Extract filename as title
            filename = pdf_url.split("/")[-1].replace(".pdf", "")

            document = {
                "url": pdf_url,
                "title": filename,
                "content": text,
                "content_type": "pdf",
                "metadata": {
                    "title": filename,
                    "source_url": pdf_url,
                    "file_size_kb": file_size_kb,
                },
                "images": [],
                "source_site": urlparse(pdf_url).netloc,
            }

            logger.debug(
                "pdf_parsed",
                url=pdf_url,
                content_length=len(text),
                job_id=self.job_id,
            )

            return document

        except Exception as e:
            logger.error(
                "pdf_parse_error",
                url=pdf_url,
                error=str(e),
                job_id=self.job_id,
            )
            return None
