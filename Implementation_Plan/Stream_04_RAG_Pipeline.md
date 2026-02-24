### STREAM 4: RAG Pipeline Service (LlamaIndex + Milvus + BGE-M3)

**Agent Goal:** Build the document ingestion, chunking, embedding, vector storage, and retrieval pipeline using **LlamaIndex**, **Milvus**, and **BGE-M3** embeddings.

**Files to create:**
```
rag-service/
├── Dockerfile
├── requirements.txt
├── app/
│   ├── __init__.py
│   ├── main.py                     # FastAPI app for RAG service
│   ├── config.py                   # Model names, chunk sizes, thresholds
│   ├── routers/
│   │   ├── __init__.py
│   │   ├── ingest.py               # POST /ingest (document → chunks → embeddings → Milvus)
│   │   ├── query.py                # POST /query (question → retrieve → context for chatbot)
│   │   ├── search.py               # POST /search (semantic search → ranked results for search page)
│   │   └── health.py               # GET /health
│   ├── services/
│   │   ├── __init__.py
│   │   ├── document_loader.py      # Load PDF (via Marker), DOCX, HTML, TXT
│   │   ├── marker_pdf_parser.py    # Marker integration for high-quality PDF→text
│   │   ├── text_splitter.py        # Hindi-aware chunking (sentence boundaries)
│   │   ├── embeddings.py           # BGE-M3 embedding model (dense + sparse + ColBERT)
│   │   ├── vision_embeddings.py    # SigLIP for image embeddings (multimodal search)
│   │   ├── vector_store.py         # Milvus client (upsert, hybrid search, delete)
│   │   ├── retriever.py            # Hybrid retrieval (BGE-M3 dense + sparse) via LlamaIndex
│   │   ├── reranker.py             # Cross-encoder reranking for top-K
│   │   ├── context_builder.py      # Assemble context with source citations
│   │   ├── cache_service.py        # Redis query result caching (hash query+filters → cached top-K)
│   │   └── summarizer.py           # Summarize long documents before ingestion
│   ├── llamaindex_config/
│   │   ├── __init__.py
│   │   ├── index_builder.py        # LlamaIndex VectorStoreIndex with Milvus
│   │   ├── query_engine.py         # LlamaIndex query engine with custom retrievers
│   │   └── node_parser.py          # Custom Hindi-aware node parser
│   ├── models/
│   │   ├── __init__.py
│   │   ├── ingest.py               # IngestRequest, IngestResponse
│   │   └── query.py                # QueryRequest, QueryResponse, RetrievedChunk, Source
│   └── utils/
│       ├── __init__.py
│       ├── hindi_tokenizer.py      # Hindi-specific text processing
│       └── metrics.py              # Prometheus metrics
└── tests/
    ├── conftest.py
    ├── test_ingest.py
    ├── test_query.py
    ├── test_search.py
    └── test_hindi_chunking.py
```

**Key technical decisions (from Design):**
- **Embedding model:** `BAAI/bge-m3` — provides dense, sparse (lexical), AND ColBERT representations in a single model, enabling native hybrid search
- **Vision embeddings:** `SigLIP` — for indexing images extracted from documents/websites to support multimodal search results
- **Vector DB:** **Milvus** (standalone mode with etcd + MinIO) — supports hybrid search natively
- **RAG framework:** **LlamaIndex** — VectorStoreIndex backed by Milvus, with custom Hindi-aware node parsers
- **PDF parsing:** **Marker** — high-quality PDF-to-markdown conversion preserving structure, tables, formulas
- **Chunk size:** 512 tokens with 64-token overlap; Hindi-aware sentence boundary detection
- **Retrieval strategy:** BGE-M3 hybrid (dense + sparse) with reciprocal rank fusion, followed by cross-encoder reranking

**Communicates with:** Milvus (via pymilvus), MinIO (for stored documents). Called by API Gateway via HTTP.

**Shared Contracts Reference (from `01_Shared_Contracts.md`):**
- §1 Service Registry: this service runs on port 8001 as `rag-service`
- §3 Environment Variables: read `RAG_*`, `MILVUS_*`, `REDIS_*`, `MINIO_*` variables
- §4 Error Response Format: use standard error format from §4
- §5 Health Check Format: `/health` must check Milvus and Redis connectivity, return format from §5
- §6 Log Format: use structured JSON logging via `rag_shared.middleware.logging`
- §7 Request ID: accept and propagate `X-Request-ID` header
- §8.1 API Contracts: implement exact request/response schemas for `/query`, `/search`, `/ingest` from §8.1
- §9 Language Codes: use standard language codes
- §11 Prometheus Metrics: expose `rag_retrieval_duration_seconds`, `rag_cache_hit_total`, `rag_cache_miss_total`
- §16 MinIO Buckets: store documents in `documents/raw/`, `documents/processed/`, `documents/images/` paths

---

## Agent Prompt

### Agent 4: RAG Pipeline (LlamaIndex + Milvus + BGE-M3)
```
PREREQUISITE: Read 00_Overview.md and 01_Shared_Contracts.md first.
Port 8001. Use exact API schemas from §8.1, env vars from §3, MinIO paths from §16.

Build a FastAPI RAG service using LlamaIndex framework with:
- Document ingestion: PDF (via Marker), DOCX, HTML, TXT
- Hindi-aware text chunking with sentence boundary detection
- BGE-M3 embeddings (dense + sparse + ColBERT in single model)
- SigLIP vision embeddings for image indexing (multimodal search)
- Milvus vector store (hybrid search: dense + sparse)
- Cross-encoder reranking for top-K results
- Context builder that assembles source citations
- Redis query result caching: hash query+filters → cache top-K results
  with TTL (configurable, default 1hr). cache_service.py wraps Redis
  get/set with automatic serialization. Invalidate on re-index.
- Two retrieval modes:
  (a) /query — for chatbot (returns context for LLM generation)
  (b) /search — for search page (returns ranked results with snippets,
      multimedia, events, source metadata)
```

