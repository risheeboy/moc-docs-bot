"""Generation service for LLM inference

Wraps vLLM engines with prompt templating, streaming, and request handling.
"""

import logging
import time
from typing import AsyncIterator, List, Tuple, Optional
from vllm.utils import random_uuid
from app.models.completions import Message
from app.services.model_manager import ModelManager
from app.services.prompt_templates import PromptTemplateService
from app.utils.langfuse_tracer import LangfuseTracer

logger = logging.getLogger(__name__)


class GenerationService:
    """Handles LLM text generation with streaming and tracing"""

    def __init__(
        self,
        model_manager: ModelManager,
        prompt_templates: PromptTemplateService,
        tracer: Optional[LangfuseTracer] = None
    ):
        """Initialize generation service

        Args:
            model_manager: Model manager instance
            prompt_templates: Prompt template service
            tracer: Optional Langfuse tracer
        """
        self.model_manager = model_manager
        self.prompt_templates = prompt_templates
        self.tracer = tracer

    async def generate(
        self,
        model_key: str,
        messages: List[Message],
        temperature: float = 0.3,
        max_tokens: int = 1024,
        top_p: float = 0.95,
        top_k: int = 40,
        request_id: str = "",
        model_version: Optional[str] = None
    ) -> Tuple[str, int, int]:
        """Generate text completion (non-streaming)

        Args:
            model_key: "standard", "longctx", or "multimodal"
            messages: Chat message history
            temperature: Sampling temperature (0-2)
            max_tokens: Maximum tokens to generate
            top_p: Top-p sampling parameter
            top_k: Top-k sampling parameter
            request_id: Request ID for tracing
            model_version: Optional model version for A/B testing

        Returns:
            Tuple of (generated_text, prompt_tokens, completion_tokens)
        """
        start_time = time.time()

        try:
            # Get engine
            engine = self.model_manager.get_engine(model_key)
            if not engine:
                raise ValueError(f"Model {model_key} not loaded")

            # Format prompt
            prompt = self.prompt_templates.format_messages(messages)

            # Generate
            outputs = await engine.generate(
                prompt=prompt,
                sampling_params={
                    "temperature": temperature,
                    "max_tokens": max_tokens,
                    "top_p": top_p,
                    "top_k": top_k,
                },
                request_id=request_id
            )

            if not outputs:
                raise ValueError("No output from model")

            output = outputs[0]
            generated_text = output.outputs[0].text

            # Count tokens (vLLM provides prompt_tokens and completion_tokens)
            prompt_tokens = len(output.prompt_token_ids) if output.prompt_token_ids else 0
            completion_tokens = sum(
                len(o.token_ids) for o in output.outputs
            ) if output.outputs else 0

            elapsed = time.time() - start_time

            # Trace to Langfuse if enabled
            if self.tracer:
                await self.tracer.trace_completion(
                    request_id=request_id,
                    model=self.model_manager._get_model_id(model_key),
                    messages=messages,
                    output=generated_text,
                    prompt_tokens=prompt_tokens,
                    completion_tokens=completion_tokens,
                    duration_ms=int(elapsed * 1000)
                )

            logger.info(
                "Generation completed",
                extra={
                    "request_id": request_id,
                    "model_key": model_key,
                    "prompt_tokens": prompt_tokens,
                    "completion_tokens": completion_tokens,
                    "duration_ms": int(elapsed * 1000)
                }
            )

            return generated_text, prompt_tokens, completion_tokens

        except Exception as e:
            logger.error(
                "Generation failed",
                exc_info=True,
                extra={"request_id": request_id, "model_key": model_key}
            )
            raise

    async def stream_generate(
        self,
        model_key: str,
        messages: List[Message],
        temperature: float = 0.3,
        max_tokens: int = 1024,
        top_p: float = 0.95,
        top_k: int = 40,
        request_id: str = "",
        model_version: Optional[str] = None
    ) -> AsyncIterator[Tuple[str, int, int]]:
        """Generate text completion with streaming (SSE)

        Yields tokens as they are generated.

        Args:
            model_key: "standard", "longctx", or "multimodal"
            messages: Chat message history
            temperature: Sampling temperature (0-2)
            max_tokens: Maximum tokens to generate
            top_p: Top-p sampling parameter
            top_k: Top-k sampling parameter
            request_id: Request ID for tracing
            model_version: Optional model version for A/B testing

        Yields:
            Tuples of (token, prompt_tokens, completion_tokens)
        """
        start_time = time.time()
        prompt_tokens = 0
        completion_tokens = 0
        full_output = ""

        try:
            # Get engine
            engine = self.model_manager.get_engine(model_key)
            if not engine:
                raise ValueError(f"Model {model_key} not loaded")

            # Format prompt
            prompt = self.prompt_templates.format_messages(messages)

            # Stream generation
            async for output in engine.generate(
                prompt=prompt,
                sampling_params={
                    "temperature": temperature,
                    "max_tokens": max_tokens,
                    "top_p": top_p,
                    "top_k": top_k,
                },
                request_id=request_id
            ):
                if output.outputs:
                    token = output.outputs[0].text
                    full_output += token

                    # Update token counts
                    if output.prompt_token_ids:
                        prompt_tokens = len(output.prompt_token_ids)
                    if output.outputs[0].token_ids:
                        completion_tokens = len(output.outputs[0].token_ids)

                    yield token, prompt_tokens, completion_tokens

            elapsed = time.time() - start_time

            # Trace to Langfuse if enabled
            if self.tracer:
                await self.tracer.trace_completion(
                    request_id=request_id,
                    model=self.model_manager._get_model_id(model_key),
                    messages=messages,
                    output=full_output,
                    prompt_tokens=prompt_tokens,
                    completion_tokens=completion_tokens,
                    duration_ms=int(elapsed * 1000)
                )

            logger.info(
                "Stream generation completed",
                extra={
                    "request_id": request_id,
                    "model_key": model_key,
                    "prompt_tokens": prompt_tokens,
                    "completion_tokens": completion_tokens,
                    "duration_ms": int(elapsed * 1000)
                }
            )

        except Exception as e:
            logger.error(
                "Stream generation failed",
                exc_info=True,
                extra={"request_id": request_id, "model_key": model_key}
            )
            raise
