"""HTTP client for Speech service."""

import httpx
import logging
from typing import Optional

logger = logging.getLogger(__name__)


class SpeechClient:
    """Client for Speech service API calls."""

    def __init__(self, base_url: str, timeout: float = 30.0):
        """Initialize Speech client."""
        self.base_url = base_url
        self.timeout = httpx.Timeout(timeout)

    async def stt(
        self, audio_bytes: bytes, language: str = "auto", request_id: str = ""
    ) -> dict:
        """Call Speech service /stt endpoint for transcription."""
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            files = {"audio": ("audio.wav", audio_bytes, "audio/wav")}
            data = {"language": language}

            headers = {"X-Request-ID": request_id}

            try:
                response = await client.post(
                    f"{self.base_url}/stt", files=files, data=data, headers=headers
                )
                response.raise_for_status()
                return response.json()
            except httpx.HTTPError as e:
                logger.error(f"Speech STT error: {e}", extra={"request_id": request_id})
                raise

    async def tts(
        self,
        text: str,
        language: str,
        format: str = "mp3",
        voice: str = "default",
        request_id: str = "",
    ) -> bytes:
        """Call Speech service /tts endpoint for synthesis."""
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            payload = {
                "text": text,
                "language": language,
                "format": format,
                "voice": voice,
            }

            headers = {"X-Request-ID": request_id}

            try:
                response = await client.post(
                    f"{self.base_url}/tts", json=payload, headers=headers
                )
                response.raise_for_status()
                return response.content
            except httpx.HTTPError as e:
                logger.error(f"Speech TTS error: {e}", extra={"request_id": request_id})
                raise
