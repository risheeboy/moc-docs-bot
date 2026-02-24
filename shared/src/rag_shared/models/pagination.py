"""Pagination models from §10 of Shared Contracts."""

from typing import Generic, TypeVar
from pydantic import BaseModel, Field, ConfigDict

T = TypeVar("T")


class PaginatedRequest(BaseModel):
    """Standard pagination parameters for requests."""

    page: int = Field(default=1, ge=1, description="1-indexed page number")
    page_size: int = Field(
        default=20,
        ge=1,
        le=100,
        description="Items per page (max 100)",
    )

    model_config = ConfigDict(from_attributes=True)


class PaginatedResponse(BaseModel, Generic[T]):
    """Standard pagination response wrapper."""

    total: int = Field(..., description="Total number of items across all pages")
    page: int = Field(..., description="Current page number (1-indexed)")
    page_size: int = Field(..., description="Items returned per page")
    total_pages: int = Field(..., description="Total number of pages")
    items: list[T] = Field(default_factory=list, description="Page items")

    model_config = ConfigDict(from_attributes=True)

    def __init__(self, **data):
        """Calculate total_pages if not provided."""
        if "total_pages" not in data and "total" in data and "page_size" in data:
            data["total_pages"] = (data["total"] + data["page_size"] - 1) // data["page_size"]
        super().__init__(**data)
