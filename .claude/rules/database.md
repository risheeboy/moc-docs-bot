---
description: Database schema and migration rules
paths:
  - "database/**/*.sql"
  - "database/**/*.sh"
---

# Database Rules

PostgreSQL 16 on AWS RDS (Multi-AZ, SSL required).

## Migrations

- Sequential numbered files in `database/migrations/` (next: 016_*.sql)
- NEVER modify existing migration files — always create new ones
- Naming: `NNN_description_of_change.sql`
- Always wrap in `BEGIN; ... COMMIT;`
- Include rollback comments or corresponding down migration
- Test locally: `psql postgresql://user:password@localhost:5432/ragqa`

```sql
-- 016_add_feature.sql
BEGIN;

ALTER TABLE documents ADD COLUMN feature VARCHAR(255);
CREATE INDEX idx_documents_feature ON documents(feature);

-- Rollback: ALTER TABLE documents DROP COLUMN feature;

COMMIT;
```

## Key Tables

- `users` — User accounts, roles, metadata
- `roles` — RBAC role definitions (admin, editor, viewer, api_consumer)
- `sessions` — User sessions (Redis-backed, TTL 7 days)
- `conversations` — Chat histories, document references
- `documents` — Metadata (title, source, language, size, hash)
- `document_chunks` — Text chunks with Milvus embedding IDs
- `feedback` — User feedback (thumbs up/down, rating)
- `audit_log` — All user actions (upload, delete, search, chat)
- `scrape_jobs` — Document scraping history
- `model_versions` — Fine-tuned model metadata
- `api_keys` — External API consumer keys + rate limits

## Schema Initialization

```bash
cd database
./init-db.sh           # Runs all migrations
./seed-data.sh         # Optional: loads test data
```

## Connection Strings

- Local: `postgresql://user:password@localhost:5432/ragqa`
- AWS RDS: `postgresql://user:password@ragqa.abc123.ap-south-1.rds.amazonaws.com:5432/ragqa`

## Backup

```bash
pg_dump postgresql://...@hostname/ragqa > backup.sql
pg_restore --create backup.sql
```
