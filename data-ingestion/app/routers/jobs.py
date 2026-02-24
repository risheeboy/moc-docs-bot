"""Job management endpoints for web scraping and ingestion."""

import uuid
import structlog
import asyncio
from datetime import datetime
from typing import List, Optional
from enum import Enum

from fastapi import APIRouter, Request, HTTPException, Query
from pydantic import BaseModel, Field

from app.config import settings
from app.utils.metrics import (
    job_counter,
    scrape_pages_total,
    documents_ingested_total,
    ingestion_errors_total,
)

logger = structlog.get_logger()
router = APIRouter()

# In-memory job store (in production, use database)
_jobs: dict = {}


class JobStatus(str, Enum):
    """Job status enum."""
    STARTED = "started"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    PAUSED = "paused"


class JobProgress(BaseModel):
    """Job progress tracking."""
    pages_crawled: int = Field(default=0, ge=0)
    pages_total: int = Field(default=0, ge=0)
    documents_ingested: int = Field(default=0, ge=0)
    errors: int = Field(default=0, ge=0)


class TriggerJobRequest(BaseModel):
    """Request to trigger a scraping job."""
    target_urls: List[str] = Field(
        ..., description="List of target URLs to scrape"
    )
    spider_type: str = Field(
        default="auto",
        description="Type of spider: 'auto', 'static', 'dynamic', 'pdf', 'media'",
    )
    force_rescrape: bool = Field(
        default=False, description="Force re-scraping even if content is up-to-date"
    )


class TriggerJobResponse(BaseModel):
    """Response from job trigger."""
    job_id: str = Field(..., description="Unique job ID")
    status: str = Field(..., description="Job status")
    target_count: int = Field(..., description="Number of target URLs")
    started_at: datetime = Field(..., description="Job start time")


class JobStatusRequest(BaseModel):
    """Request to get job status."""
    job_id: str = Field(..., description="Job ID")


class JobStatusResponse(BaseModel):
    """Response from job status query."""
    job_id: str = Field(..., description="Unique job ID")
    status: str = Field(..., description="Job status")
    progress: JobProgress = Field(..., description="Job progress")
    started_at: datetime = Field(..., description="Job start time")
    elapsed_seconds: float = Field(..., description="Time elapsed since start")


class ErrorResponse(BaseModel):
    """Standard error response."""
    error: dict = Field(...)


async def simulate_scraping_job(
    job_id: str, target_urls: List[str], force_rescrape: bool
):
    """Simulate a scraping and ingestion job."""
    try:
        logger.info(
            "scraping_job_started",
            job_id=job_id,
            target_count=len(target_urls),
        )

        job = _jobs[job_id]
        job["status"] = JobStatus.RUNNING

        # Simulate crawling and ingestion
        total_pages = len(target_urls) * 50  # Assume ~50 pages per site
        job["progress"]["pages_total"] = total_pages

        for i in range(total_pages):
            job["progress"]["pages_crawled"] = i + 1

            # Simulate ingestion of every 5th page
            if (i + 1) % 5 == 0:
                job["progress"]["documents_ingested"] += 1

            # Simulate occasional errors
            if (i + 1) % 100 == 0 and (i + 1) % 50 != 0:
                job["progress"]["errors"] += 1
                ingestion_errors_total.inc()

            scrape_pages_total.inc()

            # Simulate processing time
            await asyncio.sleep(0.01)

        documents_ingested_total.add(job["progress"]["documents_ingested"])
        job["status"] = JobStatus.COMPLETED
        job["completed_at"] = datetime.utcnow()

        logger.info(
            "scraping_job_completed",
            job_id=job_id,
            pages_crawled=job["progress"]["pages_crawled"],
            documents_ingested=job["progress"]["documents_ingested"],
            errors=job["progress"]["errors"],
        )

    except Exception as e:
        logger.error(
            "scraping_job_failed",
            job_id=job_id,
            error=str(e),
            exc_info=True,
        )
        job = _jobs.get(job_id)
        if job:
            job["status"] = JobStatus.FAILED
            job["error_message"] = str(e)


@router.post("/trigger", response_model=TriggerJobResponse)
async def trigger_job(
    request: Request, job_request: TriggerJobRequest
) -> TriggerJobResponse:
    """Trigger a new scraping and ingestion job.

    Per §8.6: POST /jobs/trigger
    """
    request_id = getattr(request.state, "request_id", str(uuid.uuid4()))

    # Validate request
    if not job_request.target_urls:
        raise HTTPException(
            status_code=400,
            detail={
                "error": {
                    "code": "INVALID_REQUEST",
                    "message": "target_urls cannot be empty",
                    "request_id": request_id,
                }
            },
        )

    job_id = str(uuid.uuid4())
    now = datetime.utcnow()

    # Create job record
    job = {
        "job_id": job_id,
        "status": JobStatus.STARTED,
        "target_urls": job_request.target_urls,
        "spider_type": job_request.spider_type,
        "force_rescrape": job_request.force_rescrape,
        "progress": {
            "pages_crawled": 0,
            "pages_total": 0,
            "documents_ingested": 0,
            "errors": 0,
        },
        "started_at": now,
        "completed_at": None,
        "error_message": None,
    }

    _jobs[job_id] = job
    job_counter.inc()

    logger.info(
        "job_triggered",
        job_id=job_id,
        target_count=len(job_request.target_urls),
        spider_type=job_request.spider_type,
        request_id=request_id,
    )

    # Start job asynchronously
    asyncio.create_task(
        simulate_scraping_job(
            job_id, job_request.target_urls, job_request.force_rescrape
        )
    )

    return TriggerJobResponse(
        job_id=job_id,
        status=JobStatus.STARTED.value,
        target_count=len(job_request.target_urls),
        started_at=now,
    )


@router.get("/status", response_model=JobStatusResponse)
async def get_job_status(
    request: Request,
    job_id: str = Query(..., description="Job ID to query"),
) -> JobStatusResponse:
    """Get the status of a scraping job.

    Per §8.6: GET /jobs/status?job_id=uuid
    """
    request_id = getattr(request.state, "request_id", str(uuid.uuid4()))

    if job_id not in _jobs:
        logger.warning(
            "job_not_found",
            job_id=job_id,
            request_id=request_id,
        )
        raise HTTPException(
            status_code=404,
            detail={
                "error": {
                    "code": "NOT_FOUND",
                    "message": f"Job {job_id} not found",
                    "request_id": request_id,
                }
            },
        )

    job = _jobs[job_id]
    elapsed_seconds = (datetime.utcnow() - job["started_at"]).total_seconds()

    return JobStatusResponse(
        job_id=job_id,
        status=job["status"].value,
        progress=JobProgress(**job["progress"]),
        started_at=job["started_at"],
        elapsed_seconds=elapsed_seconds,
    )
