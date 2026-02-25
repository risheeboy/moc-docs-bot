from fastapi import APIRouter, HTTPException, Header
from typing import Optional
import uuid
import logging
import time
from app.models.request import IngestRequest
from app.models.response import IngestResponse, ErrorResponse, ErrorDetail

router = APIRouter()
logger = logging.getLogger(__name__)

# Lazy-loaded services
_indexer = None
_cache_service = None

def get_indexer():
    global _indexer
    if _indexer is None:
        from app.services.indexer import IndexerService
        _indexer = IndexerService()
    return _indexer

def get_cache_service():
    global _cache_service
    if _cache_service is None:
        from app.services.cache_service import CacheService
        _cache_service = CacheService()
    return _cache_service


@router.post("/ingest", response_model=IngestResponse)
async def ingest_endpoint(
    request: IngestRequest,
    x_request_id: Optional[str] = Header(None)
) -> IngestResponse:
    """
    Ingest a document: chunk, embed, and index into Milvus.

    Called by the Data Ingestion service after document scraping/parsing.
    Chunks text according to RAG_CHUNK_SIZE/RAG_CHUNK_OVERLAP,
    generates embeddings with BGE-M3,
    stores in Milvus, and invalidates query cache.
    """
    request_id = x_request_id or str(uuid.uuid4())
    start_time = time.time()

    try:
        logger.info(
            "Ingest request",
            extra={
                "request_id": request_id,
                "document_id": request.document_id,
                "title": request.title,
                "language": request.language
            }
        )

        # Ingest document
        chunk_ids = get_indexer().ingest_document(
            document_id=request.document_id,
            title=request.title,
            source_url=request.source_url,
            source_site=request.source_site,
            content=request.content,
            content_type=request.content_type,
            language=request.language,
            metadata=request.metadata.model_dump() if request.metadata else {},
            images=request.images
        )

        # Invalidate cache after ingestion
        get_cache_service().invalidate_all()

        latency_ms = (time.time() - start_time) * 1000
        logger.info(
            "Ingest completed",
            extra={
                "request_id": request_id,
                "chunk_count": len(chunk_ids),
                "latency_ms": latency_ms
            }
        )

        return IngestResponse(
            document_id=request.document_id,
            chunk_count=len(chunk_ids),
            embedding_status="completed",
            milvus_ids=chunk_ids
        )

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
            f"Ingest error: {str(e)}",
            extra={"request_id": request_id},
            exc_info=True
        )
        raise HTTPException(
            status_code=500,
            detail=ErrorResponse(
                error=ErrorDetail(
                    code="INTERNAL_ERROR",
                    message="Failed to ingest document",
                    request_id=request_id
                )
            ).model_dump()
        )
