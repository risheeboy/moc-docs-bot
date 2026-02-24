"""Document metadata models."""

from typing import Optional
from datetime import datetime
from uuid import UUID
from pydantic import BaseModel, Field, ConfigDict


class Document(BaseModel):
    """Document metadata and content."""

    document_id: UUID = Field(..., description="Unique document identifier")
    title: str = Field(..., description="Document title")
    source_url: str = Field(..., description="Original source URL")
    source_site: str = Field(..., description="Source domain")
    content: str = Field(..., description="Full text content")
    content_type: str = Field(
        default="webpage",
        description="Document type: webpage | pdf | document | etc",
    )
    language: str = Field(
        default="en",
        description="Content language code",
    )
    author: Optional[str] = Field(default=None, description="Document author if known")
    published_date: Optional[datetime] = Field(
        default=None,
        description="Publication date",
    )
    created_at: datetime = Field(
        default_factory=datetime.utcnow,
        description="When document was ingested",
    )
    updated_at: datetime = Field(
        default_factory=datetime.utcnow,
        description="Last update timestamp",
    )
    tags: list[str] = Field(
        default_factory=list,
        description="Search tags (heritage, monuments, etc)",
    )
    minio_path: Optional[str] = Field(
        default=None,
        description="MinIO storage path for raw document",
    )

    model_config = ConfigDict(from_attributes=True)
