"""Authentication models."""

from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


class TokenPayload(BaseModel):
    """JWT token payload."""
    user_id: str
    email: str
    role: str
    exp: int
    iat: int


class TokenResponse(BaseModel):
    """Token response."""
    access_token: str
    refresh_token: Optional[str] = None
    token_type: str = "bearer"
    expires_in: int


class APIKey(BaseModel):
    """API key for widget/consumer access."""
    key_id: str
    key_hash: str
    name: str
    role: str
    created_at: datetime
    expires_at: Optional[datetime] = None
    last_used_at: Optional[datetime] = None
    active: bool = True
