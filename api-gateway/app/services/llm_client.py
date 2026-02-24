"""HTTP client for LLM service."""

import httpx
import logging
from typing import AsyncGenerator, Optional

logger = logging.getLogger(__name__)


class LLMClient:
    """Client for LLM service API calls (OpenAI-compatible)."""

    def __init__(self, base_url: str, timeout: float = 60.0):
        """Initialize LLM client."""
        self.base_url = base_url
        self.timeout = httpx.Timeout(timeout)

    async def chat_completion(
        self,
        model: str,
        messages: list[dict],
        temperature: float = 0.3,
        max_tokens: int = 1024,
        stream: bool = False,
        request_id: str = "",
    ) -> dict:
        """Call LLM service /v1/chat/completions endpoint."""
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            payload = {
                "model": model,
                "messages": messages,
                "temperature": temperature,
                "max_tokens": max_tokens,
                "stream": stream,
            }

            headers = {"X-Request-ID": request_id}

            try:
                response = await client.post(
                    f"{self.base_url}/v1/chat/completions",
                    json=payload,
                    headers=headers,
                )
                response.raise_for_status()
                return response.json()
            except httpx.HTTPError as e:
                logger.error(f"LLM service error: {e}", extra={"request_id": request_id})
                raise

    async def chat_completion_stream(
        self,
        model: str,
        messages: list[dict],
        temperature: float = 0.3,
        max_tokens: int = 1024,
        request_id: str = "",
    ) -> AsyncGenerator[str, None]:
        """Stream chat completion from LLM service."""
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            payload = {
                "model": model,
                "messages": messages,
                "temperature": temperature,
                "max_tokens": max_tokens,
                "stream": True,
            }

            headers = {"X-Request-ID": request_id}

            try:
                async with client.stream(
                    "POST",
                    f"{self.base_url}/v1/chat/completions",
                    json=payload,
                    headers=headers,
                ) as response:
                    response.raise_for_status()
                    async for line in response.aiter_lines():
                        if line.startswith("data: "):
                            data = line[6:].strip()
                            if data and data != "[DONE]":
                                yield data
            except httpx.HTTPError as e:
                logger.error(
                    f"LLM streaming error: {e}", extra={"request_id": request_id}
                )
                raise
