"""Base HTTP client with retry, timeout, and request ID propagation (§7)."""

from typing import Any, Optional
from datetime import timedelta
import httpx
from tenacity import (
    retry,
    retry_if_exception_type,
    wait_exponential,
    stop_after_attempt,
)
import uuid
import logging

logger = logging.getLogger(__name__)


class BaseHTTPClient:
    """Base HTTP client with built-in retry logic and request ID propagation.

    Features:
    - Automatic X-Request-ID propagation from incoming requests to outbound calls
    - Exponential backoff retry on transient failures
    - Connection pooling and timeout management
    - Structured error handling
    """

    def __init__(
        self,
        base_url: str,
        timeout: float = 30.0,
        max_retries: int = 3,
        request_id: Optional[str] = None,
    ):
        """Initialize HTTP client.

        Args:
            base_url: Base URL for all requests
            timeout: Request timeout in seconds
            max_retries: Maximum number of retry attempts
            request_id: Optional X-Request-ID to propagate (generates new one if None)
        """
        self.base_url = base_url
        self.timeout = httpx.Timeout(timeout)
        self.max_retries = max_retries
        self.request_id = request_id or str(uuid.uuid4())

        # Create client with connection pooling
        limits = httpx.Limits(max_keepalive_connections=10, max_connections=50)
        self.client = httpx.AsyncClient(
            base_url=base_url,
            timeout=self.timeout,
            limits=limits,
        )

    def _get_headers(self, extra_headers: Optional[dict[str, str]] = None) -> dict[str, str]:
        """Build request headers with X-Request-ID propagation.

        Args:
            extra_headers: Additional headers to include

        Returns:
            Complete headers dictionary
        """
        headers = {
            "X-Request-ID": self.request_id,
            "User-Agent": "RAG-QA-System/1.0",
        }
        if extra_headers:
            headers.update(extra_headers)
        return headers

    @retry(
        retry=retry_if_exception_type(httpx.RequestError),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        stop=stop_after_attempt(3),
        reraise=True,
    )
    async def get(
        self,
        path: str,
        params: Optional[dict[str, Any]] = None,
        headers: Optional[dict[str, str]] = None,
    ) -> httpx.Response:
        """Make GET request with automatic retry.

        Args:
            path: Endpoint path (relative to base_url)
            params: Query parameters
            headers: Additional headers

        Returns:
            Response object

        Raises:
            httpx.RequestError: If request fails after retries
        """
        request_headers = self._get_headers(headers)
        response = await self.client.get(
            path,
            params=params,
            headers=request_headers,
        )
        response.raise_for_status()
        return response

    @retry(
        retry=retry_if_exception_type(httpx.RequestError),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        stop=stop_after_attempt(3),
        reraise=True,
    )
    async def post(
        self,
        path: str,
        data: Optional[dict[str, Any]] = None,
        json: Optional[dict[str, Any]] = None,
        headers: Optional[dict[str, str]] = None,
    ) -> httpx.Response:
        """Make POST request with automatic retry.

        Args:
            path: Endpoint path
            data: Form data
            json: JSON body
            headers: Additional headers

        Returns:
            Response object

        Raises:
            httpx.RequestError: If request fails after retries
        """
        request_headers = self._get_headers(headers)
        response = await self.client.post(
            path,
            data=data,
            json=json,
            headers=request_headers,
        )
        response.raise_for_status()
        return response

    @retry(
        retry=retry_if_exception_type(httpx.RequestError),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        stop=stop_after_attempt(3),
        reraise=True,
    )
    async def put(
        self,
        path: str,
        json: Optional[dict[str, Any]] = None,
        headers: Optional[dict[str, str]] = None,
    ) -> httpx.Response:
        """Make PUT request with automatic retry.

        Args:
            path: Endpoint path
            json: JSON body
            headers: Additional headers

        Returns:
            Response object

        Raises:
            httpx.RequestError: If request fails after retries
        """
        request_headers = self._get_headers(headers)
        response = await self.client.put(
            path,
            json=json,
            headers=request_headers,
        )
        response.raise_for_status()
        return response

    @retry(
        retry=retry_if_exception_type(httpx.RequestError),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        stop=stop_after_attempt(3),
        reraise=True,
    )
    async def delete(
        self,
        path: str,
        headers: Optional[dict[str, str]] = None,
    ) -> httpx.Response:
        """Make DELETE request with automatic retry.

        Args:
            path: Endpoint path
            headers: Additional headers

        Returns:
            Response object

        Raises:
            httpx.RequestError: If request fails after retries
        """
        request_headers = self._get_headers(headers)
        response = await self.client.delete(
            path,
            headers=request_headers,
        )
        response.raise_for_status()
        return response

    async def stream(
        self,
        method: str,
        path: str,
        json: Optional[dict[str, Any]] = None,
        headers: Optional[dict[str, str]] = None,
    ) -> httpx.AsyncIterator:
        """Stream response from server (for SSE).

        Args:
            method: HTTP method
            path: Endpoint path
            json: JSON body
            headers: Additional headers

        Returns:
            Async iterator over response lines

        Raises:
            httpx.RequestError: If request fails
        """
        request_headers = self._get_headers(headers)
        return await self.client.stream(
            method,
            path,
            json=json,
            headers=request_headers,
        )

    async def close(self) -> None:
        """Close HTTP client and clean up resources."""
        await self.client.aclose()

    async def __aenter__(self) -> "BaseHTTPClient":
        """Async context manager entry."""
        return self

    async def __aexit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        """Async context manager exit."""
        await self.close()
