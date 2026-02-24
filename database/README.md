# PostgreSQL Database - Stream 2

This directory contains the complete database schema, migrations, seed data, and utility scripts for the RAG-based Hindi QA system.

## Structure

```
database/
├── Dockerfile                      # PostgreSQL 16 Alpine with extensions
├── init-extensions.sql            # pg_trgm, uuid-ossp, pgcrypto
├── migrations/                    # 14 SQL migration files (001-014)
│   ├── 001_create_roles_and_permissions.sql
│   ├── 002_create_users.sql
│   ├── 003_create_sessions.sql
│   ├── 004_create_conversations.sql
│   ├── 005_create_documents.sql
│   ├── 006_create_feedback.sql
│   ├── 007_create_audit_log.sql
│   ├── 008_create_analytics_events.sql
│   ├── 009_create_system_config.sql
│   ├── 010_create_scrape_jobs.sql
│   ├── 011_create_translation_cache.sql
│   ├── 012_create_model_versions.sql
│   ├── 013_create_events.sql
│   └── 014_create_api_keys.sql
├── seed/                          # Seed data files
│   ├── seed_roles_and_permissions.sql
│   ├── seed_users.sql
│   ├── seed_config.sql
│   ├── seed_scrape_targets.sql
│   └── seed_sample_documents.sql
├── init-db.sh                     # Initialization script
├── backup.sh                      # Backup/restore script
└── README.md                      # This file
```

## Quick Start

### 1. Build Docker Image

```bash
docker build -t rag-qa-postgres:16 .
```

### 2. Run Container (with docker-compose)

The database service is configured in the main `docker-compose.yml`:

```bash
docker-compose up -d postgres
```

### 3. Initialize Database

Once PostgreSQL is running, initialize the schema and seed data:

```bash
./init-db.sh
```

Or with environment variables:

```bash
POSTGRES_HOST=localhost \
POSTGRES_PORT=5432 \
POSTGRES_DB=ragqa \
POSTGRES_USER=ragqa_user \
POSTGRES_PASSWORD=your_secure_password \
./init-db.sh
```

## Database Schema

### Tables Overview

| Table | Purpose | Key Columns |
|---|---|---|
| `roles` | RBAC role definitions | id, name, description |
| `permissions` | Granular role permissions | role_id, resource, action |
| `users` | Admin users | id, username, email, role_id |
| `sessions` | Chat sessions | id, user_ip, language, session_start_at |
| `conversations` | Message history | session_id, role, content, language |
| `documents` | Ingested documents | id, title, source_url, source_site, status |
| `document_chunks` | Document chunks for vectorization | document_id, chunk_index, milvus_id |
| `feedback` | User feedback and sentiment | session_id, rating, sentiment_score, sentiment_label |
| `audit_log` | Compliance audit trail | action, resource_type, resource_id, user_id |
| `analytics_events` | Performance metrics | event_type, latency_ms, cache_hit |
| `system_config` | Key-value configuration | config_key, config_value, value_type |
| `scrape_jobs` | Web scraping tracking | target_url, source_site, job_status |
| `translation_cache` | Translation caching | source_text_hash, languages, translated_text |
| `model_versions` | Fine-tuned models | model_id, version, eval_score, status |
| `events` | Cultural events | title, event_date, venue, source_site |
| `api_keys` | API key management | key_hash, role_id, is_active, expires_at |

## RBAC Roles

Four roles are seeded by default:

### Admin (`admin`)
- Full system access
- User management, document management, scraping, model training
- Configuration and API key management
- Audit log access

### Editor (`editor`)
- Content management: create/update/delete documents
- Scraping job management
- Read analytics and feedback
- Event management

### Viewer (`viewer`)
- Read-only access to analytics and conversation history
- View feedback and events
- No write permissions

### API Consumer (`api_consumer`)
- Chat, search, and voice API access (embedded widget)
- Submit feedback, OCR uploads
- No admin or management operations

## Configuration

System configuration is stored in the `system_config` table. Key settings include:

### Rate Limits (requests/minute per role)
```sql
RATE_LIMIT_ADMIN=120
RATE_LIMIT_EDITOR=90
RATE_LIMIT_VIEWER=30
RATE_LIMIT_API_CONSUMER=60
```

### Data Retention (days)
```sql
RETENTION_CONVERSATIONS_DAYS=90
RETENTION_FEEDBACK_DAYS=365
RETENTION_AUDIT_LOG_DAYS=730        -- 2 years for compliance
RETENTION_ANALYTICS_DAYS=365
RETENTION_TRANSLATION_CACHE_DAYS=30
```

### LLM Models
```sql
LLM_MODEL_STANDARD=meta-llama/Llama-3.1-8B-Instruct-AWQ
LLM_MODEL_LONGCTX=mistralai/Mistral-NeMo-Instruct-2407-AWQ
LLM_MODEL_MULTIMODAL=google/gemma-3-12b-it-awq
```

### RAG Configuration
```sql
RAG_CHUNK_SIZE=512
RAG_CHUNK_OVERLAP=64
RAG_TOP_K=10
RAG_RERANK_TOP_K=5
RAG_CONFIDENCE_THRESHOLD=0.65
RAG_CACHE_TTL_SECONDS=3600
```

## Scripting

### Initialize Database

```bash
./init-db.sh [--skip-seed]
```

Runs all 14 migrations in order, then populates seed data. Use `--skip-seed` to skip seeding.

### Backup & Restore

```bash
# Full backup to local directory
./backup.sh

# Backup and upload to S3
./backup.sh --upload

# Incremental backup
./backup.sh --incremental

# Restore from backup
gunzip < /tmp/backups/ragqa_backup_YYYYMMDD_HHMMSS.sql.gz | psql -U ragqa_user -d ragqa
```

## Language Codes

The system supports 23 Indian and international languages (ISO 639-1 codes):

```
hi, en, bn, te, mr, ta, ur, gu, kn, ml, or, pa, as,
mai, sa, ne, sd, kok, doi, mni, sat, bo, ks
```

All language columns use these codes for consistent multi-language support.

## Indexes

Each table includes strategic indexes for:
- **Lookup performance:** Primary keys and foreign keys
- **Search optimization:** Full-text search columns, language filtering
- **Time-series queries:** created_at, updated_at timestamps
- **Analytics:** Composite indexes on common query patterns
- **Soft deletion:** Partial indexes for active records only

## Constraints & Validation

- **Foreign Keys:** Referential integrity with cascade delete for document chunks
- **Unique Constraints:** username, email (users); resource+action (permissions); config_key (system_config)
- **Timestamps:** All records have created_at (immutable) and updated_at (mutable) in UTC
- **UUIDs:** Primary keys are UUID v4 for distributed uniqueness

## Maintenance

### Vacuum & Analyze

```bash
# Regular maintenance (run weekly)
PGPASSWORD=password psql -U ragqa_user -d ragqa -c "VACUUM ANALYZE;"
```

### Backup Retention

Old backups are automatically cleaned up after 30 days. Configure `RETENTION_DAYS` in `backup.sh`.

## Troubleshooting

### Connection Issues

```bash
# Test connection
PGPASSWORD=password psql -h localhost -U ragqa_user -d ragqa -c "SELECT 1;"

# Check container logs
docker logs rag-qa-postgres
```

### Migration Failures

Each migration is idempotent (uses `CREATE TABLE IF NOT EXISTS`). If a migration fails:

1. Check the error message
2. Fix the underlying issue
3. Re-run `./init-db.sh`

### Performance Issues

```bash
# Check table sizes
SELECT relname, pg_size_pretty(pg_total_relation_size(relid))
FROM pg_stat_user_tables
ORDER BY pg_total_relation_size(relid) DESC;

# Check index usage
SELECT * FROM pg_stat_user_indexes;
```

## Security Notes

- Passwords are never logged; use environment variables
- API key hashes use bcrypt (never store plaintext keys)
- Audit logs are immutable (INSERT-only)
- PII (Aadhaar, phone, email) is logged only by ID, never verbatim
- system_config.is_secret flag prevents secret exposure in logs

## References

- Shared Contracts: `../Implementation_Plan/01_Shared_Contracts.md`
- Stream 2 Plan: `../Implementation_Plan/Stream_02_Database.md`
