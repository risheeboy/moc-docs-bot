"""HTTP client for Translation service."""

import httpx
import logging

logger = logging.getLogger(__name__)


class TranslationClient:
    """Client for Translation service API calls."""

    def __init__(self, base_url: str, timeout: float = 30.0):
        """Initialize Translation client."""
        self.base_url = base_url
        self.timeout = httpx.Timeout(timeout)

    async def translate(
        self,
        text: str,
        source_language: str,
        target_language: str,
        request_id: str = "",
    ) -> dict:
        """Call Translation service /translate endpoint."""
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            payload = {
                "text": text,
                "source_language": source_language,
                "target_language": target_language,
            }

            headers = {"X-Request-ID": request_id}

            try:
                response = await client.post(
                    f"{self.base_url}/translate", json=payload, headers=headers
                )
                response.raise_for_status()
                return response.json()
            except httpx.HTTPError as e:
                logger.error(
                    f"Translation service error: {e}", extra={"request_id": request_id}
                )
                raise

    async def translate_batch(
        self,
        texts: list[str],
        source_language: str,
        target_language: str,
        request_id: str = "",
    ) -> dict:
        """Call Translation service /translate/batch endpoint."""
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            payload = {
                "texts": texts,
                "source_language": source_language,
                "target_language": target_language,
            }

            headers = {"X-Request-ID": request_id}

            try:
                response = await client.post(
                    f"{self.base_url}/translate/batch",
                    json=payload,
                    headers=headers,
                )
                response.raise_for_status()
                return response.json()
            except httpx.HTTPError as e:
                logger.error(
                    f"Translation batch error: {e}", extra={"request_id": request_id}
                )
                raise

    async def detect(self, text: str, request_id: str = "") -> dict:
        """Call Translation service /detect endpoint."""
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            payload = {"text": text}

            headers = {"X-Request-ID": request_id}

            try:
                response = await client.post(
                    f"{self.base_url}/detect", json=payload, headers=headers
                )
                response.raise_for_status()
                return response.json()
            except httpx.HTTPError as e:
                logger.error(
                    f"Language detection error: {e}", extra={"request_id": request_id}
                )
                raise
