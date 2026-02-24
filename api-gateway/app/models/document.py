"""Document management request/response models."""

from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime
from uuid import UUID


class DocumentUpload(BaseModel):
    """Document upload metadata."""
    title: str = Field(..., min_length=1, max_length=500)
    description: Optional[str] = None
    source_url: Optional[str] = None
    language: str = Field(default="en")
    content_type: str = Field(default="webpage")


class DocumentResponse(BaseModel):
    """Document response."""
    document_id: str
    title: str
    source_url: Optional[str] = None
    language: str
    content_type: str
    chunk_count: int
    embedding_status: str
    created_at: datetime
    updated_at: datetime
    request_id: str


class DocumentListResponse(BaseModel):
    """List of documents response."""
    documents: list[DocumentResponse]
    total: int
    page: int
    page_size: int
    request_id: str
