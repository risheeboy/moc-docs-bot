"""Unified semantic search endpoint."""

from fastapi import APIRouter, Depends, HTTPException, Request, Query
from sqlalchemy.ext.asyncio import AsyncSession
from ..models import SearchRequest, SearchResponse, SearchSuggestRequest, SearchSuggestResponse
from ..dependencies import get_db, get_redis, verify_jwt_token, verify_api_key
from ..services.rag_client import RAGClient
from ..services.cache_service import CacheService
from ..config import get_settings
from datetime import datetime
import uuid
import logging

router = APIRouter(prefix="/api/v1", tags=["search"])
logger = logging.getLogger(__name__)


@router.get("/search", response_model=SearchResponse, tags=["search"])
async def search(
    query: str = Query(..., min_length=1, max_length=2000),
    language: str = Query(default="en"),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    request: Request = None,
    db: AsyncSession = Depends(get_db),
    redis = Depends(get_redis),
    settings = Depends(get_settings),
    _: any = Depends(verify_jwt_token) or Depends(verify_api_key),
):
    """Unified semantic search with AI summaries and multimedia."""
    request_id = getattr(request.state, "request_id", str(uuid.uuid4()))

    try:
        # Initialize clients
        rag_client = RAGClient(settings.rag_service_url)
        cache_service = CacheService(redis)

        # Check cache
        cache_key = cache_service.get_key(
            "search", query, language, str(page), str(page_size)
        )
        cached_result = await cache_service.get(cache_key)
        if cached_result:
            logger.info(f"Cache hit for search query", extra={"request_id": request_id})
            return SearchResponse(
                **cached_result,
                cached=True,
                request_id=request_id,
                timestamp=datetime.utcnow(),
            )

        # Perform search via RAG
        rag_response = await rag_client.search(
            query=query,
            language=language,
            page=page,
            page_size=page_size,
            filters={},
            request_id=request_id,
        )

        # Build response
        result = SearchResponse(
            results=rag_response.get("results", []),
            multimedia=rag_response.get("multimedia", []),
            events=rag_response.get("events", []),
            total_results=rag_response.get("total_results", 0),
            page=page,
            page_size=page_size,
            cached=False,
            request_id=request_id,
            timestamp=datetime.utcnow(),
        )

        # Cache result
        await cache_service.set(cache_key, result.model_dump(), settings.rag_cache_ttl_seconds)

        return result

    except Exception as e:
        logger.error(f"Search error: {e}", extra={"request_id": request_id})
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


@router.get("/search/suggest", response_model=SearchSuggestResponse, tags=["search"])
async def search_suggest(
    prefix: str = Query(..., min_length=1, max_length=100),
    language: str = Query(default="en"),
    limit: int = Query(default=10, ge=1, le=50),
    request: Request = None,
    redis = Depends(get_redis),
    settings = Depends(get_settings),
    _: any = Depends(verify_jwt_token) or Depends(verify_api_key),
):
    """Auto-complete suggestions for search."""
    request_id = getattr(request.state, "request_id", str(uuid.uuid4()))

    try:
        # For now, return empty suggestions
        # In production, implement trie-based suggestion engine
        suggestions = []

        return SearchSuggestResponse(
            suggestions=suggestions,
            request_id=request_id,
        )

    except Exception as e:
        logger.error(f"Search suggest error: {e}", extra={"request_id": request_id})
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
