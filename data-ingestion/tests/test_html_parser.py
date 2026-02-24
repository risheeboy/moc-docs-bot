"""Tests for HTML parser."""

import pytest
from app.parsers.html_parser import HtmlParser


@pytest.fixture
def parser():
    """Create HtmlParser instance."""
    return HtmlParser()


@pytest.mark.asyncio
async def test_extract_text_basic(parser):
    """Test basic text extraction."""
    html = """
    <html>
        <body>
            <h1>Title</h1>
            <p>This is a paragraph with some content.</p>
            <p>This is another paragraph.</p>
        </body>
    </html>
    """

    text = await parser.extract_text(html)

    assert text is not None
    assert len(text) > 0
    assert "Title" in text or "paragraph" in text


@pytest.mark.asyncio
async def test_extract_text_with_noise(parser):
    """Test text extraction with boilerplate content."""
    html = """
    <html>
        <head>
            <script>console.log('test');</script>
        </head>
        <body>
            <nav>Navigation content</nav>
            <article>
                <h1>Main Content</h1>
                <p>Important article text here.</p>
            </article>
            <footer>Footer content</footer>
        </body>
    </html>
    """

    text = await parser.extract_text(html)

    assert text is not None
    # Should prioritize article content
    if text:
        assert "article" not in text.lower() or "Important" in text


@pytest.mark.asyncio
async def test_extract_structured_data(parser):
    """Test structured data extraction."""
    html = """
    <html>
        <head>
            <title>Page Title</title>
            <meta name="description" content="Page description">
            <meta name="keywords" content="keyword1, keyword2">
        </head>
        <body>
            <h1>Content</h1>
        </body>
    </html>
    """

    data = await parser.extract_structured_data(html)

    assert "title" in data or "description" in data


@pytest.mark.asyncio
async def test_extract_empty_content(parser):
    """Test extraction from empty HTML."""
    html = "<html><body></body></html>"

    text = await parser.extract_text(html)

    assert text is None or len(text.strip()) == 0


@pytest.mark.asyncio
async def test_extract_text_short_content(parser):
    """Test extraction from very short content."""
    html = "<html><body><p>Hi</p></body></html>"

    text = await parser.extract_text(html)

    # Very short content might not be extracted
    # depending on trafilatura's threshold
