import pytest
import os
from fastapi.testclient import TestClient
from app.main import app
from app.config import Settings


@pytest.fixture
def client():
    """Provide FastAPI test client."""
    return TestClient(app)


@pytest.fixture
def sample_query():
    """Sample query for testing."""
    return {
        "query": "भारतीय संस्कृति मंत्रालय के बारे में बताइए",
        "language": "hi",
        "session_id": "test-session-123",
        "chat_history": [],
        "top_k": 10,
        "rerank_top_k": 5,
        "filters": {
            "source_sites": [],
            "content_type": None,
            "date_from": None,
            "date_to": None
        }
    }


@pytest.fixture
def sample_search():
    """Sample search request for testing."""
    return {
        "query": "Indian heritage sites",
        "language": "en",
        "page": 1,
        "page_size": 20,
        "filters": {
            "source_sites": [],
            "content_type": "webpage",
            "date_from": None,
            "date_to": None,
            "language": None
        }
    }


@pytest.fixture
def sample_ingest():
    """Sample document ingestion request."""
    return {
        "document_id": "doc-123",
        "title": "Ministry of Culture Overview",
        "source_url": "https://culture.gov.in/about",
        "source_site": "culture.gov.in",
        "content": """
        The Ministry of Culture is responsible for:
        1. Preserving Indian heritage
        2. Promoting cultural events
        3. Supporting art and artists
        """,
        "content_type": "webpage",
        "language": "en",
        "metadata": {
            "author": "Ministry of Culture",
            "published_date": "2025-01-15",
            "tags": ["culture", "heritage", "ministry"]
        },
        "images": []
    }
