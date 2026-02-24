"""HTTP client for RAG service."""

import httpx
import logging
from typing import Optional, Any
from datetime import datetime

logger = logging.getLogger(__name__)


class RAGClient:
    """Client for RAG service API calls."""

    def __init__(self, base_url: str, timeout: float = 30.0):
        """Initialize RAG client."""
        self.base_url = base_url
        self.timeout = httpx.Timeout(timeout)

    async def query(
        self,
        query: str,
        language: str,
        session_id: str,
        chat_history: list,
        top_k: int,
        rerank_top_k: int,
        filters: dict,
        request_id: str,
    ) -> dict:
        """Call RAG service /query endpoint."""
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            payload = {
                "query": query,
                "language": language,
                "session_id": session_id,
                "chat_history": chat_history,
                "top_k": top_k,
                "rerank_top_k": rerank_top_k,
                "filters": filters,
            }

            headers = {"X-Request-ID": request_id}

            try:
                response = await client.post(
                    f"{self.base_url}/query", json=payload, headers=headers
                )
                response.raise_for_status()
                return response.json()
            except httpx.HTTPError as e:
                logger.error(f"RAG service error: {e}", extra={"request_id": request_id})
                raise

    async def search(
        self,
        query: str,
        language: str,
        page: int,
        page_size: int,
        filters: dict,
        request_id: str,
    ) -> dict:
        """Call RAG service /search endpoint."""
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            payload = {
                "query": query,
                "language": language,
                "page": page,
                "page_size": page_size,
                "filters": filters,
            }

            headers = {"X-Request-ID": request_id}

            try:
                response = await client.post(
                    f"{self.base_url}/search", json=payload, headers=headers
                )
                response.raise_for_status()
                return response.json()
            except httpx.HTTPError as e:
                logger.error(f"RAG search error: {e}", extra={"request_id": request_id})
                raise

    async def ingest(
        self,
        document_id: str,
        title: str,
        source_url: str,
        source_site: str,
        content: str,
        content_type: str,
        language: str,
        metadata: dict,
        images: list,
        request_id: str,
    ) -> dict:
        """Call RAG service /ingest endpoint."""
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            payload = {
                "document_id": document_id,
                "title": title,
                "source_url": source_url,
                "source_site": source_site,
                "content": content,
                "content_type": content_type,
                "language": language,
                "metadata": metadata,
                "images": images,
            }

            headers = {"X-Request-ID": request_id}

            try:
                response = await client.post(
                    f"{self.base_url}/ingest", json=payload, headers=headers
                )
                response.raise_for_status()
                return response.json()
            except httpx.HTTPError as e:
                logger.error(f"RAG ingest error: {e}", extra={"request_id": request_id})
                raise
