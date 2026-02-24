"""CRUD operations for database models."""

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc
from datetime import datetime
from .models import (
    Session,
    Conversation,
    Feedback,
    Document,
    AuditLog,
    APIKey,
    Analytics,
    SystemConfig,
)
import logging

logger = logging.getLogger(__name__)


class SessionCRUD:
    """CRUD for sessions."""

    @staticmethod
    async def create(db: AsyncSession, session_id: str, user_id: str, language: str = "en"):
        """Create new session."""
        session = Session(session_id=session_id, user_id=user_id, language=language)
        db.add(session)
        await db.commit()
        return session

    @staticmethod
    async def get(db: AsyncSession, session_id: str):
        """Get session by ID."""
        result = await db.execute(select(Session).filter(Session.session_id == session_id))
        return result.scalar_one_or_none()

    @staticmethod
    async def update_activity(db: AsyncSession, session_id: str):
        """Update last activity timestamp."""
        session = await SessionCRUD.get(db, session_id)
        if session:
            session.last_activity = datetime.utcnow()
            await db.commit()


class ConversationCRUD:
    """CRUD for conversations."""

    @staticmethod
    async def create(
        db: AsyncSession,
        session_id: str,
        user_id: str,
        role: str,
        content: str,
        language: str,
    ):
        """Create conversation message."""
        conv = Conversation(
            session_id=session_id, user_id=user_id, role=role, content=content, language=language
        )
        db.add(conv)
        await db.commit()
        return conv

    @staticmethod
    async def get_by_session(db: AsyncSession, session_id: str, limit: int = 20):
        """Get conversation history for session."""
        result = await db.execute(
            select(Conversation)
            .filter(Conversation.session_id == session_id)
            .order_by(Conversation.timestamp)
            .limit(limit)
        )
        return result.scalars().all()


class FeedbackCRUD:
    """CRUD for feedback."""

    @staticmethod
    async def create(
        db: AsyncSession,
        session_id: str,
        user_id: str,
        query: str,
        response: str,
        rating: int,
        feedback_type: str,
        feedback_text: str,
        language: str,
    ):
        """Create feedback record."""
        feedback = Feedback(
            session_id=session_id,
            user_id=user_id,
            query=query,
            response=response,
            rating=rating,
            feedback_type=feedback_type,
            feedback_text=feedback_text,
            language=language,
        )
        db.add(feedback)
        await db.commit()
        return feedback

    @staticmethod
    async def update_sentiment(
        db: AsyncSession, feedback_id: str, sentiment_score: float, sentiment_label: str
    ):
        """Update feedback with sentiment."""
        result = await db.execute(
            select(Feedback).filter(Feedback.feedback_id == feedback_id)
        )
        feedback = result.scalar_one_or_none()
        if feedback:
            feedback.sentiment_score = sentiment_score
            feedback.sentiment_label = sentiment_label
            await db.commit()


class DocumentCRUD:
    """CRUD for documents."""

    @staticmethod
    async def create(
        db: AsyncSession,
        document_id: str,
        title: str,
        source_url: str,
        source_site: str,
        language: str,
        content_type: str,
    ):
        """Create document record."""
        doc = Document(
            document_id=document_id,
            title=title,
            source_url=source_url,
            source_site=source_site,
            language=language,
            content_type=content_type,
        )
        db.add(doc)
        await db.commit()
        return doc

    @staticmethod
    async def get(db: AsyncSession, document_id: str):
        """Get document by ID."""
        result = await db.execute(select(Document).filter(Document.document_id == document_id))
        return result.scalar_one_or_none()

    @staticmethod
    async def list_all(db: AsyncSession, page: int = 1, page_size: int = 20):
        """List all documents with pagination."""
        result = await db.execute(
            select(Document)
            .order_by(desc(Document.created_at))
            .offset((page - 1) * page_size)
            .limit(page_size)
        )
        return result.scalars().all()

    @staticmethod
    async def delete(db: AsyncSession, document_id: str):
        """Delete document."""
        doc = await DocumentCRUD.get(db, document_id)
        if doc:
            await db.delete(doc)
            await db.commit()


class AuditLogCRUD:
    """CRUD for audit logs."""

    @staticmethod
    async def create(
        db: AsyncSession,
        request_id: str,
        user_id: str,
        role: str,
        method: str,
        path: str,
        status_code: int,
        duration_ms: float,
    ):
        """Create audit log entry."""
        log = AuditLog(
            request_id=request_id,
            user_id=user_id,
            role=role,
            method=method,
            path=path,
            status_code=status_code,
            duration_ms=duration_ms,
        )
        db.add(log)
        await db.commit()
        return log


class APIKeyCRUD:
    """CRUD for API keys."""

    @staticmethod
    async def create(db: AsyncSession, key_id: str, user_id: str, key_hash: str, name: str):
        """Create API key."""
        api_key = APIKey(key_id=key_id, user_id=user_id, key_hash=key_hash, name=name)
        db.add(api_key)
        await db.commit()
        return api_key

    @staticmethod
    async def get_by_hash(db: AsyncSession, key_hash: str):
        """Get API key by hash."""
        result = await db.execute(select(APIKey).filter(APIKey.key_hash == key_hash))
        return result.scalar_one_or_none()

    @staticmethod
    async def update_last_used(db: AsyncSession, key_id: str):
        """Update last used timestamp."""
        result = await db.execute(select(APIKey).filter(APIKey.key_id == key_id))
        key = result.scalar_one_or_none()
        if key:
            key.last_used_at = datetime.utcnow()
            await db.commit()
