## Dependency Graph (Updated)

```
                    ┌─────────────────────────────────────┐
                    │  Phase 1: All start simultaneously  │
                    └────────────────┬────────────────────┘
                                     │
Stream 10 (Shared Libs) ────────────────────────────────────────────────┐
         │                                                               │
         ├──► Stream 3  (API Gateway + Semantic Router + RBAC) ◄── Stream 2 (DB + RBAC)
         │         │
         ├──► Stream 4  (RAG: LlamaIndex + Milvus + BGE-M3 + SigLIP)
         │
         ├──► Stream 5  (LLM: Llama 3.1 + Mistral NeMo + Gemma 3 + Guardrails)
         │
         ├──► Stream 6  (Speech: IndicConformer + IndicTTS)
         │
         ├──► Stream 7  (OCR: Tesseract + EasyOCR)
         │
         ├──► Stream 12 (Data Ingestion: Scrapy + Playwright + Marker)
         │         │
         │         └──► Stream 14 (Fine-Tuning: QLoRA + Eval) [after initial data scraped]
         │
         └──► Stream 13 (Translation: IndicTrans2)

Stream 1  (Infrastructure + Backup/DR) ◄── all services (Dockerfiles)
Stream 8  (Chat Widget + GIGW)         ──► calls API Gateway
Stream 9  (Admin Dashboard)            ──► calls API Gateway
Stream 11 (Search Page + GIGW)         ──► calls API Gateway
Stream 16 (Documentation)             ──► references all stream specs

                    ┌─────────────────────────────────────┐
                    │ Phase 3: After all services deployed │
                    └────────────────┬────────────────────┘
                                     │
Stream 15 (Integration + Perf + Security Testing) ◄── requires all services running
```

**Streams 1-13 + 16 can start simultaneously.** Stream 14 starts after Stream 12 scrapes initial data. Stream 15 runs last against the fully deployed system.
