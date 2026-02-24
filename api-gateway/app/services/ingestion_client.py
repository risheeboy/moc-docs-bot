"""HTTP client for Data Ingestion service."""

import httpx
import logging

logger = logging.getLogger(__name__)


class IngestionClient:
    """Client for Data Ingestion service API calls."""

    def __init__(self, base_url: str, timeout: float = 30.0):
        """Initialize Ingestion client."""
        self.base_url = base_url
        self.timeout = httpx.Timeout(timeout)

    async def trigger_job(
        self,
        target_urls: list[str],
        spider_type: str = "auto",
        force_rescrape: bool = False,
        request_id: str = "",
    ) -> dict:
        """Call Ingestion service /jobs/trigger endpoint."""
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            payload = {
                "target_urls": target_urls,
                "spider_type": spider_type,
                "force_rescrape": force_rescrape,
            }

            headers = {"X-Request-ID": request_id}

            try:
                response = await client.post(
                    f"{self.base_url}/jobs/trigger", json=payload, headers=headers
                )
                response.raise_for_status()
                return response.json()
            except httpx.HTTPError as e:
                logger.error(
                    f"Ingestion trigger error: {e}", extra={"request_id": request_id}
                )
                raise

    async def get_job_status(
        self, job_id: str, request_id: str = ""
    ) -> dict:
        """Call Ingestion service /jobs/status endpoint."""
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            headers = {"X-Request-ID": request_id}

            try:
                response = await client.get(
                    f"{self.base_url}/jobs/status",
                    params={"job_id": job_id},
                    headers=headers,
                )
                response.raise_for_status()
                return response.json()
            except httpx.HTTPError as e:
                logger.error(
                    f"Ingestion status error: {e}", extra={"request_id": request_id}
                )
                raise
