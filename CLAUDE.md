# RAG-Based Hindi & English, Search & QA System: Ministry of Culture Platform

RAG-based conversational QA chatbot + semantic search system for India's Ministry of Culture (culture.gov.in). 16 microservices on AWS ECS (Fargate + GPU EC2). Both Search and Chatbot interfaces process Hindi and English user inputs and documents. Output language is user-selectable from UI with Hindi as the default.

## Quick Commands

- `cd aws && ./deploy.sh` — One-click AWS deployment (Terraform + Docker + ECS)
- `cd aws && ./destroy.sh` — Tear down AWS infrastructure
- `docker-compose up -d` — Local development stack
- `cd database && ./init-db.sh` — Run PostgreSQL migrations
- `pytest testing/ -v` — Run all tests
- `docker-compose logs -f [service]` — View service logs

## Key Files

- `Implementation_Plan/01_Shared_Contracts.md` — **Master source of truth** for ports, APIs, env vars, schemas
- `shared/src/rag_shared/config.py` — Centralized configuration (Pydantic settings)
- `aws/terraform/` — Complete IaC (VPC, ECS, RDS, S3, ALB, IAM)
- `database/migrations/` — 15 sequential SQL migrations
- `.env.example` — Environment variable template

## Architecture

16 services communicating via AWS Cloud Map (`ragqa.local` namespace):

| Service | Port | Tech |
|---------|------|------|
| API Gateway | 8000 | FastAPI, Semantic Router |
| RAG Service | 8001 | LlamaIndex, Milvus, BGE-M3 |
| LLM Service | 8002 | vLLM (Llama 3.1, Mistral NeMo, Gemma 3) |
| Speech Service | 8003 | IndicConformer STT, IndicTTS |
| Translation | 8004 | IndicTrans2 (22 languages) |
| OCR Service | 8005 | Tesseract 5, EasyOCR |
| Data Ingestion | 8006 | Scrapy, Playwright |
| Model Training | 8007 | QLoRA fine-tuning |
| Chat Widget | 80 | React 18, Shadow DOM |
| Search Page | 80 | React 18, Semantic Search SPA |
| Admin Dashboard | 80 | React 18, Recharts |

AWS managed: RDS PostgreSQL 16, ElastiCache Redis 7.x, S3 (3 buckets), CloudWatch.

## Tech Stack

- **Backend:** Python 3.11, FastAPI, Pydantic v2, SQLAlchemy 2.0 async, structlog
- **ML/AI:** LlamaIndex, vLLM, Sentence-Transformers (BGE-M3), SigLIP, Unsloth (QLoRA)
- **Frontend:** React 18, TypeScript, Vite, Tailwind CSS, Recharts
- **Infrastructure:** Terraform 1.6+, Docker, AWS ECS, RDS, ElastiCache, S3, ALB
- **Monitoring:** Prometheus, Grafana, Langfuse

## Code Conventions

- Python: async/await for all FastAPI endpoints, type hints required, snake_case
- Pydantic v2 syntax (Field, ConfigDict, model_validate)
- Structured logging with structlog (JSON format)
- Standard error format: `{"error": {"code": "...", "message": "...", "request_id": "uuid"}}`
- Health checks: `GET /health` on every service returning `{"status": "healthy|unhealthy"}`
- Database: never modify existing migrations, create new numbered files (016+)
- Frontend: functional components with hooks, Tailwind classes, React Query for server state
- Security: GIGW compliance, WCAG 2.1 AA accessibility

## Environment

- Auth: disabled (`AUTH_ENABLED=false`) — VPC isolation provides security
- Region: ap-south-1 (Mumbai)
- GPU: g5.2xlarge (NVIDIA A10G) for LLM, Speech, Translation, Training
- S3 buckets: ragqa-documents, ragqa-models, ragqa-backups
- IAM roles provide S3 credentials (no access keys in code)

## Known Issues

1. **CORS misconfiguration** — speech-service, ocr-service, data-ingestion, llm-service use `allow_origins=["*"]`. Fix: restrict to ALB origin.
2. **IndicTTS placeholder** — Returns silence (zero-filled array). Awaiting AI4Bharat model release.
3. **Rate limiter race condition** — `api-gateway/app/middleware/rate_limiter.py` needs Redis Lua script for atomic check-and-decrement.
4. **embed.js placeholder** — `frontend/chat-widget/embed.js` doesn't load React app. Needs implementation.
5. **Deduplicator no persistence** — data-ingestion deduplicator resets on restart. Needs PostgreSQL backing.
6. **Admin dashboard XSS risk** — Uses localStorage for JWT tokens. Move to httpOnly cookies.
7. **No S3 upload after training** — Fine-tuned models not auto-uploaded. Add save_to_s3() to model-training.

---

**For detailed rules and conventions, see `.claude/rules/` and service-level CLAUDE.md files.**
