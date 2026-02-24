# LLM Service

Multi-model LLM inference service with OpenAI-compatible API for the RAG-based Hindi QA system.

## Overview

This service provides GPU-accelerated text generation using vLLM, supporting three specialized models:

- **Llama 3.1 8B Instruct (AWQ)**: Standard Q&A, chatbot responses, sentiment analysis
- **Mistral NeMo 12B (AWQ)**: Summarization, long-context documents (128K tokens)
- **Gemma 3 (AWQ)**: Multimodal reasoning, image understanding

Features:
- OpenAI-compatible API (`/v1/chat/completions`)
- Streaming support (Server-Sent Events)
- Multi-model serving with dynamic loading
- Content guardrails (PII redaction, toxicity filtering, hallucination detection)
- Hindi/English prompt templates
- Langfuse observability integration
- Prometheus metrics

## Architecture

```
┌─────────────────────────────────────────┐
│   FastAPI Application (Port 8002)      │
├─────────────────────────────────────────┤
│                                         │
│  ┌─────────────────────────────────┐   │
│  │   Completions Router            │   │
│  │ POST /v1/chat/completions       │   │
│  └────────────┬────────────────────┘   │
│               │                         │
│  ┌────────────▼────────────────────┐   │
│  │  Generation Service             │   │
│  │  - Prompt formatting            │   │
│  │  - Streaming & non-streaming    │   │
│  │  - Token counting               │   │
│  └────────────┬────────────────────┘   │
│               │                         │
│  ┌────────────▼────────────────────┐   │
│  │  Model Manager (vLLM)           │   │
│  │  - Multi-model serving          │   │
│  │  - GPU memory management        │   │
│  │  - Load/unload models           │   │
│  └────────────┬────────────────────┘   │
│               │                         │
│  ┌────────────▼────────────────────┐   │
│  │  GPU (CUDA)                     │   │
│  │  - vLLM engines                 │   │
│  └─────────────────────────────────┘   │
│                                         │
│  ┌─────────────────────────────────┐   │
│  │  Guardrails Service             │   │
│  │  - PII detection/redaction      │   │
│  │  - Toxicity filtering           │   │
│  │  - Hallucination detection      │   │
│  └─────────────────────────────────┘   │
│                                         │
│  ┌─────────────────────────────────┐   │
│  │  Health Router                  │   │
│  │  GET /health (per-model status) │   │
│  └─────────────────────────────────┘   │
│                                         │
└─────────────────────────────────────────┘
```

## API Endpoints

### Chat Completions (OpenAI-compatible)

**POST** `/v1/chat/completions`

OpenAI-compatible endpoint for text generation. Supports both streaming and non-streaming responses.

**Request:**
```json
{
  "model": "meta-llama/Llama-3.1-8B-Instruct-AWQ",
  "messages": [
    {"role": "system", "content": "You are a helpful assistant..."},
    {"role": "user", "content": "Question about Indian culture"}
  ],
  "temperature": 0.3,
  "max_tokens": 1024,
  "top_p": 0.95,
  "top_k": 40,
  "stream": false,
  "model_version": "v1.2-finetuned"
}
```

**Response (non-streaming):**
```json
{
  "id": "chatcmpl-uuid",
  "object": "chat.completion",
  "created": 1234567890,
  "model": "meta-llama/Llama-3.1-8B-Instruct-AWQ",
  "choices": [
    {
      "index": 0,
      "message": {
        "role": "assistant",
        "content": "Response text..."
      },
      "finish_reason": "stop"
    }
  ],
  "usage": {
    "prompt_tokens": 512,
    "completion_tokens": 256,
    "total_tokens": 768
  }
}
```

**Response (streaming - SSE):**
```
data: {"id":"chatcmpl-uuid","choices":[{"delta":{"content":"token"},"index":0}]}
data: {"id":"chatcmpl-uuid","choices":[{"delta":{"content":" more"},"index":0}]}
data: [DONE]
```

### Health Check

**GET** `/health`

Returns service health status and per-model loaded state.

**Response:**
```json
{
  "status": "healthy",
  "service": "llm-service",
  "version": "1.0.0",
  "uptime_seconds": 3612,
  "timestamp": "2026-02-24T10:30:00Z",
  "dependencies": {
    "llm_standard": {
      "status": "healthy",
      "latency_ms": 12
    },
    "llm_longctx": {
      "status": "healthy",
      "latency_ms": 8
    },
    "llm_multimodal": {
      "status": "unhealthy",
      "latency_ms": 0
    }
  }
}
```

### Models List

**GET** `/v1/models`

Lists available models.

**Response:**
```json
{
  "object": "list",
  "data": [
    {
      "id": "meta-llama/Llama-3.1-8B-Instruct-AWQ",
      "object": "model",
      "owned_by": "meta",
      "permission": []
    },
    {
      "id": "mistralai/Mistral-NeMo-Instruct-2407-AWQ",
      "object": "model",
      "owned_by": "mistral",
      "permission": []
    },
    {
      "id": "google/gemma-3-12b-it-awq",
      "object": "model",
      "owned_by": "google",
      "permission": []
    }
  ]
}
```

### Metrics

**GET** `/metrics`

Prometheus metrics in text format.

## Configuration

Environment variables (from `.env`):

```bash
# Service
APP_ENV=production                          # production | staging | development
APP_DEBUG=false
APP_LOG_LEVEL=INFO

# Models
LLM_MODEL_STANDARD=meta-llama/Llama-3.1-8B-Instruct-AWQ
LLM_MODEL_LONGCTX=mistralai/Mistral-NeMo-Instruct-2407-AWQ
LLM_MODEL_MULTIMODAL=google/gemma-3-12b-it-awq

# GPU
LLM_GPU_MEMORY_UTILIZATION=0.85
LLM_MAX_MODEL_LEN_STANDARD=8192
LLM_MAX_MODEL_LEN_LONGCTX=131072
LLM_MAX_MODEL_LEN_MULTIMODAL=8192

# Loading
LLM_LOAD_ON_STARTUP=true
LLM_PRELOAD_MODELS=standard,longctx  # Comma-separated

# Langfuse
LANGFUSE_ENABLED=true
LANGFUSE_HOST=http://langfuse:3001
LANGFUSE_PUBLIC_KEY=...
LANGFUSE_SECRET_KEY=...

# Cache
REDIS_HOST=redis
REDIS_PORT=6379
REDIS_PASSWORD=...
```

## Installation & Deployment

### Prerequisites

- NVIDIA GPU (48GB+ VRAM recommended)
- CUDA 12.1+
- Docker & Docker Compose

### Build Docker Image

```bash
cd llm-service
docker build -t llm-service:1.0.0 .
```

### Download Models

Before deployment, pre-download model weights (optional but recommended):

```bash
bash model-download.sh
```

This downloads ~80GB of model weights to the `model-cache` volume.

### Run with Docker Compose

```yaml
llm-service:
  build: ./llm-service
  image: llm-service:1.0.0
  container_name: llm-service
  ports:
    - "8002:8002"
  environment:
    - LLM_LOAD_ON_STARTUP=true
    - LLM_PRELOAD_MODELS=standard,longctx
    - LLM_GPU_MEMORY_UTILIZATION=0.85
    - LANGFUSE_ENABLED=true
    - LANGFUSE_HOST=http://langfuse:3001
  volumes:
    - model-cache:/root/.cache/huggingface/hub
  deploy:
    resources:
      reservations:
        devices:
          - driver: nvidia
            count: 1
            capabilities: [gpu]
  healthcheck:
    test: ["CMD", "curl", "-f", "http://localhost:8002/health"]
    interval: 30s
    timeout: 10s
    retries: 3
    start_period: 60s
```

### Local Development

```bash
# Install dependencies
pip install -r requirements.txt

# Run server
uvicorn app.main:app --host 0.0.0.0 --port 8002 --reload

# Run tests
pytest tests/

# Check with curl
curl -X POST http://localhost:8002/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "meta-llama/Llama-3.1-8B-Instruct-AWQ",
    "messages": [{"role": "user", "content": "Hello"}],
    "stream": false
  }'
```

## Model Selection & Routing

The API Gateway's Semantic Router selects the appropriate model based on query type:

| Query Type | Model | Use Case |
|---|---|---|
| Standard Q&A | Llama 3.1 8B | Short responses, factual questions |
| Long context | Mistral NeMo 12B | Documents >4K tokens, summarization |
| Multimodal | Gemma 3 | Image queries, visual understanding |

Example: If a user asks about a large PDF document, the API Gateway routes to Mistral NeMo 12B for its 128K context window.

## Content Guardrails

### PII Redaction

Automatically redacts Personally Identifiable Information:
- Aadhaar numbers (12-digit)
- Phone numbers (+91 or 0 prefixed)
- Email addresses
- PAN (10-character format)

Example:
```
Input:  "Contact me at user@example.com or call 9876543210"
Output: "Contact me at [EMAIL_REDACTED] or call [PHONE_REDACTED]"
```

### Toxicity Filtering

Detects and removes offensive language in both Hindi and English.

Filtered keywords: hate speech, slurs, profanity

### Hallucination Detection

Basic cross-reference: checks if generated claims overlap with provided context.

Advanced: Can be extended with semantic similarity scoring.

## Metrics

Prometheus metrics exposed at `/metrics`:

```
llm_tokens_generated_total{model="..."}
llm_prompt_tokens_total{model="..."}
llm_completion_tokens_total{model="..."}
llm_inference_duration_seconds{model="..."}
llm_requests_total{model="...", status="success|error"}
llm_model_loaded{model="..."}  # 1=loaded, 0=not loaded
llm_cache_hits_total{model="..."}
llm_cache_misses_total{model="..."}
```

## Logging

Structured JSON logging with fields:
- `timestamp`: ISO 8601 UTC
- `level`: DEBUG, INFO, WARNING, ERROR, CRITICAL
- `service`: "llm-service"
- `request_id`: UUID for tracing
- `message`: Log message
- `logger`: Module path
- `extra`: Additional context

Example:
```json
{
  "timestamp": "2026-02-24T10:30:00.123Z",
  "level": "INFO",
  "service": "llm-service",
  "request_id": "550e8400-e29b-41d4-a716-446655440000",
  "message": "Chat completion successful",
  "logger": "app.routers.completions",
  "extra": {
    "model": "meta-llama/Llama-3.1-8B-Instruct-AWQ",
    "prompt_tokens": 512,
    "completion_tokens": 256,
    "duration_ms": 1234
  }
}
```

## Observability

### Langfuse Integration

All LLM calls are traced to Langfuse for:
- Request/response logging
- Token usage tracking
- Latency analysis
- Cost tracking
- Model A/B testing

Access at: http://langfuse:3001

### Health Checks

- `/health` endpoint reports per-model status
- Kubernetes probes: liveness, readiness, startup
- Dependency status: model loading state, GPU memory

## Error Handling

Standard error format (§4, Shared Contracts):

```json
{
  "error": {
    "code": "MODEL_LOADING",
    "message": "Model is not loaded. Please try again.",
    "request_id": "550e8400-e29b-41d4-a716-446655440000"
  }
}
```

Common error codes:
- `INVALID_REQUEST`: Malformed request
- `MODEL_LOADING`: Model still loading (HTTP 503)
- `INTERNAL_ERROR`: Server error (HTTP 500)
- `RATE_LIMIT_EXCEEDED`: Too many requests (HTTP 429)

## Performance Tuning

### GPU Memory Optimization

For 24GB GPU (RTX 3090):
```bash
LLM_GPU_MEMORY_UTILIZATION=0.75  # More conservative
LLM_PRELOAD_MODELS=standard      # Load only one model
```

For 48GB GPU (A6000):
```bash
LLM_GPU_MEMORY_UTILIZATION=0.85
LLM_PRELOAD_MODELS=standard,longctx  # Load two models
```

For 80GB GPU (A100):
```bash
LLM_GPU_MEMORY_UTILIZATION=0.90
LLM_PRELOAD_MODELS=standard,longctx,multimodal  # Load all
```

### Token Throughput

Typical throughput on A6000 with standard model:
- Prompt: ~1000 tokens/sec
- Completion: ~80-100 tokens/sec

## Testing

```bash
# Unit tests
pytest tests/test_completions.py -v
pytest tests/test_multi_model.py -v
pytest tests/test_hindi_generation.py -v

# Coverage
pytest --cov=app tests/

# Integration test
python -m pytest tests/ -v --tb=short
```

## Troubleshooting

### Model not loading
```
Check GPU memory: nvidia-smi
Check vLLM logs: docker logs llm-service
Reduce gpu_memory_utilization in config
```

### High latency
```
Check GPU utilization: nvidia-smi
Monitor metrics at /metrics
Check for CPU bottlenecks: top, htop
```

### OOM (Out of Memory) errors
```
Reduce max_model_len in config
Unload non-essential models
Use smaller batch size
Enable CPU offload: swap_space=4
```

## Related Documentation

- Design Document: `/Implementation_Plan/00_Overview.md`
- API Contracts: `/Implementation_Plan/01_Shared_Contracts.md`
- Stream 5 Specification: `/Implementation_Plan/Stream_05_LLM_Service.md`
- vLLM Documentation: https://docs.vllm.ai/
- OpenAI API Reference: https://platform.openai.com/docs/api-reference

## License

Part of RAG-based Hindi QA System for Ministry of Culture, Government of India.
