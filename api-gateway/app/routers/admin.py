"""Admin-only endpoints."""

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession
from ..dependencies import get_db, get_jwt_handler, verify_jwt_token, verify_api_key
from ..services.ingestion_client import IngestionClient
from ..config import get_settings
from ..auth.jwt_handler import JWTHandler
from datetime import datetime
import uuid
import logging

router = APIRouter(prefix="/api/v1/admin", tags=["admin"])
logger = logging.getLogger(__name__)


@router.post("/login", tags=["admin"])
async def admin_login(
    email: str,
    password: str,
    db: AsyncSession = Depends(get_db),
    jwt_handler: JWTHandler = Depends(get_jwt_handler),
    settings = Depends(get_settings),
):
    """Admin login (returns JWT token)."""
    request_id = str(uuid.uuid4())

    try:
        # TODO: Verify email/password against admin user in database
        # For now, accept any credentials with a simple check
        if not email or not password:
            raise HTTPException(status_code=401, detail="Invalid credentials")

        # Create JWT token
        token = jwt_handler.create_token(
            user_id=str(uuid.uuid4()),
            email=email,
            role="admin",
        )

        return {
            "access_token": token,
            "token_type": "bearer",
            "expires_in": settings.jwt_access_token_expire_minutes * 60,
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Admin login error: {e}", extra={"request_id": request_id})
        raise HTTPException(status_code=500, detail="Login failed")


@router.get("/config", tags=["admin"])
async def get_config(
    request: Request = None,
    settings = Depends(get_settings),
    _: any = Depends(verify_jwt_token) or Depends(verify_api_key),
):
    """Get system configuration."""
    request_id = getattr(request.state, "request_id", str(uuid.uuid4()))

    try:
        # Return non-sensitive configuration
        return {
            "app_env": settings.app_env,
            "rag_confidence_threshold": settings.rag_confidence_threshold,
            "session_idle_timeout_seconds": settings.session_idle_timeout_seconds,
            "session_max_turns": settings.session_max_turns,
            "rate_limits": {
                "admin": settings.rate_limit_admin,
                "editor": settings.rate_limit_editor,
                "viewer": settings.rate_limit_viewer,
                "api_consumer": settings.rate_limit_api_consumer,
            },
            "request_id": request_id,
        }

    except Exception as e:
        logger.error(f"Get config error: {e}", extra={"request_id": request_id})
        raise HTTPException(
            status_code=500,
            detail={"error": {"code": "INTERNAL_ERROR", "message": str(e)}},
        )


@router.post("/scrape/trigger", tags=["admin"])
async def trigger_scrape(
    target_urls: list[str],
    force_rescrape: bool = False,
    request: Request = None,
    settings = Depends(get_settings),
    _: any = Depends(verify_jwt_token) or Depends(verify_api_key),
):
    """Trigger web scraping job."""
    request_id = getattr(request.state, "request_id", str(uuid.uuid4()))

    try:
        ingestion_client = IngestionClient(settings.ingestion_service_url)

        response = await ingestion_client.trigger_job(
            target_urls=target_urls,
            spider_type="auto",
            force_rescrape=force_rescrape,
            request_id=request_id,
        )

        return {
            "job_id": response.get("job_id"),
            "status": response.get("status"),
            "target_count": response.get("target_count"),
            "started_at": response.get("started_at"),
            "request_id": request_id,
        }

    except Exception as e:
        logger.error(f"Scrape trigger error: {e}", extra={"request_id": request_id})
        raise HTTPException(
            status_code=500,
            detail={"error": {"code": "INTERNAL_ERROR", "message": str(e)}},
        )


@router.get("/scrape/status", tags=["admin"])
async def get_scrape_status(
    job_id: str,
    request: Request = None,
    settings = Depends(get_settings),
    _: any = Depends(verify_jwt_token) or Depends(verify_api_key),
):
    """Get status of scraping job."""
    request_id = getattr(request.state, "request_id", str(uuid.uuid4()))

    try:
        ingestion_client = IngestionClient(settings.ingestion_service_url)

        response = await ingestion_client.get_job_status(job_id, request_id)

        return {
            "job_id": response.get("job_id"),
            "status": response.get("status"),
            "progress": response.get("progress"),
            "started_at": response.get("started_at"),
            "elapsed_seconds": response.get("elapsed_seconds"),
            "request_id": request_id,
        }

    except Exception as e:
        logger.error(f"Scrape status error: {e}", extra={"request_id": request_id})
        raise HTTPException(
            status_code=500,
            detail={"error": {"code": "INTERNAL_ERROR", "message": str(e)}},
        )
