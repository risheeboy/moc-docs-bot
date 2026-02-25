import pytest
import os
from unittest.mock import MagicMock, patch, AsyncMock
from fastapi.testclient import TestClient
from app.config import Settings

# Import app after router refactoring to lazy-load services
from app.main import app


@pytest.fixture
def mock_embedder():
    """Mock embedder service to avoid downloading models."""
    mock = MagicMock()

    # Create different embeddings for different texts to test similarity
    def embed_text_side_effect(text):
        import numpy as np
        if "The cat is on the mat" in text:
            # text1 - reference embedding
            vec = np.random.RandomState(1).randn(1024)
        elif "A cat sits on the mat" in text:
            # text2 - similar to text1 (add small noise)
            vec = np.random.RandomState(1).randn(1024) + np.random.RandomState(2).randn(1024) * 0.1
        elif "weather" in text.lower() or "sunny" in text.lower():
            # text3 - different
            vec = np.random.RandomState(3).randn(1024)
        else:
            # default
            vec = np.random.RandomState(4).randn(1024)

        return {"dense": vec.tolist(), "text": text}

    mock.embed_text = MagicMock(side_effect=embed_text_side_effect)
    mock.get_embedding_dimension = MagicMock(return_value=1024)
    mock.embed_batch = MagicMock(return_value=[
        {"dense": [0.1] * 1024, "text": "test1"},
        {"dense": [0.2] * 1024, "text": "test2"},
        {"dense": [0.3] * 1024, "text": "test3"},
    ])
    return mock


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
