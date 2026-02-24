"""Extract structured data (JSON-LD, schema.org) from web pages."""

import structlog
from typing import Dict, List, Any, Optional
import json
import re

from bs4 import BeautifulSoup

logger = structlog.get_logger()


class StructuredDataExtractor:
    """Extractor for structured data from web pages."""

    async def extract(self, soup: BeautifulSoup) -> Dict[str, Any]:
        """Extract all structured data from HTML page.

        Args:
            soup: BeautifulSoup object

        Returns:
            Dictionary with extracted structured data
        """
        structured_data = {
            "json_ld": await self._extract_json_ld(soup),
            "microdata": await self._extract_microdata(soup),
            "opengraph": await self._extract_opengraph(soup),
            "twitter_card": await self._extract_twitter_card(soup),
        }

        return structured_data

    async def _extract_json_ld(self, soup: BeautifulSoup) -> List[Dict]:
        """Extract JSON-LD structured data.

        Args:
            soup: BeautifulSoup object

        Returns:
            List of JSON-LD objects
        """
        json_ld_data = []

        try:
            scripts = soup.find_all("script", type="application/ld+json")

            for script in scripts:
                try:
                    data = json.loads(script.string)
                    json_ld_data.append(data)

                except json.JSONDecodeError as e:
                    logger.debug("json_ld_parsing_error", error=str(e))

        except Exception as e:
            logger.warning("json_ld_extraction_error", error=str(e))

        return json_ld_data

    async def _extract_microdata(self, soup: BeautifulSoup) -> Dict[str, List[Dict]]:
        """Extract microdata (schema.org itemscope).

        Args:
            soup: BeautifulSoup object

        Returns:
            Dictionary with microdata
        """
        microdata = {}

        try:
            # Find all elements with itemscope
            items = soup.find_all(attrs={"itemscope": True})

            for item in items:
                item_type = item.get("itemtype", "unknown")

                if item_type not in microdata:
                    microdata[item_type] = []

                item_data = {}

                # Extract all properties within this item
                for prop in item.find_all(attrs={"itemprop": True}):
                    prop_name = prop.get("itemprop")

                    # Get value from content attribute or text
                    if prop.get("content"):
                        value = prop["content"]
                    else:
                        value = prop.get_text().strip()

                    if prop_name not in item_data:
                        item_data[prop_name] = []

                    if value:
                        item_data[prop_name].append(value)

                if item_data:
                    microdata[item_type].append(item_data)

        except Exception as e:
            logger.warning("microdata_extraction_error", error=str(e))

        return microdata

    async def _extract_opengraph(self, soup: BeautifulSoup) -> Dict[str, str]:
        """Extract Open Graph meta tags.

        Args:
            soup: BeautifulSoup object

        Returns:
            Dictionary with Open Graph properties
        """
        og_data = {}

        try:
            og_tags = soup.find_all("meta", attrs={"property": re.compile(r"^og:")})

            for tag in og_tags:
                property_name = tag.get("property", "").replace("og:", "")
                content = tag.get("content", "")

                if property_name and content:
                    og_data[property_name] = content

        except Exception as e:
            logger.warning("opengraph_extraction_error", error=str(e))

        return og_data

    async def _extract_twitter_card(self, soup: BeautifulSoup) -> Dict[str, str]:
        """Extract Twitter Card meta tags.

        Args:
            soup: BeautifulSoup object

        Returns:
            Dictionary with Twitter Card properties
        """
        twitter_data = {}

        try:
            twitter_tags = soup.find_all(
                "meta", attrs={"name": re.compile(r"^twitter:")}
            )

            for tag in twitter_tags:
                name = tag.get("name", "").replace("twitter:", "")
                content = tag.get("content", "")

                if name and content:
                    twitter_data[name] = content

        except Exception as e:
            logger.warning("twitter_card_extraction_error", error=str(e))

        return twitter_data

    @staticmethod
    def flatten_json_ld(json_ld: Dict) -> Dict[str, Any]:
        """Flatten JSON-LD object for easier access.

        Args:
            json_ld: JSON-LD object

        Returns:
            Flattened dictionary
        """
        flattened = {}

        def flatten(obj, prefix=""):
            if isinstance(obj, dict):
                for key, value in obj.items():
                    new_key = f"{prefix}.{key}" if prefix else key
                    flatten(value, new_key)
            elif isinstance(obj, list):
                for i, item in enumerate(obj):
                    new_key = f"{prefix}[{i}]"
                    flatten(item, new_key)
            else:
                flattened[prefix] = obj

        flatten(json_ld)
        return flattened
