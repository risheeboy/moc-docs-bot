from pydantic import BaseModel, Field
from typing import Optional, List, Any
from datetime import datetime


class ChatMessage(BaseModel):
    """Represents a single chat message."""
    role: str = Field(..., description="Message role: 'user' or 'assistant'")
    content: str = Field(..., description="Message content")


class QueryFilters(BaseModel):
    """Filters for query requests."""
    source_sites: Optional[List[str]] = Field(default=None, description="Filter by source sites")
    content_type: Optional[str] = Field(default=None, description="Filter by content type")
    date_from: Optional[str] = Field(default=None, description="Filter by date from (ISO 8601)")
    date_to: Optional[str] = Field(default=None, description="Filter by date to (ISO 8601)")


class QueryRequest(BaseModel):
    """Request for chatbot query retrieval."""
    query: str = Field(..., description="User query")
    language: str = Field(..., description="Language code (e.g., 'hi', 'en')")
    session_id: str = Field(..., description="Session ID for conversation context")
    chat_history: Optional[List[ChatMessage]] = Field(default=[], description="Previous messages in conversation")
    top_k: Optional[int] = Field(default=10, description="Number of results to retrieve")
    rerank_top_k: Optional[int] = Field(default=5, description="Number of results after reranking")
    filters: Optional[QueryFilters] = Field(default=None, description="Search filters")


class SearchFilters(BaseModel):
    """Filters for search requests."""
    source_sites: Optional[List[str]] = Field(default=None, description="Filter by source sites")
    content_type: Optional[str] = Field(default=None, description="Filter by content type")
    date_from: Optional[str] = Field(default=None, description="Filter by date from (ISO 8601)")
    date_to: Optional[str] = Field(default=None, description="Filter by date to (ISO 8601)")
    language: Optional[str] = Field(default=None, description="Filter by language")


class SearchRequest(BaseModel):
    """Request for semantic search."""
    query: str = Field(..., description="Search query")
    language: str = Field(..., description="Language code")
    page: Optional[int] = Field(default=1, ge=1, description="Page number (1-indexed)")
    page_size: Optional[int] = Field(default=20, ge=1, le=100, description="Results per page")
    filters: Optional[SearchFilters] = Field(default=None, description="Search filters")


class IngestMetadata(BaseModel):
    """Metadata for ingested documents."""
    author: Optional[str] = Field(default=None, description="Document author")
    published_date: Optional[str] = Field(default=None, description="Publication date (ISO 8601)")
    tags: Optional[List[str]] = Field(default=None, description="Document tags")


class IngestImage(BaseModel):
    """Image extracted from document."""
    url: str = Field(..., description="Image URL")
    alt_text: Optional[str] = Field(default=None, description="Alternative text")
    s3_path: str = Field(..., description="Path in S3 storage")


class IngestRequest(BaseModel):
    """Request to ingest a document."""
    document_id: str = Field(..., description="Unique document ID")
    title: str = Field(..., description="Document title")
    source_url: str = Field(..., description="Source URL")
    source_site: str = Field(..., description="Source site domain")
    content: str = Field(..., description="Full text content")
    content_type: str = Field(..., description="Content type (e.g., 'webpage', 'pdf', 'document')")
    language: str = Field(..., description="Language code")
    metadata: Optional[IngestMetadata] = Field(default=None, description="Document metadata")
    images: Optional[List[IngestImage]] = Field(default=None, description="Extracted images")
