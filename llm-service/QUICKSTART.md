# LLM Service - Quick Start Guide

## Build & Run

### Docker Build
```bash
cd llm-service
docker build -t llm-service:1.0.0 .
```

### Run Locally
```bash
pip install -r requirements.txt
uvicorn app.main:app --host 0.0.0.0 --port 8002 --reload
```

### Docker Run
```bash
docker run -p 8002:8002 \
  -e LLM_LOAD_ON_STARTUP=true \
  -e LLM_PRELOAD_MODELS=standard \
  --gpus all \
  llm-service:1.0.0
```

## Test Endpoints

### Health Check
```bash
curl http://localhost:8002/health | jq
```

### List Models
```bash
curl http://localhost:8002/v1/models | jq
```

### Chat Completion (Non-streaming)
```bash
curl -X POST http://localhost:8002/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "meta-llama/Llama-3.1-8B-Instruct-AWQ",
    "messages": [
      {"role": "system", "content": "You are a helpful assistant."},
      {"role": "user", "content": "What is 2+2?"}
    ],
    "temperature": 0.3,
    "max_tokens": 100,
    "stream": false
  }' | jq
```

### Chat Completion (Streaming)
```bash
curl -X POST http://localhost:8002/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "meta-llama/Llama-3.1-8B-Instruct-AWQ",
    "messages": [{"role": "user", "content": "Hello"}],
    "stream": true
  }'
```

### Metrics
```bash
curl http://localhost:8002/metrics | grep llm_
```

## Environment Variables

### Critical
```bash
LLM_MODEL_STANDARD=meta-llama/Llama-3.1-8B-Instruct-AWQ
LLM_MODEL_LONGCTX=mistralai/Mistral-NeMo-Instruct-2407-AWQ
LLM_MODEL_MULTIMODAL=google/gemma-3-12b-it-awq
```

### GPU Tuning
```bash
LLM_GPU_MEMORY_UTILIZATION=0.85     # Adjust for your GPU
LLM_LOAD_ON_STARTUP=true
LLM_PRELOAD_MODELS=standard,longctx
```

### Observability
```bash
LANGFUSE_ENABLED=true
LANGFUSE_HOST=http://langfuse:3001
LANGFUSE_PUBLIC_KEY=<key>
LANGFUSE_SECRET_KEY=<secret>
```

## Testing

```bash
# Run all tests
pytest tests/ -v

# Run specific test file
pytest tests/test_completions.py -v

# Run with coverage
pytest --cov=app tests/
```

## Troubleshooting

### Model Not Loading
```bash
# Check GPU
nvidia-smi

# Check logs
docker logs llm-service

# Reduce memory usage
export LLM_GPU_MEMORY_UTILIZATION=0.7
```

### High Latency
```bash
# Check metrics
curl http://localhost:8002/metrics | grep duration

# Check GPU utilization
nvidia-smi -l
```

### Out of Memory
```bash
# Reduce context length
LLM_MAX_MODEL_LEN_STANDARD=4096

# Load fewer models
LLM_PRELOAD_MODELS=standard
```

## Project Structure

```
llm-service/
├── app/
│   ├── main.py                  # FastAPI app
│   ├── config.py                # Configuration
│   ├── models/                  # Pydantic schemas
│   ├── routers/                 # API endpoints
│   ├── services/                # Business logic
│   └── utils/                   # Metrics, tracing
├── tests/                       # Unit tests
├── Dockerfile                   # Production image
├── requirements.txt             # Dependencies
└── README.md                    # Full documentation
```

## API Summary

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/health` | GET | Health check |
| `/v1/models` | GET | List models |
| `/v1/chat/completions` | POST | Chat completion |
| `/metrics` | GET | Prometheus metrics |

## Key Features

✓ OpenAI-compatible API
✓ Multi-model serving (3 models)
✓ Streaming support (SSE)
✓ Content guardrails (PII, toxicity)
✓ Hindi/English support
✓ Prometheus metrics
✓ Langfuse tracing
✓ 26 unit tests
✓ Production-ready Docker image

## Dependencies

**Python:** 3.11+
**GPU:** NVIDIA with CUDA 12.1+
**Memory:** 48GB+ VRAM recommended

## Links

- [Full Documentation](README.md)
- [Implementation Details](IMPLEMENTATION.md)
- [API Contracts](../Implementation_Plan/01_Shared_Contracts.md)
- [Stream Specification](../Implementation_Plan/Stream_05_LLM_Service.md)
