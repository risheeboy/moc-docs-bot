# Data Ingestion Service

FastAPI on port 8006. Web scraping and document ingestion pipeline for 30 Ministry websites.

## Key Files

- `app/main.py` — FastAPI application
- `app/spiders/` — Scrapy spider definitions
- `app/services/scraper.py` — Scrapy + Playwright orchestration
- `app/services/cleaner.py` — HTML/text cleaning and normalization
- `app/services/deduplicator.py` — Content deduplication (stateless)
- `app/services/event_extractor.py` — Cultural event parsing
- `app/services/pdf_processor.py` — PDF to Markdown (Marker library)
- `app/config.py` — Configuration

## Endpoints

- `POST /ingest/websites` — Start scraping seeded websites
- `POST /ingest/pdf` — Process uploaded PDF
- `GET /ingest/status/{job_id}` — Scrape job status
- `POST /ingest/event/extract` — Extract events from HTML
- `GET /health` — Health check

## Pipeline

1. Spider (Scrapy + Playwright for JS rendering)
2. Clean (boilerplate removal, text normalization)
3. Deduplicate (content hash comparison)
4. PDF process (Marker library → Markdown)
5. Upload (batch S3 push)
6. Index (trigger RAG service webhook)

## Data Source

30 Ministry of Culture websites (seeded in database), e.g., cultura.gov.in subdomains, cultural heritage sites.

## Event Extraction

Parses: event name, date, location, category (music, dance, exhibition), duration, organizer, contact, registration link.

## Dependencies

- Scrapy (web scraping)
- Playwright (JavaScript rendering)
- Marker library (PDF → Markdown)
- BeautifulSoup4 (HTML parsing)
- boto3 (S3 upload)

## Known Issues

1. **S3 filename mismatch** — `minio_uploader.py` contains boto3 code.
2. **Deduplicator stateless** — Loses state on restart. Add PostgreSQL backing.
3. **CORS misconfiguration** — Uses `allow_origins=["*"]`. Fix: restrict to ALB.
4. **No failure backoff** — Failed documents not retried.
