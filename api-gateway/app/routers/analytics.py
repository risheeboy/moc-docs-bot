"""Analytics endpoints."""

from fastapi import APIRouter, Depends, HTTPException, Request, Query
from sqlalchemy.ext.asyncio import AsyncSession
from ..models import AnalyticsSummary, QueryStats
from ..dependencies import get_db, verify_jwt_token, verify_api_key
from datetime import datetime, timedelta
import uuid
import logging

router = APIRouter(prefix="/api/v1/analytics", tags=["analytics"])
logger = logging.getLogger(__name__)


@router.get("/summary", response_model=AnalyticsSummary, tags=["analytics"])
async def analytics_summary(
    days: int = Query(default=7, ge=1, le=365),
    request: Request = None,
    db: AsyncSession = Depends(get_db),
    _: any = Depends(verify_jwt_token) or Depends(verify_api_key),
):
    """Get analytics summary for a period."""
    request_id = getattr(request.state, "request_id", str(uuid.uuid4()))

    try:
        period_end = datetime.utcnow()
        period_start = period_end - timedelta(days=days)

        # TODO: Query actual data from database
        # For now, return mock data

        return AnalyticsSummary(
            total_queries=100,
            total_feedback=50,
            avg_response_time_ms=1234.5,
            avg_rating=4.2,
            languages={"en": 60, "hi": 40},
            top_queries=[
                QueryStats(
                    query="Ministry of Culture",
                    count=15,
                    avg_response_time_ms=1200.0,
                    success_rate=0.95,
                    most_common_language="en",
                )
            ],
            period_start=period_start,
            period_end=period_end,
            request_id=request_id,
            timestamp=datetime.utcnow(),
        )

    except Exception as e:
        logger.error(f"Analytics summary error: {e}", extra={"request_id": request_id})
        raise HTTPException(
            status_code=500,
            detail={
                "error": {
                    "code": "INTERNAL_ERROR",
                    "message": str(e),
                    "request_id": request_id,
                }
            },
        )


@router.get("/queries", tags=["analytics"])
async def analytics_queries(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    request: Request = None,
    db: AsyncSession = Depends(get_db),
    _: any = Depends(verify_jwt_token) or Depends(verify_api_key),
):
    """Get query analytics with pagination."""
    request_id = getattr(request.state, "request_id", str(uuid.uuid4()))

    try:
        # TODO: Query actual analytics from database
        return {
            "queries": [],
            "total": 0,
            "page": page,
            "page_size": page_size,
            "request_id": request_id,
        }

    except Exception as e:
        logger.error(f"Query analytics error: {e}", extra={"request_id": request_id})
        raise HTTPException(
            status_code=500,
            detail={
                "error": {
                    "code": "INTERNAL_ERROR",
                    "message": str(e),
                    "request_id": request_id,
                }
            },
        )
