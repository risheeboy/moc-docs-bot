"""Analytics request/response models."""

from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


class QueryStats(BaseModel):
    """Statistics for a query."""
    query: str
    count: int
    avg_response_time_ms: float
    success_rate: float = Field(ge=0.0, le=1.0)
    most_common_language: str


class AnalyticsSummary(BaseModel):
    """Overall analytics summary."""
    total_queries: int
    total_feedback: int
    avg_response_time_ms: float
    avg_rating: float = Field(ge=0.0, le=5.0)
    languages: dict[str, int]
    top_queries: list[QueryStats]
    period_start: datetime
    period_end: datetime
    request_id: str
    timestamp: datetime
