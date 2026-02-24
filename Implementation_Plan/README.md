# Implementation Plan — File Index

The implementation plan has been split into individual files so that each sub-agent only needs to read the files relevant to its task.

## How to Use

1. **Every agent MUST read first:**
   - `00_Overview.md` — architecture, tech stack, interfaces
   - `01_Shared_Contracts.md` — **MANDATORY** service ports, env vars, API schemas, error formats, health checks, log format, language codes, dependency versions
2. **Each stream agent** reads its own `Stream_XX_*.md` file (contains both the stream spec AND the agent prompt)
3. **For cross-stream context**, see `17_Dependency_Graph.md`
4. **For requirements traceability**, see `18_NFR_Checklist.md`
5. **For final structure**, see `19_Execution_and_Structure.md`

> **CRITICAL:** All agents must follow the shared contracts exactly. Do not invent your own port numbers, env var names, error formats, or API schemas. The contracts in `01_Shared_Contracts.md` are the single source of truth for inter-service communication.

## Files

| File | Description | Lines |
|---|---|---|
| [00_Overview.md](00_Overview.md) | Project overview, architecture, tech stack | 115 |
| [01_Shared_Contracts.md](01_Shared_Contracts.md) | **MANDATORY** Service registry, env vars, API contracts, error/health/log formats | ~550 |
| [Stream_01_Infrastructure.md](Stream_01_Infrastructure.md) | Docker Compose, NGINX, monitoring, backups + Agent prompt | 105 |
| [Stream_02_Database.md](Stream_02_Database.md) | PostgreSQL schema, migrations, RBAC + Agent prompt | 87 |
| [Stream_03_API_Gateway.md](Stream_03_API_Gateway.md) | FastAPI, semantic routing, auth, RBAC + Agent prompt | 161 |
| [Stream_04_RAG_Pipeline.md](Stream_04_RAG_Pipeline.md) | LlamaIndex, Milvus, BGE-M3 embeddings + Agent prompt | 90 |
| [Stream_05_LLM_Service.md](Stream_05_LLM_Service.md) | vLLM multi-model (Llama, Mistral, Gemma) + Agent prompt | 82 |
| [Stream_06_Speech.md](Stream_06_Speech.md) | IndicConformer STT, IndicTTS + Agent prompt | 67 |
| [Stream_07_OCR.md](Stream_07_OCR.md) | Tesseract, EasyOCR, preprocessing + Agent prompt | 56 |
| [Stream_08_Chat_Widget.md](Stream_08_Chat_Widget.md) | React chat widget, voice, GIGW + Agent prompt | 103 |
| [Stream_09_Admin_Dashboard.md](Stream_09_Admin_Dashboard.md) | React admin dashboard, analytics + Agent prompt | 68 |
| [Stream_10_Shared_Libs.md](Stream_10_Shared_Libs.md) | Shared Python package, utilities + Agent prompt | 67 |
| [Stream_11_Search_Page.md](Stream_11_Search_Page.md) | React semantic search page, GIGW + Agent prompt | 105 |
| [Stream_12_Data_Ingestion.md](Stream_12_Data_Ingestion.md) | Scrapy, Playwright, 30 websites + Agent prompt | 116 |
| [Stream_13_Translation.md](Stream_13_Translation.md) | IndicTrans2 translation service + Agent prompt | 63 |
| [Stream_14_Model_Training.md](Stream_14_Model_Training.md) | Fine-tuning, evaluation, continuous learning + Agent prompt | 84 |
| [Stream_15_Testing.md](Stream_15_Testing.md) | Integration, performance, security testing + Agent prompt | 95 |
| [Stream_16_Documentation.md](Stream_16_Documentation.md) | API docs, deployment guides, training + Agent prompt | 89 |
| [17_Dependency_Graph.md](17_Dependency_Graph.md) | Cross-stream dependencies and sequencing | 39 |
| [18_NFR_Checklist.md](18_NFR_Checklist.md) | Non-functional requirements checklist (53 items) | 59 |
| [19_Execution_and_Structure.md](19_Execution_and_Structure.md) | Execution order and final folder structure | 79 |
