"""Feedback submission endpoints."""

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession
from ..models import FeedbackCreate, FeedbackResponse
from ..dependencies import get_db, verify_jwt_token, verify_api_key
from ..services.llm_client import LLMClient
from ..config import get_settings
from ..db.crud import FeedbackCRUD
from datetime import datetime
import uuid
import logging

router = APIRouter(prefix="/api/v1", tags=["feedback"])
logger = logging.getLogger(__name__)


@router.post("/feedback", response_model=FeedbackResponse, tags=["feedback"])
async def submit_feedback(
    request_obj: FeedbackCreate,
    request: Request = None,
    db: AsyncSession = Depends(get_db),
    settings = Depends(get_settings),
    _: any = Depends(verify_jwt_token) or Depends(verify_api_key),
):
    """Submit user feedback with sentiment analysis."""
    request_id = getattr(request.state, "request_id", str(uuid.uuid4()))
    feedback_id = str(uuid.uuid4())

    try:
        # Create feedback record
        feedback = await FeedbackCRUD.create(
            db,
            session_id=request_obj.session_id,
            user_id=getattr(request.state, "user", {}).get("user_id", "anonymous"),
            query=request_obj.query,
            response=request_obj.response,
            rating=request_obj.rating,
            feedback_type=request_obj.feedback_type,
            feedback_text=request_obj.feedback_text or "",
            language=request_obj.language,
        )

        # Run sentiment analysis asynchronously
        sentiment_score = None
        sentiment_label = None

        try:
            llm_client = LLMClient(settings.llm_service_url)
            sentiment_prompt = f"""Analyze the sentiment of the following feedback text. Return only a JSON object with "score" (0-1) and "label" ("positive", "neutral", or "negative").

Feedback: "{request_obj.feedback_text or ''}"

Response:"""

            response = await llm_client.chat_completion(
                model=settings.llm_model_standard,
                messages=[{"role": "user", "content": sentiment_prompt}],
                temperature=0.0,
                max_tokens=50,
                request_id=request_id,
            )

            # Parse sentiment response
            import json

            try:
                sentiment_text = response["choices"][0]["message"]["content"]
                sentiment_data = json.loads(sentiment_text)
                sentiment_score = float(sentiment_data.get("score", 0.5))
                sentiment_label = sentiment_data.get("label", "neutral")
            except (json.JSONDecodeError, ValueError, KeyError):
                sentiment_score = 0.5
                sentiment_label = "neutral"

            # Update feedback with sentiment
            await FeedbackCRUD.update_sentiment(db, feedback_id, sentiment_score, sentiment_label)
        except Exception as e:
            logger.warning(f"Sentiment analysis failed: {e}", extra={"request_id": request_id})

        return FeedbackResponse(
            feedback_id=feedback.feedback_id,
            session_id=feedback.session_id,
            rating=feedback.rating,
            feedback_type=feedback.feedback_type,
            sentiment_score=sentiment_score,
            sentiment_label=sentiment_label,
            created_at=feedback.created_at,
            request_id=request_id,
        )

    except Exception as e:
        logger.error(f"Feedback submission error: {e}", extra={"request_id": request_id})
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
