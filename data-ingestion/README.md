# Data Ingestion Engine (Stream 12)

Web scraping and content ingestion pipeline for the RAG-based Hindi QA system.

## Overview

The Data Ingestion Engine crawls the 30 ring-fenced Ministry of Culture websites, extracts and parses content, and feeds it into the RAG service for embedding and indexing.

## Features

- **Multi-spider Architecture**: Static (Scrapy), Dynamic (Playwright), PDF, and Media spiders
- **Content Parsing**: HTML extraction via trafilatura, PDF parsing via Marker
- **Smart Deduplication**: MinHash/SimHash for duplicate detection
- **Language Detection**: Automatic language classification
- **Event Extraction**: Extracts cultural events from pages
- **Metadata Extraction**: Titles, authors, dates, tags
- **MinIO Integration**: Raw document storage per §16
- **PostgreSQL Integration**: Document metadata tracking
- **RAG Integration**: Direct /ingest calls to RAG service per §8.1
- **Scheduled Scraping**: APScheduler for periodic re-scraping
- **Robots.txt Compliance**: Respects crawl directives

## Architecture

```
┌─────────────────────────────────────────────┐
│      API Gateway (Port 8006)                │
├─────────────────────────────────────────────┤
│ POST /jobs/trigger - Start scraping job    │
│ GET /jobs/status - Query job status         │
│ POST /targets - Create/manage targets       │
│ GET /health - Health check                  │
└───┬───────────────────────────────────────┬─┘
    │                                         │
    │      Scrapers                    Pipeline
    │  ┌──────────────────┐       ┌──────────────────┐
    ├─→│ StaticSpider     │       │ Deduplicator     │
    │  │ DynamicSpider    │──────→│ LanguageDetect   │
    │  │ PdfSpider        │       │ Chunker          │
    │  │ MediaSpider      │       │ MinIOUploader    │
    │  └──────────────────┘       │ DbWriter         │
    │                             └────────┬─────────┘
    │                                      │
    └──────────────────────────┬───────────┘
                               │
                ┌──────────────┴──────────────┐
                │                             │
            MinIO                        PostgreSQL
         (documents/)                 (documents,
                                      events,
                                    scrape_jobs)
                │
                └──→ RAG Service /ingest
```

## Quick Start

### Build

```bash
docker build -t data-ingestion:latest .
```

### Run

```bash
# With docker-compose
docker-compose up data-ingestion

# Standalone
docker run -it --rm \
  -e INGESTION_SCRAPE_INTERVAL_HOURS=24 \
  -e RAG_SERVICE_URL=http://rag-service:8001 \
  -e MINIO_ENDPOINT=minio:9000 \
  -e POSTGRES_HOST=postgres \
  data-ingestion:latest
```

### Health Check

```bash
curl http://localhost:8006/health
```

## API Endpoints

### Trigger Scraping Job

```bash
POST /jobs/trigger
Content-Type: application/json

{
  "target_urls": ["https://culture.gov.in"],
  "spider_type": "auto",
  "force_rescrape": false
}
```

Response:
```json
{
  "job_id": "uuid",
  "status": "started",
  "target_count": 1,
  "started_at": "2026-02-24T10:30:00Z"
}
```

### Query Job Status

```bash
GET /jobs/status?job_id=uuid
```

Response:
```json
{
  "job_id": "uuid",
  "status": "running",
  "progress": {
    "pages_crawled": 45,
    "pages_total": 120,
    "documents_ingested": 30,
    "errors": 2
  },
  "started_at": "2026-02-24T10:30:00Z",
  "elapsed_seconds": 180
}
```

### Manage Targets

```bash
# List all targets
GET /targets

# Get specific target
GET /targets/{target_id}

# Create target
POST /targets
Content-Type: application/json

{
  "name": "Example Site",
  "base_url": "https://example.gov.in",
  "spider_type": "static",
  "scrape_interval_hours": 24
}

# Update target
PUT /targets/{target_id}

# Delete target
DELETE /targets/{target_id}
```

## Configuration

### Environment Variables

```bash
# Ingestion settings
INGESTION_SCRAPE_INTERVAL_HOURS=24
INGESTION_MAX_CONCURRENT_SPIDERS=4
INGESTION_RESPECT_ROBOTS_TXT=true

# MinIO settings
MINIO_ENDPOINT=minio:9000
MINIO_ACCESS_KEY=minioadmin
MINIO_SECRET_KEY=minioadmin
MINIO_BUCKET_DOCUMENTS=documents

# PostgreSQL settings
POSTGRES_HOST=postgres
POSTGRES_DB=ragqa
POSTGRES_USER=ragqa_user
POSTGRES_PASSWORD=changeme

# RAG Service settings
RAG_SERVICE_URL=http://rag-service:8001
```

## 30 Ring-Fenced Websites

The service targets 30 Ministry of Culture websites:

1. culture.gov.in - Ministry main site
2. indianculture.gov.in - Indian Culture Portal
3. mgmd.gov.in - Manuscripts & Graphics
4. vedicheritage.gov.in - Vedic Heritage
5. museumsofindia.gov.in - Museums of India
6. gyanbharatam.com - Knowledge Platform
7. abhilekh-patal.in - Archival System
8. asi.nic.in - Archaeological Survey
9. nationalmuseumindia.gov.in - National Museum
10. sangeetnatak.gov.in - Sangeet Natak Akademi
... (30 total, see targets/ministry_sites.json)

## Spider Types

### Static Spider
Uses Scrapy for HTML-based government websites. Efficient for traditional site structures.

### Dynamic Spider
Uses Playwright for JavaScript SPAs. Handles client-side rendering.

### PDF Spider
Discovers and downloads PDFs from sites. Parses with Marker for quality extraction.

### Media Spider
Extracts images, videos, and multimedia metadata from pages.

## Content Pipeline

1. **Scraper** → Crawls websites, discovers content
2. **Parser** → Extracts clean text, metadata, structured data
3. **Deduplicator** → Detects duplicate/near-duplicate content
4. **Language Classifier** → Detects document language
5. **Chunker** → Splits content into RAG-compatible chunks
6. **MinIO Upload** → Stores raw documents
7. **RAG Ingest** → Calls RAG /ingest endpoint
8. **DB Write** → Records metadata in PostgreSQL

## Testing

```bash
# Run unit tests
pytest tests/

# Run with coverage
pytest --cov=app tests/

# Run specific test
pytest tests/test_static_spider.py -v
```

## Monitoring

### Prometheus Metrics

Access metrics at `GET /metrics`

Key metrics:
- `ingestion_pages_crawled_total` - Total pages crawled
- `ingestion_documents_ingested_total` - Documents sent to RAG
- `ingestion_errors_total` - Ingestion errors
- `ingestion_job_duration_seconds` - Job execution time

### Health Endpoint

```bash
curl http://localhost:8006/health
```

Returns health status of:
- MinIO connectivity
- PostgreSQL connectivity
- Redis connectivity
- RAG Service connectivity

## Shared Contracts

Per Shared Contracts (01_Shared_Contracts.md):

- **§1**: Service runs on port 8006 as `data-ingestion`
- **§3**: Reads `INGESTION_*`, `MINIO_*`, `POSTGRES_*`, `RAG_SERVICE_URL` env vars
- **§4**: Standard error response format
- **§5**: Standard health check format
- **§8.1**: RAG /ingest schema (document chunking and embedding)
- **§8.6**: Job trigger/status API schemas
- **§9**: Language codes (ISO 639-1)
- **§11**: Prometheus metrics
- **§16**: MinIO bucket structure

## Production Deployment

### Database Schema

Create tables in PostgreSQL:

```sql
-- Documents table
CREATE TABLE documents (
  document_id UUID PRIMARY KEY,
  title VARCHAR(500),
  url TEXT,
  source_site VARCHAR(255),
  content_type VARCHAR(50),
  language VARCHAR(10),
  raw_document_path VARCHAR(255),
  processed_text_path VARCHAR(255),
  created_at TIMESTAMP,
  updated_at TIMESTAMP
);

-- Events table
CREATE TABLE events (
  event_id UUID PRIMARY KEY,
  title VARCHAR(500),
  date DATE,
  venue VARCHAR(255),
  description TEXT,
  source_url TEXT,
  created_at TIMESTAMP
);

-- Scrape jobs table
CREATE TABLE scrape_jobs (
  job_id UUID PRIMARY KEY,
  target_url TEXT,
  spider_type VARCHAR(50),
  status VARCHAR(50),
  pages_crawled INT,
  documents_found INT,
  errors INT,
  started_at TIMESTAMP,
  completed_at TIMESTAMP
);
```

### Scaling

- Increase `INGESTION_MAX_CONCURRENT_SPIDERS` for parallelism
- Use separate worker processes for long-running jobs
- Cache robots.txt per domain
- Monitor memory for MinHash operations on large corpora

## Troubleshooting

### No documents ingested

1. Check spider is allowed by robots.txt
2. Verify content selectors in targets
3. Check RAG service /ingest endpoint is responding
4. Review ingestion logs for parser errors

### High CPU usage

- Reduce concurrent spiders
- Disable MinHash deduplication for initial pass
- Profile PDF parsing for slow PDFs

### MinIO errors

- Verify bucket exists and is accessible
- Check MINIO_ACCESS_KEY and MINIO_SECRET_KEY
- Ensure MinIO endpoint is reachable

## License

Ministry of Culture, Government of India
