"""Streaming chat endpoint (Server-Sent Events)."""

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from ..models import ChatRequest
from ..dependencies import get_db, get_redis, verify_jwt_token, verify_api_key
from ..services.rag_client import RAGClient
from ..services.llm_client import LLMClient
from ..router_engine.semantic_router import SemanticRouter
from ..config import get_settings
from ..db.crud import SessionCRUD, ConversationCRUD
import uuid
import json
import logging

router = APIRouter(prefix="/api/v1", tags=["chat"])
logger = logging.getLogger(__name__)


@router.post("/chat/stream", tags=["chat"])
async def chat_stream(
    request_obj: ChatRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
    redis = Depends(get_redis),
    settings = Depends(get_settings),
    _: any = Depends(verify_jwt_token) or Depends(verify_api_key),
):
    """Stream chat response via Server-Sent Events."""
    request_id = getattr(request.state, "request_id", str(uuid.uuid4()))

    async def event_generator():
        try:
            # Get or create session
            if not request_obj.session_id:
                request_obj.session_id = str(uuid.uuid4())

            session = await SessionCRUD.get(db, request_obj.session_id)
            if not session:
                user_id = getattr(request.state, "user", {}).get("user_id", "anonymous")
                session = await SessionCRUD.create(
                    db, request_obj.session_id, user_id, request_obj.language
                )

            # Initialize clients
            rag_client = RAGClient(settings.rag_service_url)
            llm_client = LLMClient(settings.llm_service_url)
            semantic_router = SemanticRouter()

            # Route query
            route = semantic_router.route(
                request_obj.query, request_obj.language, request_obj.chat_history
            )

            # Retrieve context
            rag_response = await rag_client.query(
                query=request_obj.query,
                language=request_obj.language,
                session_id=request_obj.session_id,
                chat_history=[h.model_dump() for h in request_obj.chat_history],
                top_k=request_obj.top_k,
                rerank_top_k=5,
                filters=request_obj.filters.model_dump(),
                request_id=request_id,
            )

            sources = rag_response.get("sources", [])
            confidence = rag_response.get("confidence", 0.0)
            context = rag_response.get("context", "")

            # Check confidence
            if confidence < settings.rag_confidence_threshold:
                fallback_message = (
                    "मुझे इस विषय पर पर्याप्त जानकारी नहीं मिली। कृपया संस्कृति मंत्रालय हेल्पलाइन 011-23388261 पर संपर्क करें या arit-culture@gov.in पर ईमेल करें।"
                    if request_obj.language == "hi"
                    else "I'm unable to find a reliable answer to your question. Please contact the Ministry of Culture helpline at 011-23388261 or email arit-culture@gov.in."
                )
                # Send fallback as single chunk
                yield f"data: {json.dumps({'content': fallback_message, 'delta': fallback_message, 'sources': [], 'confidence': confidence, 'session_id': request_obj.session_id, 'model_used': route.model, 'request_id': request_id})}\n\n"
                yield "data: [DONE]\n\n"
                return

            # Stream LLM response with language-aware system prompt
            language_prompts = {
                "hi": (
                    "आप भारत के संस्कृति मंत्रालय के लिए एक विशेषज्ञ सहायक हैं। "
                    "आपकी भूमिका भारतीय विरासत, संस्कृति, स्मारकों, परंपराओं और सरकारी सांस्कृतिक पहलों के बारे में "
                    "सटीक और तथ्यपूर्ण उत्तर प्रदान करना है। कृपया हिंदी में उत्तर दें।"
                ),
                "en": (
                    "You are an expert assistant for the Ministry of Culture, Government of India. "
                    "Your role is to provide accurate, factual answers about Indian heritage, culture, monuments, "
                    "traditions, and government cultural initiatives. Please respond in English."
                ),
            }
            lang_key = request_obj.language if request_obj.language in language_prompts else "hi"
            base_prompt = language_prompts[lang_key]
            system_prompt = f"{base_prompt}\n\nContext:\n{context}"

            messages = [{"role": "system", "content": system_prompt}]
            for msg in request_obj.chat_history:
                messages.append({"role": msg.role, "content": msg.content})
            messages.append({"role": "user", "content": request_obj.query})

            accumulated_content = ""
            async for chunk in llm_client.chat_completion_stream(
                model=route.model,
                messages=messages,
                temperature=0.3,
                max_tokens=1024,
                request_id=request_id,
            ):
                try:
                    data = json.loads(chunk)
                    delta = data.get("choices", [{}])[0].get("delta", {}).get("content", "")
                    if delta:
                        accumulated_content += delta
                        yield f"data: {json.dumps({'content': accumulated_content, 'delta': delta, 'sources': sources, 'confidence': confidence, 'session_id': request_obj.session_id, 'model_used': route.model, 'request_id': request_id})}\n\n"
                except json.JSONDecodeError:
                    pass

            # Save conversation
            await ConversationCRUD.create(
                db,
                request_obj.session_id,
                getattr(request.state, "user", {}).get("user_id", "anonymous"),
                "user",
                request_obj.query,
                request_obj.language,
            )

            await ConversationCRUD.create(
                db,
                request_obj.session_id,
                getattr(request.state, "user", {}).get("user_id", "anonymous"),
                "assistant",
                accumulated_content,
                request_obj.language,
            )

            yield "data: [DONE]\n\n"

        except Exception as e:
            logger.error(f"Stream error: {e}", extra={"request_id": request_id})
            error_msg = {"error": "Stream processing error"}
            yield f"data: {json.dumps(error_msg)}\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Request-ID": request_id,
        },
    )
