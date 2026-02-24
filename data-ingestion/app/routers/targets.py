"""CRUD endpoints for scrape targets (Ministry websites)."""

import uuid
import structlog
from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, Request, HTTPException, Query
from pydantic import BaseModel, Field

logger = structlog.get_logger()
router = APIRouter()

# In-memory target store (in production, use database)
_targets: dict = {}


class ScrapeTarget(BaseModel):
    """Configuration for a website to scrape."""
    target_id: str = Field(..., description="Unique target ID")
    name: str = Field(..., description="Target name")
    base_url: str = Field(..., description="Base URL to scrape")
    spider_type: str = Field(
        default="auto",
        description="Spider type: 'auto', 'static', 'dynamic', 'pdf', 'media'",
    )
    content_selectors: dict = Field(
        default_factory=dict, description="CSS/XPath selectors for content extraction"
    )
    exclude_patterns: List[str] = Field(
        default_factory=list, description="URL patterns to exclude"
    )
    scrape_interval_hours: int = Field(default=24, ge=1)
    enabled: bool = Field(default=True)
    created_at: datetime = Field(...)
    updated_at: datetime = Field(...)


class CreateTargetRequest(BaseModel):
    """Request to create a scrape target."""
    name: str = Field(..., description="Target name")
    base_url: str = Field(..., description="Base URL to scrape")
    spider_type: str = Field(default="auto")
    content_selectors: dict = Field(default_factory=dict)
    exclude_patterns: List[str] = Field(default_factory=list)
    scrape_interval_hours: int = Field(default=24, ge=1)


class UpdateTargetRequest(BaseModel):
    """Request to update a scrape target."""
    name: Optional[str] = None
    spider_type: Optional[str] = None
    content_selectors: Optional[dict] = None
    exclude_patterns: Optional[List[str]] = None
    scrape_interval_hours: Optional[int] = None
    enabled: Optional[bool] = None


class TargetListResponse(BaseModel):
    """Response with list of targets."""
    targets: List[ScrapeTarget]
    total: int


@router.get("", response_model=TargetListResponse)
async def list_targets(
    request: Request,
    enabled_only: bool = Query(False, description="Filter only enabled targets"),
) -> TargetListResponse:
    """List all scrape targets."""
    request_id = getattr(request.state, "request_id", str(uuid.uuid4()))

    targets = list(_targets.values())

    if enabled_only:
        targets = [t for t in targets if t.enabled]

    logger.info(
        "targets_listed",
        count=len(targets),
        enabled_only=enabled_only,
        request_id=request_id,
    )

    return TargetListResponse(targets=targets, total=len(targets))


@router.get("/{target_id}", response_model=ScrapeTarget)
async def get_target(request: Request, target_id: str) -> ScrapeTarget:
    """Get a specific scrape target."""
    request_id = getattr(request.state, "request_id", str(uuid.uuid4()))

    if target_id not in _targets:
        logger.warning(
            "target_not_found",
            target_id=target_id,
            request_id=request_id,
        )
        raise HTTPException(
            status_code=404,
            detail={
                "error": {
                    "code": "NOT_FOUND",
                    "message": f"Target {target_id} not found",
                    "request_id": request_id,
                }
            },
        )

    return _targets[target_id]


@router.post("", response_model=ScrapeTarget)
async def create_target(
    request: Request, target_request: CreateTargetRequest
) -> ScrapeTarget:
    """Create a new scrape target."""
    request_id = getattr(request.state, "request_id", str(uuid.uuid4()))

    target_id = str(uuid.uuid4())
    now = datetime.utcnow()

    target = ScrapeTarget(
        target_id=target_id,
        name=target_request.name,
        base_url=target_request.base_url,
        spider_type=target_request.spider_type,
        content_selectors=target_request.content_selectors,
        exclude_patterns=target_request.exclude_patterns,
        scrape_interval_hours=target_request.scrape_interval_hours,
        created_at=now,
        updated_at=now,
    )

    _targets[target_id] = target

    logger.info(
        "target_created",
        target_id=target_id,
        name=target.name,
        base_url=target.base_url,
        request_id=request_id,
    )

    return target


@router.put("/{target_id}", response_model=ScrapeTarget)
async def update_target(
    request: Request,
    target_id: str,
    target_request: UpdateTargetRequest,
) -> ScrapeTarget:
    """Update a scrape target."""
    request_id = getattr(request.state, "request_id", str(uuid.uuid4()))

    if target_id not in _targets:
        raise HTTPException(
            status_code=404,
            detail={
                "error": {
                    "code": "NOT_FOUND",
                    "message": f"Target {target_id} not found",
                    "request_id": request_id,
                }
            },
        )

    target = _targets[target_id]

    # Update fields
    if target_request.name is not None:
        target.name = target_request.name
    if target_request.spider_type is not None:
        target.spider_type = target_request.spider_type
    if target_request.content_selectors is not None:
        target.content_selectors = target_request.content_selectors
    if target_request.exclude_patterns is not None:
        target.exclude_patterns = target_request.exclude_patterns
    if target_request.scrape_interval_hours is not None:
        target.scrape_interval_hours = target_request.scrape_interval_hours
    if target_request.enabled is not None:
        target.enabled = target_request.enabled

    target.updated_at = datetime.utcnow()

    logger.info(
        "target_updated",
        target_id=target_id,
        request_id=request_id,
    )

    return target


@router.delete("/{target_id}")
async def delete_target(request: Request, target_id: str) -> dict:
    """Delete a scrape target."""
    request_id = getattr(request.state, "request_id", str(uuid.uuid4()))

    if target_id not in _targets:
        raise HTTPException(
            status_code=404,
            detail={
                "error": {
                    "code": "NOT_FOUND",
                    "message": f"Target {target_id} not found",
                    "request_id": request_id,
                }
            },
        )

    del _targets[target_id]

    logger.info(
        "target_deleted",
        target_id=target_id,
        request_id=request_id,
    )

    return {"success": True, "target_id": target_id}
