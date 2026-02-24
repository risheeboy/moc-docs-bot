"""HTML parsing and clean text extraction using trafilatura."""

import structlog
from typing import Optional

import trafilatura
from trafilatura.settings import Extractor

logger = structlog.get_logger()


class HtmlParser:
    """Parser for extracting clean text from HTML using trafilatura."""

    def __init__(self):
        """Initialize HTML parser."""
        self.extractor = Extractor()

    async def extract_text(self, html: str) -> Optional[str]:
        """Extract clean text from HTML.

        Uses trafilatura for high-quality content extraction, removing boilerplate
        like navigation, ads, and other irrelevant content.

        Args:
            html: HTML content

        Returns:
            Extracted text or None if extraction fails
        """
        try:
            # Use trafilatura to extract main content
            content = trafilatura.extract(
                html,
                include_comments=False,
                favor_precision=True,
                favor_recall=False,
            )

            if not content:
                # Fallback: use basic HTML stripping
                from bs4 import BeautifulSoup
                soup = BeautifulSoup(html, "html.parser")

                # Remove script and style elements
                for script in soup(["script", "style"]):
                    script.decompose()

                text = soup.get_text()
                lines = (line.strip() for line in text.splitlines())
                chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
                content = " ".join(chunk for chunk in chunks if chunk)

            return content.strip() if content else None

        except Exception as e:
            logger.warning(
                "html_parsing_error",
                error=str(e),
            )
            return None

    async def extract_structured_data(self, html: str) -> dict:
        """Extract structured data from HTML (metadata, etc).

        Args:
            html: HTML content

        Returns:
            Dictionary with extracted structured data
        """
        try:
            from bs4 import BeautifulSoup

            soup = BeautifulSoup(html, "html.parser")

            data = {}

            # Extract title
            title_tag = soup.find("title")
            if title_tag:
                data["title"] = title_tag.get_text().strip()

            # Extract meta tags
            meta_description = soup.find("meta", attrs={"name": "description"})
            if meta_description:
                data["description"] = meta_description.get("content", "")

            meta_keywords = soup.find("meta", attrs={"name": "keywords"})
            if meta_keywords:
                data["keywords"] = meta_keywords.get("content", "").split(",")

            # Extract OG tags
            og_tags = soup.find_all("meta", attrs={"property": True})
            for tag in og_tags:
                property_name = tag.get("property", "").replace("og:", "")
                if property_name:
                    data[f"og_{property_name}"] = tag.get("content", "")

            return data

        except Exception as e:
            logger.warning(
                "structured_data_extraction_error",
                error=str(e),
            )
            return {}
