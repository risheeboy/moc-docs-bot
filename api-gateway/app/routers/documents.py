"""Document management endpoints."""

from fastapi import APIRouter, Depends, HTTPException, Request, File, UploadFile, Form
from sqlalchemy.ext.asyncio import AsyncSession
from ..models import DocumentUpload, DocumentResponse, DocumentListResponse
from ..dependencies import get_db, verify_jwt_token, verify_api_key
from ..services.rag_client import RAGClient
from ..config import get_settings
from ..db.crud import DocumentCRUD
from datetime import datetime
import uuid
import logging

router = APIRouter(prefix="/api/v1/documents", tags=["documents"])
logger = logging.getLogger(__name__)


@router.post("/upload", response_model=DocumentResponse, tags=["documents"])
async def upload_document(
    file: UploadFile = File(...),
    title: str = Form(...),
    description: str = Form(default=""),
    source_url: str = Form(default=""),
    language: str = Form(default="en"),
    request: Request = None,
    db: AsyncSession = Depends(get_db),
    settings = Depends(get_settings),
    _: any = Depends(verify_jwt_token) or Depends(verify_api_key),
):
    """Upload document for ingestion and embedding."""
    request_id = getattr(request.state, "request_id", str(uuid.uuid4()))
    document_id = str(uuid.uuid4())

    try:
        # Read file
        content = await file.read()

        # Create document record
        doc = await DocumentCRUD.create(
            db,
            document_id=document_id,
            title=title,
            source_url=source_url,
            source_site="uploaded",
            language=language,
            content_type="pdf" if file.filename.endswith(".pdf") else "text",
        )

        # Call RAG service to ingest
        rag_client = RAGClient(settings.rag_service_url)
        rag_response = await rag_client.ingest(
            document_id=document_id,
            title=title,
            source_url=source_url,
            source_site="uploaded",
            content=content.decode("utf-8", errors="ignore"),
            content_type="pdf" if file.filename.endswith(".pdf") else "text",
            language=language,
            metadata={"description": description},
            images=[],
            request_id=request_id,
        )

        # Update document with embedding status
        doc.chunk_count = rag_response.get("chunk_count", 0)
        doc.embedding_status = rag_response.get("embedding_status", "pending")
        doc.milvus_ids = rag_response.get("milvus_ids", [])
        await db.commit()

        return DocumentResponse(
            document_id=doc.document_id,
            title=doc.title,
            source_url=doc.source_url,
            language=doc.language,
            content_type=doc.content_type,
            chunk_count=doc.chunk_count,
            embedding_status=doc.embedding_status,
            created_at=doc.created_at,
            updated_at=doc.updated_at,
            request_id=request_id,
        )

    except Exception as e:
        logger.error(f"Document upload error: {e}", extra={"request_id": request_id})
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


@router.get("", response_model=DocumentListResponse, tags=["documents"])
async def list_documents(
    page: int = 1,
    page_size: int = 20,
    request: Request = None,
    db: AsyncSession = Depends(get_db),
    _: any = Depends(verify_jwt_token) or Depends(verify_api_key),
):
    """List ingested documents."""
    request_id = getattr(request.state, "request_id", str(uuid.uuid4()))

    try:
        docs = await DocumentCRUD.list_all(db, page, page_size)

        return DocumentListResponse(
            documents=[
                DocumentResponse(
                    document_id=doc.document_id,
                    title=doc.title,
                    source_url=doc.source_url,
                    language=doc.language,
                    content_type=doc.content_type,
                    chunk_count=doc.chunk_count,
                    embedding_status=doc.embedding_status,
                    created_at=doc.created_at,
                    updated_at=doc.updated_at,
                    request_id=request_id,
                )
                for doc in docs
            ],
            total=len(docs),
            page=page,
            page_size=page_size,
            request_id=request_id,
        )

    except Exception as e:
        logger.error(f"List documents error: {e}", extra={"request_id": request_id})
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


@router.delete("/{document_id}", tags=["documents"])
async def delete_document(
    document_id: str,
    request: Request = None,
    db: AsyncSession = Depends(get_db),
    _: any = Depends(verify_jwt_token) or Depends(verify_api_key),
):
    """Delete document and cleanup Milvus embeddings."""
    request_id = getattr(request.state, "request_id", str(uuid.uuid4()))

    try:
        await DocumentCRUD.delete(db, document_id)

        return {"message": "Document deleted", "request_id": request_id}

    except Exception as e:
        logger.error(f"Delete document error: {e}", extra={"request_id": request_id})
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
