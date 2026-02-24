---
name: architecture
description: Detailed system architecture, service relationships, data flow, and inter-service API contracts. Use when understanding how the platform works, investigating service interactions, or designing new features.
---

# RAG-QA Platform Architecture

For the complete service contracts, API schemas, and environment variables, see the project's Implementation_Plan/01_Shared_Contracts.md

## Data Flow

```
User → ALB (public) → Chat Widget / Search Page / Admin Dashboard
                              ↓ (API calls)
                       ALB (internal) → API Gateway (8000)
                              ↓
                       [Semantic Router]
                              ↓
            ┌─────────────────┼─────────────────┐
            ↓                 ↓                 ↓
        Chat/QA           Search          Voice/Translation
     RAG (8001)        RAG (8001)       Speech (8003) / Translation (8004)
        ↓                 ↓
     LLM (8002)      Return results
        ↓
     Response
```

## Service Responsibilities

**API Gateway (8000):** Central router. Semantic Router classifies queries → standard (Llama 3.1 8B), long-context (Mistral NeMo 12B), or multimodal (Gemma 3 12B). Rate limiting, RBAC (disabled), request ID propagation.

**RAG Service (8001):** Embedding (BGE-M3, 768-dim dense + sparse + ColBERT), vector search (Milvus), document chunking (512 tokens, 64 overlap), reranking (top-k=10→5), multimodal retrieval (SigLIP). Redis query cache (TTL 1hr).

**LLM Service (8002):** vLLM inference with AWQ 4-bit quantized models. Guardrails: PII redaction (Aadhaar, PAN), toxicity filter, prompt injection detection. SSE streaming responses.

**Speech (8003):** STT via IndicConformer (23 languages), TTS via IndicTTS (Hindi) + Coqui (English). Audio: WAV 16kHz.

**Translation (8004):** IndicTrans2 (1B params) for 22 Indian languages. Redis cache (24hr TTL). Batch endpoint.

**OCR (8005):** Tesseract 5 (primary) + EasyOCR (fallback). Hindi document preprocessing: binarization, deskew, noise removal.

**Data Ingestion (8006):** Scrapy + Playwright crawlers for 30 Ministry websites. Pipeline: crawl → clean → deduplicate → S3 upload → embed → Milvus index.

**Model Training (8007):** QLoRA fine-tuning (rank=16, alpha=32). Evaluation benchmarks for Hindi cultural domain. Continuous learning from user feedback.

## AWS Infrastructure

- **VPC:** 10.0.0.0/16, 2 public subnets (ALB, NAT), 2 private subnets (all services)
- **Compute:** ECS Fargate (11 services) + EC2 g5.2xlarge GPU (4 services)
- **Database:** RDS PostgreSQL 16 Multi-AZ, 15 migrations
- **Cache:** ElastiCache Redis 7.x with in-transit encryption
- **Storage:** S3 (ragqa-documents, ragqa-models, ragqa-backups)
- **Networking:** Public ALB (frontends, Grafana, Langfuse) + Internal ALB (API Gateway)
- **Service Discovery:** Cloud Map `ragqa.local` private DNS
- **Monitoring:** CloudWatch logs, Prometheus metrics, Grafana dashboards, Langfuse LLM traces

## RBAC Roles (when AUTH_ENABLED=true)

| Role | Permissions |
|------|------------|
| admin | All operations |
| editor | Document upload/edit, scrape jobs, view analytics |
| viewer | Chat, search, download |
| api_consumer | API-only, rate-limited |

## Service Ports (Internal)

| Service | Port | Cloud Map URL |
|---------|------|---|
| API Gateway | 8000 | http://api-gateway.ragqa.local:8000 |
| RAG Service | 8001 | http://rag-service.ragqa.local:8001 |
| LLM Service | 8002 | http://llm-service.ragqa.local:8002 |
| Speech Service | 8003 | http://speech-service.ragqa.local:8003 |
| Translation Service | 8004 | http://translation-service.ragqa.local:8004 |
| OCR Service | 8005 | http://ocr-service.ragqa.local:8005 |
| Data Ingestion | 8006 | http://data-ingestion.ragqa.local:8006 |
| Model Training | 8007 | http://model-training.ragqa.local:8007 |
| Milvus | 19530 | (internal) |
| PostgreSQL | 5432 | (internal) |
| Redis | 6379 | (internal) |

## Key Technologies

**Backend:** Python 3.11, FastAPI 0.104+, Pydantic v2, SQLAlchemy 2.0, Structlog

**ML/AI:** LlamaIndex 0.10+, vLLM 0.3+, BGE-M3 embeddings, PyMilvus, SigLIP, Unsloth, QLoRA

**Speech:** AI4Bharat IndicConformer (STT), IndicTTS (TTS), Coqui TTS fallback

**Translation:** AI4Bharat IndicTrans2 (22 languages)

**OCR:** Tesseract 5, EasyOCR

**Frontend:** React 18, TypeScript, Vite, Tailwind CSS, Recharts, React Query

**Infrastructure:** Terraform 1.6+, Docker, AWS ECS Fargate, RDS, ElastiCache, S3

**Monitoring:** Prometheus, Grafana, Langfuse, CloudWatch
