"""Chat endpoint for conversational queries."""

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession
from ..models import ChatRequest, ChatResponse, ErrorResponse
from ..dependencies import get_db, get_redis, get_jwt_handler, verify_jwt_token, verify_api_key
from ..services.rag_client import RAGClient
from ..services.llm_client import LLMClient
from ..services.cache_service import CacheService
from ..router_engine.semantic_router import SemanticRouter
from ..config import get_settings
from ..db.crud import SessionCRUD, ConversationCRUD
from datetime import datetime
import uuid
import logging
import json

router = APIRouter(prefix="/api/v1", tags=["chat"])
logger = logging.getLogger(__name__)


@router.post("/chat", response_model=ChatResponse, tags=["chat"])
async def chat_query(
    request_obj: ChatRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
    redis = Depends(get_redis),
    settings = Depends(get_settings),
    _: any = Depends(verify_jwt_token) or Depends(verify_api_key),
):
    """Process chat query with RAG and LLM."""
    request_id = getattr(request.state, "request_id", str(uuid.uuid4()))

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

        # Update session activity
        await SessionCRUD.update_activity(db, request_obj.session_id)

        # Initialize clients
        rag_client = RAGClient(settings.rag_service_url)
        llm_client = LLMClient(settings.llm_service_url)
        cache_service = CacheService(redis)
        semantic_router = SemanticRouter()

        # Check cache
        cache_key = cache_service.get_key("chat", request_obj.query, request_obj.language)
        cached_result = await cache_service.get(cache_key)
        if cached_result:
            logger.info(f"Cache hit for query", extra={"request_id": request_id})
            return ChatResponse(
                **cached_result,
                cached=True,
                session_id=request_obj.session_id,
                request_id=request_id,
                timestamp=datetime.utcnow(),
            )

        # Route query to appropriate model
        route = semantic_router.route(
            request_obj.query, request_obj.language, request_obj.chat_history
        )

        # Retrieve context via RAG
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

        # Check confidence threshold
        if confidence < settings.rag_confidence_threshold:
            fallback_message = (
                "मुझे इस विषय पर पर्याप्त जानकारी नहीं मिली। कृपया संस्कृति मंत्रालय हेल्पलाइन 011-23388261 पर संपर्क करें या arit-culture@gov.in पर ईमेल करें।"
                if request_obj.language == "hi"
                else "I'm unable to find a reliable answer to your question. Please contact the Ministry of Culture helpline at 011-23388261 or email arit-culture@gov.in."
            )
            return ChatResponse(
                response=fallback_message,
                sources=[],
                confidence=confidence,
                session_id=request_obj.session_id,
                language=request_obj.language,
                model_used=route.model,
                cached=False,
                request_id=request_id,
                timestamp=datetime.utcnow(),
            )

        # Generate response via LLM with language-aware system prompt
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

        llm_response = await llm_client.chat_completion(
            model=route.model,
            messages=messages,
            temperature=0.3,
            max_tokens=1024,
            request_id=request_id,
        )

        response_text = llm_response["choices"][0]["message"]["content"]

        # Store conversation
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
            response_text,
            request_obj.language,
        )

        # Prepare response
        result = ChatResponse(
            response=response_text,
            sources=sources,
            confidence=confidence,
            session_id=request_obj.session_id,
            language=request_obj.language,
            model_used=route.model,
            cached=False,
            request_id=request_id,
            timestamp=datetime.utcnow(),
        )

        # Cache result
        await cache_service.set(
            cache_key, result.model_dump(), settings.rag_cache_ttl_seconds
        )

        return result

    except Exception as e:
        logger.error(f"Chat query error: {e}", extra={"request_id": request_id})
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
