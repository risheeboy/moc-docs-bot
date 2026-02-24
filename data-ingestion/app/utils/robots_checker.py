"""robots.txt checker for respecting crawl directives."""

import structlog
from typing import Optional
import asyncio

import httpx

logger = structlog.get_logger()


class RobotsChecker:
    """Check robots.txt compliance before crawling."""

    def __init__(self, respect_robots_txt: bool = True):
        """Initialize robots checker.

        Args:
            respect_robots_txt: Whether to enforce robots.txt rules
        """
        self.respect_robots_txt = respect_robots_txt
        self.robots_cache = {}  # Cache of robots.txt per domain

    async def is_allowed(self, url: str, user_agent: str) -> bool:
        """Check if URL is allowed by robots.txt.

        Args:
            url: URL to check
            user_agent: User-Agent string

        Returns:
            True if allowed, False if blocked
        """
        if not self.respect_robots_txt:
            return True

        try:
            from urllib.parse import urlparse
            from urllib.robotparser import RobotFileParser

            parsed_url = urlparse(url)
            domain = f"{parsed_url.scheme}://{parsed_url.netloc}"

            # Get robots.txt from cache or fetch it
            if domain not in self.robots_cache:
                robots_txt = await self._fetch_robots_txt(domain)
                self.robots_cache[domain] = robots_txt

            robots = self.robots_cache[domain]

            if robots is None:
                # No robots.txt or error fetching it - allow by default
                return True

            # Check if URL is allowed
            path = parsed_url.path
            if not path:
                path = "/"

            allowed = robots.can_fetch(user_agent, path)

            if not allowed:
                logger.warning(
                    "url_blocked_by_robots_txt",
                    url=url,
                    domain=domain,
                )

            return allowed

        except Exception as e:
            logger.warning(
                "robots_txt_check_error",
                url=url,
                error=str(e),
            )
            # Allow by default if error occurs
            return True

    async def _fetch_robots_txt(self, domain: str) -> Optional["RobotFileParser"]:
        """Fetch and parse robots.txt from domain.

        Args:
            domain: Domain base URL

        Returns:
            RobotFileParser object or None
        """
        try:
            from urllib.robotparser import RobotFileParser

            robots_url = f"{domain}/robots.txt"

            async with httpx.AsyncClient(timeout=10) as client:
                response = await client.get(robots_url)

                if response.status_code == 200:
                    robot_parser = RobotFileParser()
                    robot_parser.parse(response.text.split("\n"))

                    logger.debug(
                        "robots_txt_fetched",
                        domain=domain,
                    )

                    return robot_parser

                else:
                    logger.debug(
                        "robots_txt_not_found",
                        domain=domain,
                        status=response.status_code,
                    )
                    return None

        except Exception as e:
            logger.warning(
                "robots_txt_fetch_error",
                domain=domain,
                error=str(e),
            )
            return None

    def clear_cache(self):
        """Clear robots.txt cache."""
        self.robots_cache.clear()
        logger.debug("robots_cache_cleared")


class CrawlDelay:
    """Handle crawl delay and rate limiting from robots.txt."""

    def __init__(self, default_delay: float = 1.0):
        """Initialize crawl delay manager.

        Args:
            default_delay: Default delay in seconds
        """
        self.default_delay = default_delay
        self.domain_delays = {}  # Map of domain -> delay in seconds

    async def get_delay(self, url: str, user_agent: str) -> float:
        """Get crawl delay for URL's domain.

        Args:
            url: URL to check
            user_agent: User-Agent string

        Returns:
            Delay in seconds
        """
        try:
            from urllib.parse import urlparse
            from urllib.robotparser import RobotFileParser

            parsed_url = urlparse(url)
            domain = f"{parsed_url.scheme}://{parsed_url.netloc}"

            if domain in self.domain_delays:
                return self.domain_delays[domain]

            # Try to get crawl delay from robots.txt
            robots_url = f"{domain}/robots.txt"

            async with httpx.AsyncClient(timeout=10) as client:
                response = await client.get(robots_url)

                if response.status_code == 200:
                    robot_parser = RobotFileParser()
                    robot_parser.parse(response.text.split("\n"))

                    delay = robot_parser.request_rate(user_agent)

                    if delay:
                        # request_rate returns requests per delay
                        actual_delay = delay.delay or self.default_delay
                    else:
                        actual_delay = self.default_delay

                    self.domain_delays[domain] = actual_delay
                    return actual_delay

        except Exception as e:
            logger.debug(
                "crawl_delay_fetch_error",
                url=url,
                error=str(e),
            )

        return self.default_delay

    def set_delay(self, domain: str, delay: float):
        """Manually set crawl delay for domain.

        Args:
            domain: Domain URL
            delay: Delay in seconds
        """
        self.domain_delays[domain] = delay
        logger.debug(
            "crawl_delay_set",
            domain=domain,
            delay=delay,
        )
