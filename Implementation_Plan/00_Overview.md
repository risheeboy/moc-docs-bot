# Implementation Plan — Overview

This directory contains the implementation plan split into individual files.
See [README.md](README.md) for the file index.

---

# RAG-Based Hindi QA System — Implementation Plan

## Project Overview

An AI-powered multilingual chatbot and RAG-based Q&A system for the Ministry of Culture (Government of India) website. The system provides **two user-facing interfaces** — a Conversational Chatbot and a Unified Semantic Search page — plus voice interaction, document OCR, content summarization, sentiment analysis, translation, and analytics. All services are deployed as Docker containers on a single GPU-equipped Linux machine.

---

## Two User-Facing Interfaces

| Interface | Description | Deployment |
|---|---|---|
| **Conversational Chatbot** | Floating chat widget embedded on culture.gov.in via `<script>` tag. Multi-turn dialogue, voice input/output, source citations, feedback. | Embeddable widget (Stream 8) |
| **Unified Semantic Search** | Full-page search interface with search bar, AI-generated result summaries, multimedia results (images/videos from source sites), event listings, language toggle, and faceted filtering across all 30 ring-fenced Ministry platforms. | Standalone SPA page (Stream 11) |

Both interfaces share the same API Gateway and backend services, but they call different endpoints and render results differently.

---

## Architecture Summary (from Design Document)

```
┌─────────────────────────────────────────────────────────────────────────┐
│                          NGINX Reverse Proxy                            │
│                       (SSL termination, routing)                        │
└───┬──────────────┬────────────────┬──────────────────┬──────────────────┘
    │              │                │                  │
┌───▼────┐  ┌──────▼───────┐ ┌─────▼──────┐   ┌──────▼──────┐
│ Search │  │ Chat Widget  │ │   Admin    │   │  Grafana    │
│  Page  │  │  (embedded)  │ │ Dashboard  │   │  Dashboards │
│ (SPA)  │  │    (SPA)     │ │   (SPA)    │   │             │
└───┬────┘  └──────┬───────┘ └─────┬──────┘   └─────────────┘
    │              │                │
    └──────┬───────┴────────────────┘
           │
    ┌──────▼──────────────┐
    │    API Gateway      │
    │    (FastAPI)        │
    │  Auth / Rate Limit  │
    │  Semantic Router    │◄─── Routes queries to specialized models
    └──┬──┬──┬──┬──┬──┬──┘
       │  │  │  │  │  │
  ┌────┘  │  │  │  │  └─────────────────┐
  │    ┌──┘  │  │  └──────┐             │
  ▼    ▼     ▼  ▼         ▼             ▼
┌────┐┌────┐┌──────┐┌─────────┐┌──────┐┌──────────┐
│RAG ││LLM ││Speech││Translat-││ OCR  ││Data      │
│Svc ││Svc ││ Svc  ││ion Svc  ││ Svc  ││Ingestion │
│    ││    ││      ││(Indic-  ││      ││Engine    │
│    ││    ││      ││Trans2)  ││      ││(Scrapy+  │
│    ││    ││      ││         ││      ││Playwright│
└─┬──┘└─┬──┘└──┬───┘└────┬────┘└──┬───┘└────┬─────┘
  │     │      │         │       │          │
  ▼     ▼      ▼         ▼       ▼          ▼
┌─────┐┌────────────────────┐┌──────┐┌──────┐┌──────┐
│Milvus││  GPU (CUDA)        ││Tessr-││MinIO ││Redis │
│VecDB ││  • Llama 3.1 8B   ││act + ││Object││Cache │
│      ││  • Mistral NeMo12B ││Hindi ││Store ││      │
│      ││  • Gemma 3 (multi) ││      ││      ││      │
│      ││  • IndicConformer  ││      ││      ││      │
└──────┘└────────────────────┘└──────┘└──────┘└──────┘
              │
       ┌──────▼──────┐    ┌───────────┐
       │ PostgreSQL  │    │ Langfuse  │ (LLM observability)
       │ (metadata,  │    └───────────┘
       │  sessions,  │    ┌───────────┐
       │  audit log) │    │Prometheus │──▶ Grafana
       └─────────────┘    └───────────┘
```

---

## Technology Stack (aligned with Design Document)

| Component | Technology | Docker Image Source |
|---|---|---|
| Reverse Proxy | NGINX | `nginx:1.25-alpine` |
| API Gateway | FastAPI + Uvicorn + Semantic Router | Custom (`python:3.11-slim`) |
| RAG Pipeline | **LlamaIndex** + sentence-transformers | Custom (`python:3.11-slim`) |
| Text Embeddings | **BAAI/bge-m3** (multilingual dense+sparse) | Loaded in RAG service |
| Vision Embeddings | **SigLIP** (for image/multimodal search) | Loaded in RAG service |
| LLM Service (standard) | **Llama 3.1 8B Instruct** via vLLM | `vllm/vllm-openai:latest` |
| LLM Service (long-ctx) | **Mistral NeMo 12B** via vLLM | `vllm/vllm-openai:latest` |
| LLM Service (multimodal)| **Gemma 3** via vLLM | `vllm/vllm-openai:latest` |
| Semantic Router | Routes queries to appropriate model | In API Gateway |
| Vector DB | **Milvus** | `milvusdb/milvus:latest` |
| Relational DB | PostgreSQL 16 | `postgres:16-alpine` |
| Object Storage | **MinIO** | `minio/minio:latest` |
| Cache | Redis 7 | `redis:7-alpine` |
| Speech-to-Text | **AI4Bharat IndicConformer** | Custom (`python:3.11-slim` + CUDA) |
| Text-to-Speech | AI4Bharat IndicTTS / Coqui TTS | Custom (`python:3.11-slim`) |
| Translation | **IndicTrans2** (ai4bharat) | Custom (`python:3.11-slim` + CUDA) |
| OCR Service | Tesseract + EasyOCR (Hindi) | Custom (`python:3.11-slim`) |
| PDF Parsing | **Marker** (high-quality PDF→text) | In Data Ingestion / RAG service |
| Web Scraping | **Scrapy + Playwright** | Custom (`python:3.11-slim`) |
| Frontend: Chat Widget | React 18 + TypeScript | Built via `node:20-alpine`, served by NGINX |
| Frontend: Search Page | React 18 + TypeScript | Built via `node:20-alpine`, served by NGINX |
| Frontend: Admin Dashboard | React 18 + TypeScript | Built via `node:20-alpine`, served by NGINX |
| Monitoring | Prometheus | `prom/prometheus:latest` |
| Dashboards | Grafana | `grafana/grafana:latest` |
| LLM Observability | **Langfuse** | `langfuse/langfuse:latest` |
| Log Aggregation | Loki + Promtail | `grafana/loki:latest` |

---

## Parallel Task Streams

The implementation is organized into **16 streams** that can be developed in parallel by sub-agents. Dependencies between streams are minimal and documented.
