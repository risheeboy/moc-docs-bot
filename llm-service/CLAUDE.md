# LLM Service

FastAPI on port 8002. LLM inference with vLLM backend (GPU-only, g5.2xlarge minimum).

## Key Files

- `app/main.py` — FastAPI application
- `app/services/generation.py` — vLLM inference wrapper, streaming
- `app/services/guardrails.py` — PII detection, toxicity filter, injection detection
- `app/services/model_manager.py` — Model loading and caching
- `app/config.py` — Model paths, inference config

## Models

Three models via semantic router (all AWQ 4-bit quantized):
- Llama 3.1 8B — Standard general-purpose
- Mistral NeMo 12B — Long-context (extended window)
- Gemma 3 12B — Multimodal (image + text)

## Endpoints

- `POST /completions` — Text generation (streaming SSE)
- `POST /completions/batch` — Batch inference (non-streaming)
- `GET /models` — List available models
- `GET /health` — Health check

## GPU Requirements

- Instance: g5.2xlarge (NVIDIA A10G 24GB VRAM)
- Compute: CUDA 11.8+, PyTorch GPU
- All 3 models fit in VRAM with quantization

## Dependencies

- vLLM (inference backend)
- PyTorch (GPU support)
- Transformers library
- Model weights from HuggingFace

## Known Issues

1. **CORS misconfiguration** — Uses `allow_origins=["*"]`. Fix: restrict to ALB domain.
2. **No mid-stream error handling** — SSE can't handle errors after streaming starts.
3. **No token counting** — Can't pre-validate input token length.
