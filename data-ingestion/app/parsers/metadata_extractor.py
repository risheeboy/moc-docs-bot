"""Extract metadata from HTML pages."""

import structlog
from typing import Dict, Optional
from datetime import datetime
from urllib.parse import urlparse

from bs4 import BeautifulSoup

logger = structlog.get_logger()


class MetadataExtractor:
    """Extractor for page metadata (title, date, author, language, etc)."""

    async def extract(self, soup: BeautifulSoup, url: str) -> Dict:
        """Extract metadata from HTML page.

        Args:
            soup: BeautifulSoup object
            url: Page URL

        Returns:
            Dictionary with extracted metadata
        """
        metadata = {
            "source_url": url,
            "source_site": urlparse(url).netloc,
        }

        # Extract title
        title = await self._extract_title(soup)
        if title:
            metadata["title"] = title

        # Extract description
        description = await self._extract_description(soup)
        if description:
            metadata["description"] = description

        # Extract author
        author = await self._extract_author(soup)
        if author:
            metadata["author"] = author

        # Extract published date
        published_date = await self._extract_date(soup)
        if published_date:
            metadata["published_date"] = published_date

        # Extract language
        language = await self._extract_language(soup)
        if language:
            metadata["language"] = language

        # Extract tags/keywords
        tags = await self._extract_tags(soup)
        if tags:
            metadata["tags"] = tags

        # Extract canonical URL
        canonical = await self._extract_canonical(soup)
        if canonical:
            metadata["canonical_url"] = canonical

        return metadata

    async def _extract_title(self, soup: BeautifulSoup) -> Optional[str]:
        """Extract page title."""
        try:
            # Try Open Graph title first
            og_title = soup.find("meta", attrs={"property": "og:title"})
            if og_title and og_title.get("content"):
                return og_title["content"].strip()

            # Try meta title tag
            meta_title = soup.find("meta", attrs={"name": "title"})
            if meta_title and meta_title.get("content"):
                return meta_title["content"].strip()

            # Fallback to <title> tag
            title_tag = soup.find("title")
            if title_tag:
                return title_tag.get_text().strip()

        except Exception as e:
            logger.debug("title_extraction_error", error=str(e))

        return None

    async def _extract_description(self, soup: BeautifulSoup) -> Optional[str]:
        """Extract page description."""
        try:
            # Try Open Graph description
            og_desc = soup.find("meta", attrs={"property": "og:description"})
            if og_desc and og_desc.get("content"):
                return og_desc["content"].strip()

            # Try meta description tag
            meta_desc = soup.find("meta", attrs={"name": "description"})
            if meta_desc and meta_desc.get("content"):
                return meta_desc["content"].strip()

        except Exception as e:
            logger.debug("description_extraction_error", error=str(e))

        return None

    async def _extract_author(self, soup: BeautifulSoup) -> Optional[str]:
        """Extract page author."""
        try:
            # Try article:author
            author = soup.find("meta", attrs={"property": "article:author"})
            if author and author.get("content"):
                return author["content"].strip()

            # Try author meta tag
            author = soup.find("meta", attrs={"name": "author"})
            if author and author.get("content"):
                return author["content"].strip()

        except Exception as e:
            logger.debug("author_extraction_error", error=str(e))

        return None

    async def _extract_date(self, soup: BeautifulSoup) -> Optional[str]:
        """Extract published date."""
        try:
            # Try article:published_time
            pub_date = soup.find("meta", attrs={"property": "article:published_time"})
            if pub_date and pub_date.get("content"):
                return pub_date["content"].strip()

            # Try datePublished schema
            date_pub = soup.find("meta", attrs={"itemprop": "datePublished"})
            if date_pub and date_pub.get("content"):
                return date_pub["content"].strip()

            # Try dateModified
            date_mod = soup.find("meta", attrs={"itemprop": "dateModified"})
            if date_mod and date_mod.get("content"):
                return date_mod["content"].strip()

        except Exception as e:
            logger.debug("date_extraction_error", error=str(e))

        return None

    async def _extract_language(self, soup: BeautifulSoup) -> Optional[str]:
        """Extract page language."""
        try:
            # Try html lang attribute
            html_tag = soup.find("html")
            if html_tag and html_tag.get("lang"):
                lang = html_tag["lang"].strip()
                # Normalize language code (e.g., "en-US" -> "en")
                if "-" in lang:
                    lang = lang.split("-")[0]
                return lang

            # Try meta language tag
            lang_meta = soup.find("meta", attrs={"name": "language"})
            if lang_meta and lang_meta.get("content"):
                return lang_meta["content"].strip()

        except Exception as e:
            logger.debug("language_extraction_error", error=str(e))

        return None

    async def _extract_tags(self, soup: BeautifulSoup) -> list:
        """Extract page tags/keywords."""
        try:
            tags = []

            # Try keywords meta tag
            keywords = soup.find("meta", attrs={"name": "keywords"})
            if keywords and keywords.get("content"):
                keyword_list = keywords["content"].split(",")
                tags.extend([k.strip() for k in keyword_list if k.strip()])

            # Try article:tag
            article_tags = soup.find_all("meta", attrs={"property": "article:tag"})
            for tag in article_tags:
                if tag.get("content"):
                    tags.append(tag["content"].strip())

            return list(set(tags))[:10]  # Limit to 10 unique tags

        except Exception as e:
            logger.debug("tags_extraction_error", error=str(e))

        return []

    async def _extract_canonical(self, soup: BeautifulSoup) -> Optional[str]:
        """Extract canonical URL."""
        try:
            canonical = soup.find("link", attrs={"rel": "canonical"})
            if canonical and canonical.get("href"):
                return canonical["href"].strip()

        except Exception as e:
            logger.debug("canonical_extraction_error", error=str(e))

        return None
