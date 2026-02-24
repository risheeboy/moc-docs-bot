"""Langfuse tracer integration for LLM call tracing and observability

Provides tracing of LLM completions and performance metrics to Langfuse.
"""

import logging
from typing import List, Optional
from app.config import LLMConfig
from app.models.completions import Message

logger = logging.getLogger(__name__)


class LangfuseTracer:
    """Traces LLM calls to Langfuse for observability"""

    def __init__(self, config: LLMConfig):
        """Initialize Langfuse tracer

        Args:
            config: LLM configuration
        """
        self.config = config
        self.enabled = config.langfuse_enabled

        # Import Langfuse only if enabled
        if self.enabled:
            try:
                from langfuse import Langfuse
                self.client = Langfuse(
                    public_key=config.langfuse_public_key,
                    secret_key=config.langfuse_secret_key,
                    host=config.langfuse_host
                )
            except ImportError:
                logger.warning("Langfuse not installed, tracing disabled")
                self.enabled = False
            except Exception as e:
                logger.error("Failed to initialize Langfuse", exc_info=True)
                self.enabled = False

    async def trace_completion(
        self,
        request_id: str,
        model: str,
        messages: List[Message],
        output: str,
        prompt_tokens: int,
        completion_tokens: int,
        duration_ms: int
    ):
        """Trace an LLM completion

        Args:
            request_id: Request ID
            model: Model name
            messages: Input messages
            output: Generated output
            prompt_tokens: Number of prompt tokens
            completion_tokens: Number of completion tokens
            duration_ms: Inference duration in milliseconds
        """
        if not self.enabled or not hasattr(self, 'client'):
            return

        try:
            # Format messages for logging
            messages_dict = [
                {"role": msg.role, "content": msg.content}
                for msg in messages
            ]

            # Trace the completion
            self.client.trace(
                name="llm_completion",
                input={"messages": messages_dict},
                output=output,
                metadata={
                    "model": model,
                    "request_id": request_id,
                    "prompt_tokens": prompt_tokens,
                    "completion_tokens": completion_tokens,
                    "duration_ms": duration_ms
                },
                tags=["llm", "completion"]
            )

            logger.debug(
                "Traced LLM completion to Langfuse",
                extra={
                    "request_id": request_id,
                    "model": model,
                    "duration_ms": duration_ms
                }
            )

        except Exception as e:
            logger.error(
                "Failed to trace to Langfuse",
                exc_info=True,
                extra={"request_id": request_id}
            )

    async def trace_error(
        self,
        request_id: str,
        model: str,
        error: str,
        duration_ms: int
    ):
        """Trace an LLM error

        Args:
            request_id: Request ID
            model: Model name
            error: Error message
            duration_ms: Duration until error
        """
        if not self.enabled or not hasattr(self, 'client'):
            return

        try:
            self.client.trace(
                name="llm_error",
                output={"error": error},
                metadata={
                    "model": model,
                    "request_id": request_id,
                    "duration_ms": duration_ms
                },
                tags=["llm", "error"]
            )

        except Exception as e:
            logger.error(
                "Failed to trace error to Langfuse",
                exc_info=True,
                extra={"request_id": request_id}
            )
