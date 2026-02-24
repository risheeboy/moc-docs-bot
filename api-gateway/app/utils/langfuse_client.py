"""Langfuse tracing integration for LLM observability."""

from langfuse import Langfuse
from typing import Optional
import logging

logger = logging.getLogger(__name__)


class LangfuseTracer:
    """Wrapper for Langfuse LLM tracing."""

    def __init__(self, public_key: Optional[str] = None, secret_key: Optional[str] = None):
        """Initialize Langfuse tracer."""
        self.enabled = public_key is not None and secret_key is not None
        self.client = None

        if self.enabled:
            try:
                self.client = Langfuse(public_key=public_key, secret_key=secret_key)
                logger.info("Langfuse tracing enabled")
            except Exception as e:
                logger.error(f"Langfuse initialization error: {e}")
                self.enabled = False

    def trace_llm_call(
        self,
        request_id: str,
        model: str,
        messages: list[dict],
        response: str,
        tokens_used: int,
        latency_ms: float,
    ):
        """Trace LLM call to Langfuse."""
        if not self.enabled or not self.client:
            return

        try:
            # Send trace to Langfuse
            # Implementation depends on Langfuse SDK version
            self.client.log(
                trace_id=request_id,
                name=f"llm_call_{model}",
                input={"messages": messages},
                output=response,
                model=model,
                tokens_used=tokens_used,
                latency_ms=latency_ms,
            )
        except Exception as e:
            logger.error(f"Langfuse tracing error: {e}")

    def trace_rag_retrieval(
        self,
        request_id: str,
        query: str,
        results_count: int,
        latency_ms: float,
        confidence: float,
    ):
        """Trace RAG retrieval to Langfuse."""
        if not self.enabled or not self.client:
            return

        try:
            self.client.log(
                trace_id=request_id,
                name="rag_retrieval",
                input={"query": query},
                output={"results_count": results_count, "confidence": confidence},
                latency_ms=latency_ms,
            )
        except Exception as e:
            logger.error(f"Langfuse RAG tracing error: {e}")

    def flush(self):
        """Flush pending traces."""
        if self.enabled and self.client:
            try:
                self.client.flush()
            except Exception as e:
                logger.error(f"Langfuse flush error: {e}")
