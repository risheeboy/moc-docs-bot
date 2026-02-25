from fastapi import APIRouter, HTTPException, Header
from typing import Optional
import uuid
import logging
import time
from app.models.request import SearchRequest
from app.models.response import SearchResponse, SearchResult, MultimediaResult, EventResult, ErrorResponse, ErrorDetail
from app.config import settings

router = APIRouter()
logger = logging.getLogger(__name__)

# Lazy-loaded services
_retriever = None
_cache_service = None

def get_retriever():
    global _retriever
    if _retriever is None:
        from app.services.retriever import RetrieverService
        _retriever = RetrieverService()
    return _retriever

def get_cache_service():
    global _cache_service
    if _cache_service is None:
        from app.services.cache_service import CacheService
        _cache_service = CacheService()
    return _cache_service


@router.post("/search", response_model=SearchResponse)
async def search_endpoint(
    request: SearchRequest,
    x_request_id: Optional[str] = Header(None)
) -> SearchResponse:
    """
    Semantic search with pagination, multimedia, and events.

    Supports filters by source site, content type, date range, and language.
    Returns paginated results with AI-generated snippets, thumbnails, and related events.
    """
    request_id = x_request_id or str(uuid.uuid4())
    start_time = time.time()

    try:
        logger.info(
            "Search request",
            extra={
                "request_id": request_id,
                "query": request.query[:50],
                "language": request.language,
                "page": request.page,
                "page_size": request.page_size
            }
        )

        # Generate cache key
        cache_key = get_cache_service().generate_cache_key(
            query=request.query,
            language=request.language,
            filters=request.filters,
            page=request.page,
            page_size=request.page_size
        )

        # Try cache hit
        cached_response = get_cache_service().get(cache_key)
        if cached_response:
            logger.info(
                "Cache hit",
                extra={"request_id": request_id, "cache_key": cache_key}
            )
            cached_response.cached = True
            return cached_response

        # Retrieve documents for this page
        page = request.page or 1
        page_size = request.page_size or 20
        offset = (page - 1) * page_size

        # Retrieve more documents than needed for pagination
        retrieved_chunks = get_retriever().retrieve(
            query=request.query,
            language=request.language,
            top_k=settings.rag_top_k * 2,  # Retrieve extra for pagination
            rerank_top_k=settings.rag_rerank_top_k * 2,
            filters=request.filters
        )

        # Paginate results
        total_results = len(retrieved_chunks)
        paginated_chunks = retrieved_chunks[offset:offset + page_size]

        # Convert to SearchResults
        results = [
            SearchResult(
                title=chunk["title"],
                url=chunk["url"],
                snippet=chunk["snippet"][:200] if chunk.get("snippet") else "",
                score=chunk["score"],
                source_site=chunk["source_site"],
                language=chunk["language"],
                content_type=chunk["content_type"],
                thumbnail_url=chunk.get("thumbnail_url"),
                published_date=chunk.get("published_date")
            )
            for chunk in paginated_chunks
        ]

        # Extract multimedia from retrieved chunks
        multimedia = []
        for chunk in paginated_chunks:
            if chunk.get("multimedia"):
                for media in chunk["multimedia"]:
                    multimedia.append(
                        MultimediaResult(
                            type=media.get("type", "image"),
                            url=media.get("url", ""),
                            alt_text=media.get("alt_text"),
                            source_site=chunk["source_site"],
                            thumbnail_url=media.get("thumbnail_url")
                        )
                    )

        # Extract events from retrieved chunks
        events = []
        for chunk in paginated_chunks:
            if chunk.get("events"):
                for event in chunk["events"]:
                    events.append(
                        EventResult(
                            title=event.get("title", ""),
                            date=event.get("date", ""),
                            venue=event.get("venue", ""),
                            description=event.get("description", ""),
                            source_url=event.get("source_url", chunk["url"]),
                            language=chunk["language"]
                        )
                    )

        # Create response
        response = SearchResponse(
            results=results,
            multimedia=multimedia[:10] if multimedia else [],
            events=events[:5] if events else [],
            total_results=total_results,
            page=page,
            page_size=page_size,
            cached=False
        )

        # Cache response
        get_cache_service().set(cache_key, response, ttl=settings.rag_cache_ttl_seconds)

        latency_ms = (time.time() - start_time) * 1000
        logger.info(
            "Search completed",
            extra={
                "request_id": request_id,
                "latency_ms": latency_ms,
                "result_count": len(results),
                "total_results": total_results
            }
        )

        return response

    except ValueError as e:
        logger.error(
            f"Validation error: {str(e)}",
            extra={"request_id": request_id}
        )
        raise HTTPException(
            status_code=400,
            detail=ErrorResponse(
                error=ErrorDetail(
                    code="INVALID_REQUEST",
                    message=str(e),
                    request_id=request_id
                )
            ).model_dump()
        )
    except Exception as e:
        logger.error(
            f"Search error: {str(e)}",
            extra={"request_id": request_id},
            exc_info=True
        )
        raise HTTPException(
            status_code=500,
            detail=ErrorResponse(
                error=ErrorDetail(
                    code="INTERNAL_ERROR",
                    message="Failed to process search",
                    request_id=request_id
                )
            ).model_dump()
        )
