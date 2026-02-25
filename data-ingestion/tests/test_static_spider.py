"""Tests for static HTML spider."""

import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, patch

from app.scrapers.static_spider import StaticSpider


@pytest.fixture
def spider():
    """Create a StaticSpider instance for testing."""
    return StaticSpider(
        target_url="https://example.com",
        job_id="test-job-001",
        max_pages=10,
    )


@pytest.mark.asyncio
async def test_spider_initialization(spider):
    """Test spider initialization."""
    assert spider.target_url == "https://example.com"
    assert spider.job_id == "test-job-001"
    assert spider.spider_type == "static"
    assert spider.pages_crawled == 0
    assert spider.documents_found == 0


@pytest.mark.asyncio
async def test_extract_links():
    """Test link extraction from HTML."""
    spider = StaticSpider("https://example.com")

    html = """
    <html>
        <body>
            <a href="/page1">Page 1</a>
            <a href="https://example.com/page2">Page 2</a>
            <a href="https://other.com/page">External</a>
        </body>
    </html>
    """

    links = await spider._extract_links(html)

    assert len(links) > 0
    assert any("example.com" in link for link in links)


@pytest.mark.asyncio
async def test_extract_images():
    """Test image extraction from HTML."""
    from bs4 import BeautifulSoup

    spider = StaticSpider("https://example.com")

    html = """
    <html>
        <body>
            <img src="/image1.jpg" alt="Image 1">
            <img src="https://example.com/image2.png" alt="Image 2">
        </body>
    </html>
    """

    soup = BeautifulSoup(html, "html.parser")
    images = await spider._extract_images(soup, "https://example.com")

    assert len(images) == 2
    assert images[0]["alt_text"] == "Image 1"


@pytest.mark.asyncio
async def test_should_crawl_validation(spider):
    """Test URL validation for crawling."""
    # Same domain - should crawl
    assert await spider.should_crawl("https://example.com/page")

    # Different domain - should not crawl
    assert not await spider.should_crawl("https://other.com/page")


def test_get_stats(spider):
    """Test stats collection."""
    spider.pages_crawled = 5
    spider.documents_found = 3
    spider.errors = 1

    stats = spider.get_stats()

    assert stats["pages_crawled"] == 5
    assert stats["documents_found"] == 3
    assert stats["errors"] == 1


@pytest.mark.asyncio
async def test_spider_cleanup(spider):
    """Test spider cleanup."""
    await spider.cleanup()
    # Should not raise any errors
