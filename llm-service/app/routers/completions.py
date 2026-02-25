"""Completions router for LLM Service

Implements OpenAI-compatible POST /v1/chat/completions endpoint.
Supports both streaming (SSE) and non-streaming responses.
"""

import logging
import uuid
from typing import Optional
from fastapi import APIRouter, HTTPException, status, Header, Body, Depends
from fastapi.responses import StreamingResponse
from app.models.completions import (
    ChatCompletionRequest,
    ChatCompletionResponse,
    ChatCompletionChoice,
    Message,
    CompletionUsage
)
from app.services.model_manager import ModelManager
from app.services.generation import GenerationService
from app.services.guardrails import GuardrailsService
from app.utils.metrics import MetricsCollector

logger = logging.getLogger(__name__)
router = APIRouter()


def get_request_id(x_request_id: Optional[str] = Header(None)) -> str:
    """Extract or generate request ID from header"""
    return x_request_id or str(uuid.uuid4())


def get_model_manager_dependency():
    """Get model manager for dependency injection."""
    from app.main import get_model_manager
    return get_model_manager()


def get_generation_service_dependency():
    """Get generation service for dependency injection."""
    from app.main import get_generation_service
    return get_generation_service()


def get_guardrails_service_dependency():
    """Get guardrails service for dependency injection."""
    from app.main import get_guardrails_service
    return get_guardrails_service()


def get_metrics_dependency():
    """Get metrics for dependency injection."""
    from app.main import get_metrics
    return get_metrics()


@router.post("/v1/chat/completions", response_model=None, tags=["completions"])
async def chat_completions(
    request: ChatCompletionRequest,
    x_request_id: str = Header(None),
    model_manager: ModelManager = Depends(get_model_manager_dependency),
    generation_service: GenerationService = Depends(get_generation_service_dependency),
    guardrails_service: GuardrailsService = Depends(get_guardrails_service_dependency),
    metrics: MetricsCollector = Depends(get_metrics_dependency)
) -> ChatCompletionResponse | StreamingResponse:
    """
    OpenAI-compatible chat completions endpoint.

    Supports:
    - Multiple models (standard, longctx, multimodal)
    - Streaming (SSE) and non-streaming responses
    - Model version selection for A/B testing
    - Langfuse tracing integration
    - Content guardrails (PII redaction, toxicity, hallucination)

    Args:
        request: ChatCompletionRequest
        x_request_id: Optional request ID for tracing
        model_manager: Model management service
        generation_service: LLM generation service
        guardrails_service: Content filtering service
        metrics: Metrics collector

    Returns:
        ChatCompletionResponse or StreamingResponse (SSE)

    Raises:
        HTTPException with standard error format
    """
    request_id = x_request_id or str(uuid.uuid4())

    try:
        # Inject dependencies if not provided
        if model_manager is None:
            from app.main import get_model_manager, get_generation_service, get_guardrails_service, get_metrics
            model_manager = get_model_manager()
            generation_service = get_generation_service()
            guardrails_service = get_guardrails_service()
            metrics = get_metrics()

        # Map OpenAI model names to internal model keys
        model_key = _map_model_name(request.model, model_manager)

        # Validate model is loaded
        if not model_manager.is_model_loaded(model_key):
            logger.warning(
                "Model not loaded",
                extra={"model": request.model, "request_id": request_id}
            )
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail={
                    "error": {
                        "code": "MODEL_LOADING",
                        "message": f"Model {request.model} is not loaded. Please try again in a moment.",
                        "request_id": request_id
                    }
                }
            )

        # Validate request
        if not request.messages:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={
                    "error": {
                        "code": "INVALID_REQUEST",
                        "message": "At least one message is required",
                        "request_id": request_id
                    }
                }
            )

        # Apply guardrails to input
        try:
            validated_messages = await guardrails_service.validate_input(
                request.messages,
                request_id=request_id
            )
        except Exception as e:
            logger.error(
                "Guardrails validation failed",
                exc_info=True,
                extra={"request_id": request_id}
            )
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail={
                    "error": {
                        "code": "PROCESSING_FAILED",
                        "message": "Input validation failed",
                        "request_id": request_id
                    }
                }
            )

        # Streaming response
        if request.stream:
            return StreamingResponse(
                _stream_completions(
                    request=request,
                    model_key=model_key,
                    validated_messages=validated_messages,
                    generation_service=generation_service,
                    guardrails_service=guardrails_service,
                    metrics=metrics,
                    request_id=request_id,
                    model_manager=model_manager
                ),
                media_type="text/event-stream",
                headers={
                    "Cache-Control": "no-cache",
                    "Connection": "keep-alive",
                    "X-Request-ID": request_id
                }
            )

        # Non-streaming response
        else:
            return await _complete(
                request=request,
                model_key=model_key,
                validated_messages=validated_messages,
                generation_service=generation_service,
                guardrails_service=guardrails_service,
                metrics=metrics,
                request_id=request_id,
                model_manager=model_manager
            )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            "Chat completion failed",
            exc_info=True,
            extra={"request_id": request_id}
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": {
                    "code": "INTERNAL_ERROR",
                    "message": "Chat completion failed",
                    "request_id": request_id
                }
            }
        )


async def _complete(
    request: ChatCompletionRequest,
    model_key: str,
    validated_messages: list,
    generation_service: GenerationService,
    guardrails_service: GuardrailsService,
    metrics: MetricsCollector,
    request_id: str,
    model_manager: ModelManager
) -> ChatCompletionResponse:
    """Generate non-streaming completion"""
    completion_id = f"chatcmpl-{uuid.uuid4()}"

    try:
        # Generate response
        response_text, prompt_tokens, completion_tokens = await generation_service.generate(
            model_key=model_key,
            messages=validated_messages,
            temperature=request.temperature,
            max_tokens=request.max_tokens,
            top_p=request.top_p,
            top_k=request.top_k,
            request_id=request_id,
            model_version=request.model_version
        )

        # Apply guardrails to output
        filtered_response = await guardrails_service.filter_output(
            text=response_text,
            request_id=request_id
        )

        # Record metrics
        metrics.record_inference(
            model=request.model,
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens
        )

        return ChatCompletionResponse(
            id=completion_id,
            model=request.model,
            choices=[
                ChatCompletionChoice(
                    index=0,
                    message=Message(
                        role="assistant",
                        content=filtered_response
                    ),
                    finish_reason="stop"
                )
            ],
            usage=CompletionUsage(
                prompt_tokens=prompt_tokens,
                completion_tokens=completion_tokens,
                total_tokens=prompt_tokens + completion_tokens
            )
        )

    except Exception as e:
        logger.error(
            "Completion generation failed",
            exc_info=True,
            extra={"request_id": request_id, "model": request.model}
        )
        raise


async def _stream_completions(
    request: ChatCompletionRequest,
    model_key: str,
    validated_messages: list,
    generation_service: GenerationService,
    guardrails_service: GuardrailsService,
    metrics: MetricsCollector,
    request_id: str,
    model_manager: ModelManager
):
    """Generate streaming completion (SSE)"""
    completion_id = f"chatcmpl-{uuid.uuid4()}"
    total_prompt_tokens = 0
    total_completion_tokens = 0

    try:
        async for token, prompt_tokens, completion_tokens in generation_service.stream_generate(
            model_key=model_key,
            messages=validated_messages,
            temperature=request.temperature,
            max_tokens=request.max_tokens,
            top_p=request.top_p,
            top_k=request.top_k,
            request_id=request_id,
            model_version=request.model_version
        ):
            total_prompt_tokens = prompt_tokens
            total_completion_tokens = completion_tokens

            # Stream chunk
            chunk = {
                "id": completion_id,
                "object": "text_completion",
                "created": int(__import__("time").time()),
                "model": request.model,
                "choices": [
                    {
                        "index": 0,
                        "delta": {"content": token},
                        "finish_reason": None
                    }
                ]
            }
            yield f"data: {__import__('json').dumps(chunk)}\n\n"

        # Record metrics
        metrics.record_inference(
            model=request.model,
            prompt_tokens=total_prompt_tokens,
            completion_tokens=total_completion_tokens
        )

        # Send done message
        yield "data: [DONE]\n\n"

    except Exception as e:
        logger.error(
            "Stream completion failed",
            exc_info=True,
            extra={"request_id": request_id, "model": request.model}
        )
        error_message = {
            "error": {
                "code": "INTERNAL_ERROR",
                "message": "Stream generation failed",
                "request_id": request_id
            }
        }
        yield f"data: {__import__('json').dumps(error_message)}\n\n"


def _map_model_name(model_id: str, model_manager: ModelManager) -> str:
    """Map OpenAI model name to internal model key"""
    if model_manager.config.llm_model_standard in model_id:
        return "standard"
    elif model_manager.config.llm_model_longctx in model_id:
        return "longctx"
    elif model_manager.config.llm_model_multimodal in model_id:
        return "multimodal"
    else:
        # Default to standard
        return "standard"
