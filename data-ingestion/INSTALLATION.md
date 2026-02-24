# Installation and Deployment Guide

## Prerequisites

- Docker 20.10+
- Docker Compose 2.0+
- Python 3.11+ (for local development)
- 4GB RAM minimum (8GB+ recommended)
- 10GB disk space minimum

## Quick Start

### With Docker Compose

1. Clone the repository and navigate to data-ingestion directory:
```bash
cd data-ingestion
```

2. Build the Docker image:
```bash
docker build -t data-ingestion:latest .
```

3. Create .env file with configuration:
```bash
cp .env.example .env  # or create manually
```

4. Run with docker-compose (from parent directory):
```bash
docker-compose up -d data-ingestion
```

5. Verify health:
```bash
curl http://localhost:8006/health
```

### Local Development

1. Create virtual environment:
```bash
python3.11 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Setup Playwright browsers:
```bash
python -m playwright install chromium
```

4. Configure environment:
```bash
cp .env.example .env
# Edit .env with local service endpoints
```

5. Run development server:
```bash
python -m uvicorn app.main:app --reload --port 8006
```

Access at http://localhost:8006

## Environment Configuration

Create `.env` file with these variables:

### Application Settings
```
APP_ENV=production          # production | staging | development
APP_DEBUG=false
APP_LOG_LEVEL=INFO          # DEBUG | INFO | WARNING | ERROR
APP_SECRET_KEY=<random-256-bit-hex>
```

### Ingestion Service
```
INGESTION_SCRAPE_INTERVAL_HOURS=24
INGESTION_MAX_CONCURRENT_SPIDERS=4
INGESTION_RESPECT_ROBOTS_TXT=true
INGESTION_REQUEST_TIMEOUT_SECONDS=30
INGESTION_MAX_RETRIES=3
```

### MinIO (Object Storage)
```
MINIO_ENDPOINT=minio:9000      # or minio.example.com:9000
MINIO_ACCESS_KEY=minioadmin     # Change in production!
MINIO_SECRET_KEY=minioadmin     # Change in production!
MINIO_BUCKET_DOCUMENTS=documents
MINIO_USE_SSL=false             # Set to true in production
```

### PostgreSQL
```
POSTGRES_HOST=postgres          # or db.example.com
POSTGRES_PORT=5432
POSTGRES_DB=ragqa
POSTGRES_USER=ragqa_user
POSTGRES_PASSWORD=<secure>      # Change in production!
```

### RAG Service
```
RAG_SERVICE_URL=http://rag-service:8001
RAG_CHUNK_SIZE=512
RAG_CHUNK_OVERLAP=64
```

### Redis (Optional Caching)
```
REDIS_HOST=redis
REDIS_PORT=6379
REDIS_PASSWORD=<optional>
REDIS_DB_CACHE=0
```

### Scraper Settings
```
SCRAPER_MAX_PAGES_PER_SITE=1000
SCRAPER_DEPTH_LIMIT=3
SCRAPER_CONCURRENT_REQUESTS=16
SCRAPER_DOWNLOAD_DELAY=1.0

PLAYWRIGHT_HEADLESS=true
PLAYWRIGHT_TIMEOUT_MS=30000
PLAYWRIGHT_WAIT_FOR_LOAD_STATE=networkidle

PDF_MIN_FILE_SIZE_KB=1
PDF_MAX_FILE_SIZE_MB=50
PDF_TIMEOUT_SECONDS=60
```

## Database Setup

### Create PostgreSQL Tables

```sql
-- Documents table
CREATE TABLE IF NOT EXISTS documents (
    document_id UUID PRIMARY KEY,
    title VARCHAR(500),
    url TEXT,
    source_site VARCHAR(255),
    content_type VARCHAR(50),
    language VARCHAR(10),
    content_length INT,
    raw_document_path VARCHAR(255),
    processed_text_path VARCHAR(255),
    metadata JSONB,
    minio_ids TEXT[],
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    job_id UUID
);

-- Events table
CREATE TABLE IF NOT EXISTS events (
    event_id UUID PRIMARY KEY,
    title VARCHAR(500),
    date DATE,
    venue VARCHAR(255),
    description TEXT,
    source_url TEXT,
    source_page_id UUID REFERENCES documents(document_id) ON DELETE CASCADE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Scrape jobs table
CREATE TABLE IF NOT EXISTS scrape_jobs (
    job_id UUID PRIMARY KEY,
    target_url TEXT,
    spider_type VARCHAR(50),
    status VARCHAR(50),
    pages_crawled INT DEFAULT 0,
    documents_found INT DEFAULT 0,
    errors INT DEFAULT 0,
    started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP,
    error_message TEXT
);

-- Create indexes for performance
CREATE INDEX IF NOT EXISTS idx_documents_source_site ON documents(source_site);
CREATE INDEX IF NOT EXISTS idx_documents_language ON documents(language);
CREATE INDEX IF NOT EXISTS idx_documents_created_at ON documents(created_at);
CREATE INDEX IF NOT EXISTS idx_events_date ON events(date);
CREATE INDEX IF NOT EXISTS idx_scrape_jobs_status ON scrape_jobs(status);
```

### Setup MinIO Buckets

```bash
# Using minio/mc client
mc alias set minio http://minio:9000 minioadmin minioadmin
mc mb minio/documents

# Or via HTTP API
curl -X PUT http://minio:9000/documents
```

## Testing

### Run Unit Tests

```bash
# Install test dependencies
pip install pytest pytest-asyncio pytest-cov

# Run all tests
pytest tests/

# Run with coverage
pytest --cov=app --cov-report=html tests/

# Run specific test
pytest tests/test_static_spider.py -v

# Run with log output
pytest -s tests/
```

### Integration Tests

Start dependent services first:
```bash
docker-compose up -d postgres minio redis rag-service
```

Then run tests:
```bash
pytest tests/integration/
```

## Docker Deployment

### Build Image

```bash
docker build -t data-ingestion:1.0.0 .

# With build arguments
docker build \
  --build-arg PYTHON_VERSION=3.11 \
  -t data-ingestion:1.0.0 .
```

### Run Container

```bash
docker run -d \
  --name data-ingestion \
  --network rag-network \
  -p 8006:8006 \
  -e POSTGRES_HOST=postgres \
  -e MINIO_ENDPOINT=minio:9000 \
  -e RAG_SERVICE_URL=http://rag-service:8001 \
  -v /path/to/.env:/app/.env \
  data-ingestion:1.0.0
```

### Docker Compose

Add to docker-compose.yml:

```yaml
data-ingestion:
  build: ./data-ingestion
  ports:
    - "8006:8006"
  environment:
    - APP_ENV=production
    - POSTGRES_HOST=postgres
    - MINIO_ENDPOINT=minio:9000
    - RAG_SERVICE_URL=http://rag-service:8001
  depends_on:
    - postgres
    - minio
    - rag-service
  networks:
    - rag-network
  healthcheck:
    test: ["CMD", "curl", "-f", "http://localhost:8006/health"]
    interval: 30s
    timeout: 10s
    retries: 3
    start_period: 5s
```

## Monitoring

### Health Check

```bash
curl http://localhost:8006/health
```

Response:
```json
{
  "status": "healthy",
  "service": "data-ingestion",
  "version": "1.0.0",
  "uptime_seconds": 3600,
  "timestamp": "2026-02-24T10:30:00Z",
  "dependencies": {
    "minio": {"status": "healthy", "latency_ms": 12},
    "postgres": {"status": "healthy", "latency_ms": 8},
    "redis": {"status": "healthy", "latency_ms": 2},
    "rag_service": {"status": "healthy", "latency_ms": 45}
  }
}
```

### Metrics

```bash
curl http://localhost:8006/metrics | grep ingestion_
```

### Logs

View container logs:
```bash
docker logs -f data-ingestion
```

With Docker Compose:
```bash
docker-compose logs -f data-ingestion
```

## Troubleshooting

### Issue: Connection refused to PostgreSQL

**Solution:**
1. Verify PostgreSQL is running: `docker ps | grep postgres`
2. Check `POSTGRES_HOST` in `.env`
3. Verify network connectivity: `docker network ls`
4. Check database credentials

### Issue: MinIO connection errors

**Solution:**
1. Verify MinIO service: `docker ps | grep minio`
2. Check `MINIO_ENDPOINT` and credentials
3. Test manually:
```bash
aws s3api list-buckets \
  --endpoint-url http://minio:9000 \
  --access-key minioadmin \
  --secret-key minioadmin
```

### Issue: Spider timeouts

**Solution:**
1. Increase `INGESTION_REQUEST_TIMEOUT_SECONDS`
2. Increase `PLAYWRIGHT_TIMEOUT_MS` for dynamic spiders
3. Reduce `SCRAPER_CONCURRENT_REQUESTS`
4. Check network connectivity to target sites

### Issue: Out of memory

**Solution:**
1. Reduce `INGESTION_MAX_CONCURRENT_SPIDERS`
2. Reduce `SCRAPER_CONCURRENT_REQUESTS`
3. Increase Docker memory limit:
```bash
docker update --memory 4g data-ingestion
```

### Issue: Playwright browser not found

**Solution:**
```bash
# Install browsers
python -m playwright install chromium

# In Docker, browsers are installed during build
docker build --no-cache .
```

## Performance Tuning

### For High Throughput

```env
INGESTION_MAX_CONCURRENT_SPIDERS=8
SCRAPER_CONCURRENT_REQUESTS=32
SCRAPER_DOWNLOAD_DELAY=0.5
INGESTION_MAX_PAGES_PER_SITE=5000
```

### For Memory Efficiency

```env
INGESTION_MAX_CONCURRENT_SPIDERS=1
SCRAPER_CONCURRENT_REQUESTS=4
SCRAPER_DOWNLOAD_DELAY=2.0
DEDUP_MIN_HASH_NUM_PERM=64
```

### For Quality (Slower but Better)

```env
INGESTION_RESPECT_ROBOTS_TXT=true
SCRAPER_DOWNLOAD_DELAY=2.0
PLAYWRIGHT_WAIT_FOR_LOAD_STATE=networkidle
RAG_CHUNK_SIZE=256
```

## Backup and Recovery

### Backup PostgreSQL

```bash
docker exec data-postgres pg_dump -U ragqa_user ragqa > backup.sql

# Or with docker-compose
docker-compose exec postgres pg_dump -U ragqa_user ragqa > backup.sql
```

### Restore PostgreSQL

```bash
docker exec -i data-postgres psql -U ragqa_user ragqa < backup.sql
```

### Backup MinIO

```bash
# Using mc
mc cp --recursive minio/documents /local/backup/
```

## Production Checklist

- [ ] Configure secure passwords in `.env`
- [ ] Enable SSL/TLS for MINIO_USE_SSL
- [ ] Set APP_ENV=production
- [ ] Configure proper log retention
- [ ] Setup database backups
- [ ] Configure health check monitoring
- [ ] Setup Prometheus scraping
- [ ] Configure alerting for errors
- [ ] Test failover scenarios
- [ ] Document custom configurations
- [ ] Setup CI/CD pipeline
- [ ] Load test with production data
- [ ] Security audit of configurations
- [ ] Capacity planning for growth

## Support

For issues or questions:
1. Check application logs
2. Review metrics at `/metrics`
3. Check health at `/health`
4. Verify configuration in `.env`
5. Review shared contract compliance in documentation
