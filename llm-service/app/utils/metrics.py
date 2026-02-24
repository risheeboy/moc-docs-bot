"""Prometheus metrics for LLM Service

Tracks inference performance, token generation, and model status.
"""

import logging
from prometheus_client import Counter, Histogram, Gauge

logger = logging.getLogger(__name__)


class MetricsCollector:
    """Collects and reports Prometheus metrics for LLM service"""

    def __init__(self):
        """Initialize metrics collector"""

        # Token generation metrics
        self.tokens_generated = Counter(
            'llm_tokens_generated_total',
            'Total tokens generated',
            ['model']
        )

        self.prompt_tokens = Counter(
            'llm_prompt_tokens_total',
            'Total prompt tokens processed',
            ['model']
        )

        self.completion_tokens = Counter(
            'llm_completion_tokens_total',
            'Total completion tokens generated',
            ['model']
        )

        # Inference duration
        self.inference_duration = Histogram(
            'llm_inference_duration_seconds',
            'Inference duration in seconds',
            ['model'],
            buckets=(0.1, 0.5, 1.0, 2.0, 5.0, 10.0, 30.0, 60.0)
        )

        # Request count
        self.requests_total = Counter(
            'llm_requests_total',
            'Total LLM requests',
            ['model', 'status']
        )

        # Model loaded status
        self.model_loaded = Gauge(
            'llm_model_loaded',
            'Whether a model is currently loaded (1=loaded, 0=not loaded)',
            ['model']
        )

        # Cache metrics
        self.cache_hits = Counter(
            'llm_cache_hits_total',
            'Total cache hits',
            ['model']
        )

        self.cache_misses = Counter(
            'llm_cache_misses_total',
            'Total cache misses',
            ['model']
        )

        # GPU utilization
        self.gpu_memory_usage = Gauge(
            'llm_gpu_memory_usage_bytes',
            'GPU memory usage in bytes',
            ['model']
        )

        # Token throughput
        self.tokens_per_second = Gauge(
            'llm_tokens_per_second',
            'Tokens generated per second',
            ['model']
        )

    def record_inference(
        self,
        model: str,
        prompt_tokens: int,
        completion_tokens: int,
        duration_seconds: float = 0.0,
        status: str = "success"
    ):
        """Record an inference operation

        Args:
            model: Model name
            prompt_tokens: Number of prompt tokens
            completion_tokens: Number of completion tokens
            duration_seconds: Duration of inference
            status: success or error
        """
        try:
            # Record token counts
            total_tokens = prompt_tokens + completion_tokens
            self.tokens_generated.labels(model=model).inc(total_tokens)
            self.prompt_tokens.labels(model=model).inc(prompt_tokens)
            self.completion_tokens.labels(model=model).inc(completion_tokens)

            # Record duration
            if duration_seconds > 0:
                self.inference_duration.labels(model=model).observe(duration_seconds)

                # Calculate and record throughput
                if duration_seconds > 0:
                    throughput = completion_tokens / duration_seconds
                    self.tokens_per_second.labels(model=model).set(throughput)

            # Record request count
            self.requests_total.labels(model=model, status=status).inc()

        except Exception as e:
            logger.error("Failed to record metrics", exc_info=True)

    def record_model_loaded(self, model: str, is_loaded: bool):
        """Record whether a model is loaded

        Args:
            model: Model name
            is_loaded: Whether model is loaded
        """
        try:
            self.model_loaded.labels(model=model).set(1 if is_loaded else 0)
        except Exception as e:
            logger.error("Failed to record model loaded status", exc_info=True)

    def record_cache_hit(self, model: str):
        """Record a cache hit

        Args:
            model: Model name
        """
        try:
            self.cache_hits.labels(model=model).inc()
        except Exception as e:
            logger.error("Failed to record cache hit", exc_info=True)

    def record_cache_miss(self, model: str):
        """Record a cache miss

        Args:
            model: Model name
        """
        try:
            self.cache_misses.labels(model=model).inc()
        except Exception as e:
            logger.error("Failed to record cache miss", exc_info=True)

    def set_gpu_memory(self, model: str, bytes_used: int):
        """Set GPU memory usage

        Args:
            model: Model name
            bytes_used: GPU memory used in bytes
        """
        try:
            self.gpu_memory_usage.labels(model=model).set(bytes_used)
        except Exception as e:
            logger.error("Failed to record GPU memory", exc_info=True)
