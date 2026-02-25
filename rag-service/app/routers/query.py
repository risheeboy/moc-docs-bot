from fastapi import APIRouter, HTTPException, Header
from typing import Optional
import uuid
import logging
import time
from app.models.request import QueryRequest
from app.models.response import QueryResponse, Source, ErrorResponse, ErrorDetail
from app.config import settings

router = APIRouter()
logger = logging.getLogger(__name__)

# Lazy-loaded services
_retriever = None
_context_builder = None
_cache_service = None

def get_retriever():
    global _retriever
    if _retriever is None:
        from app.services.retriever import RetrieverService
        _retriever = RetrieverService()
    return _retriever

def get_context_builder():
    global _context_builder
    if _context_builder is None:
        from app.services.context_builder import ContextBuilder
        _context_builder = ContextBuilder()
    return _context_builder

def get_cache_service():
    global _cache_service
    if _cache_service is None:
        from app.services.cache_service import CacheService
        _cache_service = CacheService()
    return _cache_service


@router.post("/query", response_model=QueryResponse)
async def query_endpoint(
    request: QueryRequest,
    x_request_id: Optional[str] = Header(None)
) -> QueryResponse:
    """
    Retrieve context from documents for chatbot generation.

    Implements hybrid retrieval (BGE-M3 dense + sparse) with reranking,
    context assembly, and Redis caching.
    """
    request_id = x_request_id or str(uuid.uuid4())
    start_time = time.time()

    try:
        logger.info(
            "Query request",
            extra={
                "request_id": request_id,
                "query": request.query[:50],  # Truncate for logging
                "language": request.language,
                "session_id": request.session_id
            }
        )

        # Generate cache key
        cache_key = get_cache_service().generate_cache_key(
            query=request.query,
            language=request.language,
            filters=request.filters
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

        # Retrieve documents
        retrieved_chunks = get_retriever().retrieve(
            query=request.query,
            language=request.language,
            top_k=request.top_k or settings.rag_top_k,
            rerank_top_k=request.rerank_top_k or settings.rag_rerank_top_k,
            filters=request.filters
        )

        if not retrieved_chunks:
            logger.warning(
                "No documents retrieved",
                extra={"request_id": request_id}
            )

        # Build context from retrieved chunks
        context, sources = get_context_builder().build_context(retrieved_chunks)

        # Calculate confidence
        if sources:
            confidence = sum(s["score"] for s in sources) / len(sources)
        else:
            confidence = 0.0

        # Create response
        response = QueryResponse(
            context=context,
            sources=[
                Source(
                    title=s["title"],
                    url=s["url"],
                    snippet=s["snippet"],
                    score=s["score"],
                    source_site=s["source_site"],
                    language=s["language"],
                    content_type=s["content_type"],
                    chunk_id=s["chunk_id"]
                )
                for s in sources
            ],
            confidence=confidence,
            cached=False
        )

        # Cache response
        get_cache_service().set(cache_key, response, ttl=settings.rag_cache_ttl_seconds)

        latency_ms = (time.time() - start_time) * 1000
        logger.info(
            "Query completed",
            extra={
                "request_id": request_id,
                "latency_ms": latency_ms,
                "result_count": len(sources),
                "confidence": confidence
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
            f"Query error: {str(e)}",
            extra={"request_id": request_id},
            exc_info=True
        )
        raise HTTPException(
            status_code=500,
            detail=ErrorResponse(
                error=ErrorDetail(
                    code="INTERNAL_ERROR",
                    message="Failed to process query",
                    request_id=request_id
                )
            ).model_dump()
        )
