"""Metrics utilities for monitoring and evaluation."""

from prometheus_client import Counter, Histogram, Gauge, generate_latest, CONTENT_TYPE_LATEST
from typing import Dict, Any


# HTTP metrics
http_requests_total = Counter(
    "http_requests_total",
    "Total HTTP requests",
    ["method", "endpoint", "status_code"],
)

http_request_duration_seconds = Histogram(
    "http_request_duration_seconds",
    "HTTP request latency in seconds",
    ["method", "endpoint"],
    buckets=(0.01, 0.05, 0.1, 0.5, 1.0, 2.5, 5.0, 10.0),
)

http_request_size_bytes = Histogram(
    "http_request_size_bytes",
    "HTTP request body size in bytes",
    ["method", "endpoint"],
)

http_response_size_bytes = Histogram(
    "http_response_size_bytes",
    "HTTP response body size in bytes",
    ["method", "endpoint"],
)

# Training metrics
training_jobs_total = Counter(
    "training_jobs_total",
    "Total training jobs initiated",
    ["model", "status"],
)

training_duration_seconds = Histogram(
    "training_duration_seconds",
    "Training job duration in seconds",
    ["model"],
    buckets=(60, 300, 900, 1800, 3600, 7200, 14400, 28800),
)

training_loss = Gauge(
    "training_loss_current",
    "Current training loss",
    ["model", "job_id"],
)

training_eval_loss = Gauge(
    "training_eval_loss_current",
    "Current evaluation loss",
    ["model", "job_id"],
)

# GPU metrics
gpu_memory_utilization = Gauge(
    "gpu_memory_utilization_percent",
    "GPU memory utilization percentage",
    ["device_id"],
)

gpu_power_usage = Gauge(
    "gpu_power_usage_watts",
    "GPU power usage in watts",
    ["device_id"],
)

# Evaluation metrics
evaluation_jobs_total = Counter(
    "evaluation_jobs_total",
    "Total evaluation jobs",
    ["model", "status"],
)

evaluation_duration_seconds = Histogram(
    "evaluation_duration_seconds",
    "Evaluation duration in seconds",
    ["model"],
)

evaluation_metric_value = Gauge(
    "evaluation_metric_value",
    "Evaluation metric values",
    ["model", "version", "metric_name"],
)

# Data metrics
qa_pairs_generated_total = Counter(
    "qa_pairs_generated_total",
    "Total QA pairs generated",
)

hallucination_rate = Gauge(
    "hallucination_rate_current",
    "Current hallucination rate",
    ["model", "version"],
)


def record_http_request(
    method: str,
    endpoint: str,
    status_code: int,
    duration_seconds: float,
    request_size: int = 0,
    response_size: int = 0,
):
    """Record HTTP request metrics.

    Args:
        method: HTTP method
        endpoint: API endpoint
        status_code: HTTP status code
        duration_seconds: Request duration
        request_size: Request body size in bytes
        response_size: Response body size in bytes
    """
    http_requests_total.labels(method=method, endpoint=endpoint, status_code=status_code).inc()
    http_request_duration_seconds.labels(method=method, endpoint=endpoint).observe(duration_seconds)
    if request_size > 0:
        http_request_size_bytes.labels(method=method, endpoint=endpoint).observe(request_size)
    if response_size > 0:
        http_response_size_bytes.labels(method=method, endpoint=endpoint).observe(response_size)


def record_training_job(model: str, job_id: str, status: str):
    """Record training job initiation.

    Args:
        model: Model name
        job_id: Job ID
        status: Job status (started, completed, failed)
    """
    training_jobs_total.labels(model=model, status=status).inc()


def record_training_progress(model: str, job_id: str, loss: float, eval_loss: float):
    """Record training progress.

    Args:
        model: Model name
        job_id: Job ID
        loss: Training loss
        eval_loss: Evaluation loss
    """
    training_loss.labels(model=model, job_id=job_id).set(loss)
    training_eval_loss.labels(model=model, job_id=job_id).set(eval_loss)


def record_training_duration(model: str, duration_seconds: float):
    """Record training duration.

    Args:
        model: Model name
        duration_seconds: Duration in seconds
    """
    training_duration_seconds.labels(model=model).observe(duration_seconds)


def record_gpu_metrics(device_id: str, memory_percent: float, power_watts: float):
    """Record GPU metrics.

    Args:
        device_id: GPU device ID
        memory_percent: Memory utilization percentage
        power_watts: Power usage in watts
    """
    gpu_memory_utilization.labels(device_id=device_id).set(memory_percent)
    gpu_power_usage.labels(device_id=device_id).set(power_watts)


def record_evaluation_job(model: str, status: str):
    """Record evaluation job.

    Args:
        model: Model name
        status: Job status
    """
    evaluation_jobs_total.labels(model=model, status=status).inc()


def record_evaluation_duration(model: str, duration_seconds: float):
    """Record evaluation duration.

    Args:
        model: Model name
        duration_seconds: Duration in seconds
    """
    evaluation_duration_seconds.labels(model=model).observe(duration_seconds)


def record_evaluation_metrics(model: str, version: str, metrics: Dict[str, float]):
    """Record evaluation metrics.

    Args:
        model: Model name
        version: Model version
        metrics: Dictionary of metric name to value
    """
    for metric_name, value in metrics.items():
        evaluation_metric_value.labels(model=model, version=version, metric_name=metric_name).set(value)


def record_qa_pairs_generated(count: int):
    """Record generated QA pairs.

    Args:
        count: Number of pairs generated
    """
    qa_pairs_generated_total.inc(count)


def record_hallucination_rate(model: str, version: str, rate: float):
    """Record hallucination rate.

    Args:
        model: Model name
        version: Model version
        rate: Hallucination rate (0.0-1.0)
    """
    hallucination_rate.labels(model=model, version=version).set(rate)


def get_metrics() -> bytes:
    """Get all metrics in Prometheus format.

    Returns:
        Prometheus-formatted metrics
    """
    return generate_latest()
