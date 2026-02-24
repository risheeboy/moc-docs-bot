"""Extract cultural events from web pages."""

import structlog
from typing import List, Dict, Optional
from datetime import datetime
import re

from bs4 import BeautifulSoup

logger = structlog.get_logger()


class EventExtractor:
    """Extractor for cultural events from web pages."""

    def __init__(self):
        """Initialize event extractor."""
        # Common date patterns
        self.date_patterns = [
            r'(\d{1,2}[-/]\d{1,2}[-/]\d{2,4})',  # DD/MM/YYYY or DD-MM-YYYY
            r'(\d{4}[-/]\d{1,2}[-/]\d{1,2})',    # YYYY-MM-DD
            r'(\d{1,2}\s+(?:January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{4})',
            r'(\d{1,2}\s+(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\s+\d{4})',
        ]

    async def extract(
        self, soup: BeautifulSoup, page_url: str
    ) -> List[Dict]:
        """Extract events from HTML page.

        Args:
            soup: BeautifulSoup object
            page_url: Page URL

        Returns:
            List of event dictionaries
        """
        events = []

        try:
            # Look for event containers
            event_sections = soup.find_all(
                ["article", "section", "div"],
                class_=re.compile(r"(event|festival|program|conference)", re.I),
            )

            for section in event_sections[:20]:  # Limit to 20 events
                event = await self._parse_event_section(section, page_url)
                if event:
                    events.append(event)

            # Also check for structured event data
            structured_events = await self._extract_structured_events(soup, page_url)
            events.extend(structured_events)

        except Exception as e:
            logger.warning(
                "event_extraction_error",
                error=str(e),
            )

        return events

    async def _parse_event_section(
        self, section: BeautifulSoup, page_url: str
    ) -> Optional[Dict]:
        """Parse event data from a section element.

        Args:
            section: BeautifulSoup element
            page_url: Page URL

        Returns:
            Event dictionary or None
        """
        try:
            event = {
                "source_url": page_url,
            }

            # Extract title/name
            title = None
            for header in section.find_all(["h1", "h2", "h3", "h4"], limit=1):
                title = header.get_text().strip()
                break

            if not title:
                # Try to get title from any strong or b tag
                strong = section.find("strong")
                if strong:
                    title = strong.get_text().strip()

            if title:
                event["title"] = title

            # Extract date
            date_text = await self._extract_date_text(section)
            if date_text:
                event["date"] = date_text

            # Extract venue
            venue = await self._extract_venue(section)
            if venue:
                event["venue"] = venue

            # Extract description
            description = await self._extract_event_description(section)
            if description:
                event["description"] = description

            # Only return if we have at least title and some other info
            if "title" in event and (
                "date" in event or "venue" in event or "description" in event
            ):
                return event

        except Exception as e:
            logger.debug(
                "event_parsing_error",
                error=str(e),
            )

        return None

    async def _extract_date_text(self, section: BeautifulSoup) -> Optional[str]:
        """Extract date from section.

        Args:
            section: BeautifulSoup element

        Returns:
            Date string or None
        """
        try:
            text = section.get_text()

            for pattern in self.date_patterns:
                match = re.search(pattern, text)
                if match:
                    return match.group(1)

        except Exception as e:
            logger.debug("date_extraction_error", error=str(e))

        return None

    async def _extract_venue(self, section: BeautifulSoup) -> Optional[str]:
        """Extract venue information.

        Args:
            section: BeautifulSoup element

        Returns:
            Venue string or None
        """
        try:
            text = section.get_text()

            # Look for common venue indicators
            venue_patterns = [
                r'Venue\s*:?\s*([^\n]+)',
                r'Location\s*:?\s*([^\n]+)',
                r'Place\s*:?\s*([^\n]+)',
                r'at\s+([A-Z][^,\n]+)',
            ]

            for pattern in venue_patterns:
                match = re.search(pattern, text, re.I)
                if match:
                    venue = match.group(1).strip()
                    # Clean up common suffixes
                    venue = re.sub(r'\s*\(.*\)', '', venue)
                    return venue[:100]  # Limit to 100 chars

        except Exception as e:
            logger.debug("venue_extraction_error", error=str(e))

        return None

    async def _extract_event_description(
        self, section: BeautifulSoup
    ) -> Optional[str]:
        """Extract event description.

        Args:
            section: BeautifulSoup element

        Returns:
            Description string or None
        """
        try:
            # Get all text content
            text = section.get_text()

            # Remove extra whitespace
            text = re.sub(r'\s+', ' ', text).strip()

            # Limit to 500 characters
            if len(text) > 500:
                text = text[:500] + "..."

            return text if text else None

        except Exception as e:
            logger.debug("description_extraction_error", error=str(e))

        return None

    async def _extract_structured_events(
        self, soup: BeautifulSoup, page_url: str
    ) -> List[Dict]:
        """Extract structured event data (schema.org, JSON-LD).

        Args:
            soup: BeautifulSoup object
            page_url: Page URL

        Returns:
            List of event dictionaries
        """
        events = []

        try:
            # Look for JSON-LD event data
            scripts = soup.find_all("script", type="application/ld+json")

            for script in scripts:
                try:
                    import json
                    data = json.loads(script.string)

                    if isinstance(data, list):
                        data = data

                    elif isinstance(data, dict):
                        if data.get("@type") == "Event":
                            event = {
                                "title": data.get("name", ""),
                                "date": data.get("startDate", ""),
                                "venue": data.get("location", {}).get("name", "")
                                if isinstance(data.get("location"), dict)
                                else data.get("location", ""),
                                "description": data.get("description", ""),
                                "source_url": page_url,
                            }
                            events.append(event)

                except Exception as e:
                    logger.debug("json_ld_parsing_error", error=str(e))

        except Exception as e:
            logger.debug("structured_event_extraction_error", error=str(e))

        return events
