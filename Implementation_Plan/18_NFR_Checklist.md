## Non-Functional Requirements Checklist

| # | Requirement (RFP ref) | How Addressed | Stream(s) |
|---|---|---|---|
| 1 | **Two user interfaces** (p7) | Conversational Chatbot + Unified Semantic Search Page | 8, 11 |
| 2 | **AI-powered search** across 30 platforms (p7) | Semantic search with AI summaries, multimedia, events, facets | 4, 11, 12 |
| 3 | **Conversational chatbot** (p7) | Multi-turn, context-aware, source citations, fallback mechanism | 3, 8 |
| 4 | **Multilingual (22 scheduled languages)** (p7) | IndicTrans2 + BGE-M3 + Language enum | 10, 13 |
| 5 | **Hindi + English voice** (p7) | IndicConformer STT + IndicTTS | 6 |
| 6 | **Content summarization** (p7) | Mistral NeMo 12B (128K context) via summarization prompt | 5 |
| 7 | **Sentiment analysis on feedback** (p7) | Async LLM sentiment → stored in feedback table → dashboard | 3, 5, 9 |
| 8 | **OCR / Document digitization** (p7) | Tesseract + EasyOCR (Hindi + English) | 7 |
| 9 | **WCAG 2.1 AA Accessibility** (p8) | Keyboard nav, ARIA, contrast, font scaling in both UIs | 8, 11, 15 |
| 10 | **GIGW compliance** (p8) | Government branding, bilingual UI, standard footer, sitemap | 8, 11, 16 |
| 11 | **Open-source models only** (p8) | All models are open-source (Llama, Mistral, Gemma, AI4Bharat) | 5, 6, 13 |
| 12 | **On-premise / Data sovereignty** (p10) | All Docker; no external API calls; all models local | 1 |
| 13 | **NIC/MeitY Data Centre hosting** (p10) | Documented in deployment guide; Docker host compliance | 1, 16 |
| 14 | **10TB storage** (p10) | S3 configured with 10TB capacity | 1 |
| 15 | **Encryption at rest** (p9) | PostgreSQL TDE / AES utility in shared lib | 2, 10 |
| 16 | **Encryption in transit** (p9) | NGINX TLS termination | 1 |
| 17 | **RBAC** (p9) | Roles table + permissions matrix (admin/editor/viewer/api_consumer) | 2, 3 |
| 18 | **Audit trail** (p9) | Every API request → audit_log table | 2, 3 |
| 19 | **Rate limiting** (p9) | Redis token-bucket in API gateway | 3 |
| 20 | **Input sanitization** (p9) | XSS/injection sanitizer in shared lib + API gateway | 3, 10 |
| 21 | **Response time < 5s** (p11) | Redis caching, vLLM batching, translation cache | 3, 5, 13 |
| 22 | **99.5% uptime** (p11) | Health checks, restart policies, Prometheus alerts | 1 |
| 23 | **Multi-model AI + Semantic Router** (Design) | Routes to Llama 3.1 / Mistral NeMo / Gemma 3 based on query type | 3, 5 |
| 24 | **30-website crawling** (p6) | Scrapy + Playwright data ingestion engine | 12 |
| 25 | **Multimedia search** (Design) | SigLIP vision embeddings + media spider | 4, 12 |
| 26 | **PDF (Marker), DOCX, HTML, TXT, images** (p7) | Multi-format document support | 4, 7, 12 |
| 27 | **Drupal integration** (p5) | embed.js for chatbot + embeddable search bar | 8, 11 |
| 28 | **LLM observability** (Design) | Langfuse tracing for all LLM calls | 3, 5 |
| 29 | **Analytics dashboard** (p7) | Grafana (infra) + React admin (business) + Langfuse (LLM) | 1, 9 |
| 30 | **Model fine-tuning on domain data** (p14-15) | QLoRA fine-tuning + evaluation benchmarks | 14 |
| 31 | **Continuous learning / retraining** (p15) | Feedback-driven retraining + data drift detection | 14 |
| 32 | **API documentation (OpenAPI)** (p12) | FastAPI Swagger UI + exported openapi.yaml | 3, 16 |
| 33 | **Deployment guide** (p12) | DEPLOYMENT_GUIDE.md + PREREQUISITES.md | 16 |
| 34 | **User manual (Hindi + English)** (p12) | USER_MANUAL_EN.md + USER_MANUAL_HI.md | 16 |
| 35 | **Admin guide + Training** (p12) | ADMIN_GUIDE.md + TRAINING_PLAN.md | 16 |
| 36 | **Security audit report** (p13, p22) | Automated security scanning + report generation | 15 |
| 37 | **Test reports (UAT, perf, security)** (p12-13) | Integration, load, security, UAT test suites + reports | 15 |
| 38 | **Backup & disaster recovery** (p11) | Automated daily backups (PG, Milvus, S3, Redis) + DR plan | 1, 16 |
| 39 | **Chatbot fallback / escalation** (p7) | Graceful "contact helpline" message when confidence < threshold | 3 |
| 40 | **Session management** (p9) | 30-min timeout, context truncation, session resumption | 3 |
| 41 | **PII / Content guardrails** (Design) | PII redaction, hallucination detection, topic filter, toxicity | 5 |
| 42 | **Translation** (Design) | IndicTrans2 for all 22 scheduled languages | 13 |
| 43 | **3-year AMC support** (p16) | Documented in DEPLOYMENT_GUIDE + MONITORING_GUIDE | 16 |
| 44 | **Data retention policy** (p9) | Configurable retention per data type, auto-purge service | 3 |
| 45 | **API key management** (p9) | api_keys table, generation/rotation/expiration via admin | 2, 3 |
| 46 | **Event listings / cultural events** (p7) | events table, event_extractor in data ingestion, EventCard in search | 2, 11, 12 |
| 47 | **License / IP inventory** (p17) | SBOM generation, license audit script, LICENSE_INVENTORY.md | 15, 16 |
| 48 | **Shadow DOM for Drupal embed** (p5) | CSS isolation via Shadow DOM in chat widget | 8 |
| 49 | **Monthly performance reports** (p11) | Automated monthly-report.sh from Prometheus API | 1 |
| 50 | **GPU monitoring alerts** (p11) | NVIDIA DCGM exporter → Prometheus → Grafana alerts | 1 |
| 51 | **Container image scanning** (p22) | trivy/grype scanning in security test suite | 15 |
| 52 | **Structured data extraction** (p7) | JSON-LD, microdata extraction from web pages | 12 |
| 53 | **TLS 1.2+ enforcement** (p9) | NGINX cipher suite allowlist + HSTS | 1 |


