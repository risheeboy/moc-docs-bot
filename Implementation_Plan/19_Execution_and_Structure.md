## Recommended Execution Order

1. **Phase 1 — Kick off all 16 agents simultaneously** — Streams 1-13 + 16 are designed to be independent
2. **Stream 10 (Shared Libs) completes first** (~15 min)
3. **Streams 1, 2, 8, 9, 11, 16** complete next (~30-45 min each)
4. **Streams 3-7, 12, 13** complete (~45-60 min each)
5. **Stream 14 (Fine-tuning)** can start once Stream 12 has scraped initial data
6. **Phase 2 — Integration:** Wire docker-compose.yml, run `docker-compose up`, verify inter-service communication
7. **Phase 3 — Stream 15 (Testing):** Runs against fully deployed system — integration, performance, security, UAT
8. **Phase 4 — E2E validation:** Trigger scrape of culture.gov.in → ingest → search in Hindi → get AI summary → ask chatbot follow-up → hear voice response → submit feedback → verify sentiment → check admin dashboard

---

## File/Folder Structure (Final)

```
rag-qa-hindi/
├── docker-compose.yml
├── docker-compose.override.yml
├── .env.example
├── .env
├── infrastructure/
│   ├── nginx/
│   ├── scripts/                       # init, start, stop, health-check, backup, restore
│   └── monitoring/                    # prometheus, grafana, loki configs
├── database/
│   ├── migrations/                    # SQL migrations (incl. RBAC tables)
│   └── seed/                          # Seed data (users, config, 30 scrape targets)
├── shared/
│   └── src/rag_shared/                # Shared Python package
├── api-gateway/
│   └── app/                           # FastAPI + Semantic Router + RBAC + Fallback
├── rag-service/
│   └── app/                           # LlamaIndex + Milvus + BGE-M3 + SigLIP
├── llm-service/
│   └── app/                           # vLLM multi-model + Guardrails + A/B testing
├── speech-service/
│   └── app/                           # IndicConformer STT + IndicTTS
├── translation-service/
│   └── app/                           # IndicTrans2 + translation cache
├── ocr-service/
│   └── app/                           # Tesseract + EasyOCR + Hindi preprocessing
├── data-ingestion/
│   └── app/                           # Scrapy + Playwright + Marker + 30 site configs
├── model-training/                    # NEW: Fine-tuning + evaluation + continuous learning
│   ├── app/
│   ├── data/
│   └── scripts/
├── frontend/
│   ├── chat-widget/                   # Conversational Chatbot (+ GIGW compliance)
│   ├── search-page/                   # Unified Semantic Search (+ GIGW compliance)
│   └── admin-dashboard/               # Admin SPA
├── testing/                           # NEW: Integration + Performance + Security + UAT
│   ├── integration/
│   ├── performance/
│   ├── security/
│   ├── uat/
│   └── reports/
├── docs/                              # NEW: All RFP-required documentation
│   ├── api/                           # OpenAPI spec + API reference
│   ├── deployment/                    # Deployment guide, prerequisites, backup/DR
│   ├── user/                          # User manuals (English + Hindi)
│   ├── admin/                         # Admin guide, scraping guide, security guide
│   ├── training/                      # Training materials for Ministry staff
│   ├── architecture/                  # System architecture, data flow, security docs
│   ├── compliance/                    # GIGW, WCAG, data sovereignty, license inventory
│   └── hindi/                         # Hindi translations of key documentation
└── Requirements/                      # Extracted requirements from RFP (reference only)
    ├── 01_Scope_of_Work.md
    ├── 02_Technical_Requirements.md
    ├── 03_Infrastructure.md
    ├── 04_SLAs_and_Performance.md
    ├── 05_Deliverables.md
    ├── 06_Model_Training.md
    ├── 07_Completion_Schedule.md
    ├── 08_Security_and_Compliance.md
    ├── 09_General_Terms.md
    └── 10_Financial_Bid_Structure.md
```
    ├── api/                         