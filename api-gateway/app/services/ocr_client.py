"""HTTP client for OCR service."""

import httpx
import logging

logger = logging.getLogger(__name__)


class OCRClient:
    """Client for OCR service API calls."""

    def __init__(self, base_url: str, timeout: float = 60.0):
        """Initialize OCR client."""
        self.base_url = base_url
        self.timeout = httpx.Timeout(timeout)

    async def ocr(
        self,
        file_bytes: bytes,
        filename: str,
        languages: str = "hi,en",
        engine: str = "auto",
        request_id: str = "",
    ) -> dict:
        """Call OCR service /ocr endpoint."""
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            files = {"file": (filename, file_bytes)}
            data = {"languages": languages, "engine": engine}

            headers = {"X-Request-ID": request_id}

            try:
                response = await client.post(
                    f"{self.base_url}/ocr", files=files, data=data, headers=headers
                )
                response.raise_for_status()
                return response.json()
            except httpx.HTTPError as e:
                logger.error(f"OCR service error: {e}", extra={"request_id": request_id})
                raise
