### STREAM 12: Data Ingestion Engine (Scrapy + Playwright) (**NEW**)

**Agent Goal:** Build the web scraping and content ingestion pipeline that crawls the **30 ring-fenced Ministry of Culture websites** and feeds content into the RAG pipeline.

**Files to create:**
```
data-ingestion/
├── Dockerfile
├── requirements.txt
├── app/
│   ├── __init__.py
│   ├── main.py                     # FastAPI app for ingestion management
│   ├── config.py                   # Target URLs, scrape intervals, selectors
│   ├── routers/
│   │   ├── __init__.py
│   │   ├── jobs.py                 # POST /jobs/trigger, GET /jobs/status
│   │   ├── targets.py              # CRUD scrape targets (the 30 websites)
│   │   └── health.py               # GET /health
│   ├── scrapers/
│   │   ├── __init__.py
│   │   ├── base_spider.py          # Base Scrapy spider with common settings
│   │   ├── static_spider.py        # Scrapy spider for static HTML sites
│   │   ├── dynamic_spider.py       # Playwright-based spider for JavaScript SPAs
│   │   ├── pdf_spider.py           # Spider that discovers + downloads PDFs
│   │   └── media_spider.py         # Extract images, videos, multimedia metadata
│   ├── parsers/
│   │   ├── __init__.py
│   │   ├── html_parser.py          # Extract clean text from HTML (trafilatura/readability)
│   │   ├── marker_pdf_parser.py    # Marker for high-quality PDF→text conversion
│   │   ├── metadata_extractor.py   # Extract title, date, author, language, tags
│   │   ├── event_extractor.py      # Extract cultural events (dates, venues, descriptions) from pages
│   │   ├── structured_data.py      # Extract JSON-LD, microdata, schema.org from web pages
│   │   └── media_metadata.py       # Extract image alt-text, video titles, durations
│   ├── pipeline/
│   │   ├── __init__.py
│   │   ├── dedup.py                # Content deduplication (MinHash / SimHash)
│   │   ├── language_classifier.py  # Detect document language
│   │   ├── chunker.py              # Chunk content and send to RAG service for embedding
│   │   ├── minio_uploader.py       # Store raw documents in S3 object storage
│   │   └── db_writer.py            # Write document metadata to PostgreSQL
│   ├── schedules/
│   │   ├── __init__.py
│   │   └── cron_scheduler.py       # APScheduler for periodic re-scraping
│   ├── targets/
│   │   └── ministry_sites.json     # 30 ring-fenced website definitions with selectors
│   └── utils/
│       ├── __init__.py
│       ├── robots_checker.py       # Respect robots.txt
│       └── metrics.py
└── tests/
    ├── test_static_spider.py
    ├── test_html_parser.py
    └── test_dedup.py
```

**30 ring-fenced websites include:** culture.gov.in and subordinate organizations (ASI, National Museum, Sahitya Akademi, Sangeet Natak Akademi, IGNCA, National Archives, Anthropological Survey, libraries, zonal cultural centres, etc.)

**Key technical decisions (from Design):**
- **Scrapy** for static HTML crawling (most government sites)
- **Playwright** for JavaScript-rendered SPAs (dynamic content)
- **Marker** for PDF→text conversion (higher quality than Tesseract for digital PDFs)
- **trafilatura** for clean text extraction from HTML
- **S3** for raw document storage (source of truth)
- **Deduplication** via MinHash to avoid re-indexing unchanged content
- **Scheduled re-scraping** via APScheduler (configurable per-site intervals)

**No code dependencies on other streams** — calls RAG service `/ingest` endpoint to feed documents.

**Shared Contracts Reference (from `01_Shared_Contracts.md`):**
- §1 Service Registry: this service runs on port 8006 as `data-ingestion`
- §3 Environment Variables: read `INGESTION_*`, `AWS_S3_*`, `POSTGRES_*`, `RAG_SERVICE_URL` variables
- §4 Error Response Format: use standard error format from §4
- §5 Health Check Format: `/health` must check S3 and PostgreSQL connectivity
- §8.1 Ingest API: call RAG service `/ingest` with exact schema from §8.1 (POST to rag-service:8001/ingest)
- §8.6 Jobs API: implement exact `/jobs/trigger` and `/jobs/status` schemas from §8.6
- §9 Language Codes: classify documents using codes from §9
- §16 S3 Buckets: store raw docs at `documents/raw/{source_site}/{document_id}.{ext}`, processed at `documents/processed/`

---


---

## Agent Prompt

### Agent 12: Data Ingestion Engine (**NEW**)
```
PREREQUISITE: Read 00_Overview.md and 01_Shared_Contracts.md first.
Port 8006. Call rag-service:8001/ingest per §8.1. Use S3 paths from §16.
Use jobs API schema from §8.6, env vars from §3.
Build a FastAPI-based web scraping and content ingestion service with:
- Scrapy spiders for static HTML crawling (government websites)
- Playwright-based spider for JavaScript SPA extraction
- PDF discovery + download spider
- Media spider (images, videos, metadata extraction)
- Event extraction spider: parse cultural event listings (dates, venues,
  descriptions) from Ministry pages → store in events table
- Structured data extraction: JSON-LD, microdata, schema.org from web pages
- HTML parsing via trafilatura for clean text extraction
- Marker for high-quality PDF→text conversion
- Content deduplication (MinHash/SimHash)
- Language classification per document
- S3 upload for raw document storage
- PostgreSQL metadata writes (scrape_jobs, documents tables)
- Calls RAG service /ingest to embed and index content
- APScheduler for periodic re-scraping (configurable per site)
- targets/ministry_sites.json with 30 ring-fenced website definitions.
  Known sites from RFP (populate immediately; remaining from Annexure
  to be added by Ministry contact arit-culture@gov.in):
  1. culture.gov.in (Primary Ministry site)
  2. indianculture.gov.in (Indian Culture Portal)
  3. mgmd.gov.in (Manuscripts & Graphics)
  4. vedicheritage.gov.in (Vedic Heritage)
  5. museumsofindia.gov.in (Museums of India)
  6. gyanbharatam.com (Knowledge Platform)
  7. abhilekh-patal.in (Archival System)
  8. asi.nic.in (Archaeological Survey of India)
  9. nationalmuseumindia.gov.in
  10. sangeetnatak.gov.in (Sangeet Natak Akademi)
  11. sahitya-akademi.gov.in
  12. ignca.gov.in (IGNCA)
  13. nationalarchives.nic.in
  14. ngmaindia.gov.in (National Gallery of Modern Art)
  15. nmml.nic.in (Nehru Memorial Museum)
  16. indiaculture.gov.in
  17. ccimindia.org
  18-30. Remaining sites from RFP Annexure (TBD from Ministry)
```

