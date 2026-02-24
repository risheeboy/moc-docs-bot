### STREAM 5: LLM Serving Service (Multi-Model via vLLM)

**Agent Goal:** Configure and deploy the **multi-model** LLM inference service with GPU support. The Design specifies three specialized models served via vLLM.

**Files to create:**
```
llm-service/
├── Dockerfile                      # Based on vllm/vllm-openai
├── requirements.txt
├── app/
│   ├── __init__.py
│   ├── main.py                     # FastAPI wrapper / vLLM multi-model config
│   ├── config.py                   # Model IDs, quantization, GPU allocation per model
│   ├── routers/
│   │   ├── __init__.py
│   │   ├── completions.py          # POST /v1/completions (OpenAI-compatible)
│   │   ├── chat.py                 # POST /v1/chat/completions (multi-model)
│   │   └── health.py               # GET /health (per-model loaded check)
│   ├── services/
│   │   ├── __init__.py
│   │   ├── model_manager.py        # Load/unload models, GPU memory management
│   │   ├── model_registry.py       # Registry: model_id → vLLM engine mapping
│   │   ├── prompt_templates.py     # Hindi/English prompt templates per task
│   │   ├── generation.py           # Inference logic with streaming
│   │   └── guardrails.py           # Output filtering, safety checks, PII redaction
│   ├── prompts/
│   │   ├── qa_hindi.txt            # Hindi RAG QA system prompt
│   │   ├── qa_english.txt          # English RAG QA system prompt
│   │   ├── summarize_hindi.txt     # Hindi summarization prompt
│   │   ├── summarize_english.txt   # English summarization prompt
│   │   ├── sentiment.txt           # Sentiment analysis prompt
│   │   └── search_summary.txt      # Generate AI summary for search results
│   └── utils/
│       ├── __init__.py
│       ├── langfuse_tracer.py      # Langfuse integration for LLM call tracing
│       └── metrics.py              # GPU utilization, tokens/sec, latency per model
├── model-download.sh               # Script to pre-download all model weights
└── tests/
    ├── test_completions.py
    ├── test_multi_model.py
    └── test_hindi_generation.py
```

**Models (from Design Document):**

| Model | Role | Quantization | Use Case |
|---|---|---|---|
| **Llama 3.1 8B Instruct** | Standard QA | AWQ 4-bit | Factual Q&A, chatbot responses, sentiment |
| **Mistral NeMo 12B** | Long-context | AWQ 4-bit | Summarization, long documents (128K ctx) |
| **Gemma 3** | Multimodal | AWQ 4-bit | Image-based queries, visual document understanding |

**GPU allocation strategy:** On a single GPU (e.g., 48GB A6000 or 80GB A100), models can be loaded on-demand with LRU eviction, or multiple models can share GPU via vLLM's `--max-model-len` and `--gpu-memory-utilization` flags. For smaller GPUs (24GB), only one model at a time with swapping.

**Requires:** GPU access. No code dependencies on other streams.

---


---

## Agent Prompt

### Agent 5: LLM Service (Multi-Model vLLM)
```
Build multi-model LLM inference service using vLLM with OpenAI-compatible API.
Three models:
- Llama 3.1 8B Instruct (AWQ 4-bit) — standard Q&A, chatbot, sentiment
- Mistral NeMo 12B (AWQ 4-bit) — summarization, long documents (128K context)
- Gemma 3 (AWQ 4-bit) — multimodal / visual document queries
Model registry with routing support (API Gateway's Semantic Router selects model).
Prompt templates for: Hindi QA, English QA, summarization, sentiment,
search result AI summary generation.
Guardrails (guardrails.py) must include:
  - PII detection + redaction (Aadhaar numbers, phone numbers, names)
  - Hallucination detection (cross-check response against provided context)
  - Topic guardrails (restrict to Ministry of Culture domain; reject off-topic)
  - Profanity/toxicity filter for Hindi and English
A/B testing: add model_version parameter to completions endpoint so API
Gateway can route to different fine-tuned model versions for comparison.
GPU required. Langfuse tracing integration. Streaming via SSE.
```

