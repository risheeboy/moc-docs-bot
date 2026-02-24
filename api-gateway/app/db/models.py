"""SQLAlchemy ORM models."""

from sqlalchemy import Column, String, Integer, Float, DateTime, Boolean, Text, JSON
from sqlalchemy.orm import declarative_base
from datetime import datetime
import uuid

Base = declarative_base()


class Session(Base):
    """Conversation session."""

    __tablename__ = "sessions"

    session_id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String(36))
    language = Column(String(10), default="en")
    turn_count = Column(Integer, default=0)
    context_tokens = Column(Integer, default=0)
    last_activity = Column(DateTime, default=datetime.utcnow)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class Conversation(Base):
    """Conversation message."""

    __tablename__ = "conversations"

    conversation_id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    session_id = Column(String(36))
    user_id = Column(String(36))
    role = Column(String(20))  # "user" or "assistant"
    content = Column(Text)
    language = Column(String(10))
    timestamp = Column(DateTime, default=datetime.utcnow)
    created_at = Column(DateTime, default=datetime.utcnow)


class Feedback(Base):
    """User feedback."""

    __tablename__ = "feedback"

    feedback_id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    session_id = Column(String(36))
    user_id = Column(String(36))
    query = Column(Text)
    response = Column(Text)
    rating = Column(Integer)  # 1-5
    feedback_type = Column(String(20))  # "chat" or "search"
    feedback_text = Column(Text)
    sentiment_score = Column(Float)  # 0-1
    sentiment_label = Column(String(20))  # "positive", "neutral", "negative"
    language = Column(String(10))
    created_at = Column(DateTime, default=datetime.utcnow)


class Document(Base):
    """Ingested document metadata."""

    __tablename__ = "documents"

    document_id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    title = Column(String(500))
    source_url = Column(String(2000))
    source_site = Column(String(500))
    language = Column(String(10))
    content_type = Column(String(50))  # "webpage", "pdf", "docx", etc.
    chunk_count = Column(Integer, default=0)
    embedding_status = Column(String(50))  # "pending", "completed", "failed"
    milvus_ids = Column(JSON)  # list of IDs in vector DB
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class AuditLog(Base):
    """Audit trail for all API requests."""

    __tablename__ = "audit_log"

    log_id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    request_id = Column(String(36))
    user_id = Column(String(36))
    role = Column(String(50))
    method = Column(String(10))  # GET, POST, etc.
    path = Column(String(500))
    status_code = Column(Integer)
    duration_ms = Column(Float)
    created_at = Column(DateTime, default=datetime.utcnow)


class APIKey(Base):
    """API key for widget/consumer authentication."""

    __tablename__ = "api_keys"

    key_id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String(36))
    key_hash = Column(String(64))  # SHA256 hash
    name = Column(String(500))
    role = Column(String(50), default="api_consumer")
    active = Column(Boolean, default=True)
    expires_at = Column(DateTime)
    last_used_at = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow)


class Analytics(Base):
    """Query analytics."""

    __tablename__ = "analytics"

    metric_id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    query = Column(String(2000))
    query_hash = Column(String(64))
    count = Column(Integer, default=1)
    avg_response_time_ms = Column(Float)
    success_rate = Column(Float)
    language = Column(String(10))
    model_used = Column(String(100))
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class SystemConfig(Base):
    """System configuration."""

    __tablename__ = "system_config"

    config_id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    key = Column(String(100), unique=True)
    value = Column(String(1000))
    description = Column(String(500))
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
