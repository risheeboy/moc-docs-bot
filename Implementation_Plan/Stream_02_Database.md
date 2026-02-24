### STREAM 2: PostgreSQL Database Schema & Migrations

**Agent Goal:** Design and implement the full relational database schema, migrations, and seed data.

**Files to create:**
```
database/
├── Dockerfile                      # postgres:16-alpine + extensions
├── migrations/
│   ├── 001_create_users.sql
│   ├── 002_create_sessions.sql
│   ├── 003_create_conversations.sql
│   ├── 004_create_documents.sql
│   ├── 005_create_feedback.sql
│   ├── 006_create_audit_log.sql
│   ├── 007_create_analytics.sql
│   ├── 008_create_config.sql
│   ├── 009_create_scrape_jobs.sql
│   ├── 010_create_translation_cache.sql
│   ├── 011_create_roles_permissions.sql
│   ├── 012_create_model_versions.sql
│   ├── 013_create_events.sql
│   └── 014_create_api_keys.sql
├── seed/
│   ├── seed_users.sql
│   ├── seed_config.sql
│   ├── seed_scrape_targets.sql     # 30 ring-fenced Ministry websites
│   └── seed_sample_documents.sql
├── init-db.sh                      # Runs migrations in order
└── backup.sh                       # pg_dump script
```

**Tables:**

| Table | Purpose |
|---|---|
| `users` | Admin users with role_id FK |
| `roles` | Role definitions (admin, editor, viewer, api_consumer) |
| `permissions` | Granular permissions per role (resource, action) |
| `sessions` | Chat session tracking (session_id, user_ip, lang, started_at, ended_at) |
| `conversations` | Message history (session_id, role, content, language, model_used, timestamp) |
| `documents` | Ingested doc metadata (filename, source_url, type, language, chunk_count, status) |
| `document_chunks` | Individual chunks with Milvus vector IDs |
| `feedback` | User ratings + text feedback + sentiment_score + sentiment_label |
| `audit_log` | All system events (who, what, when, ip, details JSONB) |
| `analytics_events` | Query counts, response times, language distribution, topic hits |
| `system_config` | Key-value config (model names, thresholds, feature flags) |
| `scrape_jobs` | Web scraping job status (target_url, last_scraped, status, doc_count) |
| `translation_cache` | Cached translations (source_text_hash, source_lang, target_lang, translated_text) |
| `model_versions` | Fine-tuned model tracking (model_id, version, eval_score, status, s3_path) |
| `events` | Cultural events extracted from Ministry websites (title, date, venue, description, source_url, language) |
| `api_keys` | API key management for external integrations (key_hash, role_id, created_by, expires_at, is_active) |

**No dependencies** — schema is self-contained.

**Shared Contracts Reference (from `01_Shared_Contracts.md`):**
- §3 Environment Variables: use `POSTGRES_HOST`, `POSTGRES_PORT`, `POSTGRES_DB`, `POSTGRES_USER`, `POSTGRES_PASSWORD`
- §9 Language Codes: `language` columns must accept all 23 codes listed in §9
- §10 Conventions: all column names `snake_case`, timestamps as `TIMESTAMPTZ` (UTC), UUIDs as `UUID` type
- §12 RBAC: four roles (admin, editor, viewer, api_consumer) with permissions as defined
- §3.2 Rate Limits: `system_config` seed must include `RATE_LIMIT_ADMIN=120`, `RATE_LIMIT_EDITOR=90`, `RATE_LIMIT_VIEWER=30`, `RATE_LIMIT_API_CONSUMER=60`
- §3.2 Data Retention: `system_config` seed must include retention periods: conversations=90d, feedback=365d, audit_log=730d

---

## Agent Prompt

### Agent 2: Database
```
PREREQUISITE: Read 00_Overview.md and 01_Shared_Contracts.md first.
Use exact language codes from §9, RBAC roles from §12, retention periods from §3.2.

Create PostgreSQL 16 schema with tables: users, roles, permissions,
sessions, conversations, documents, document_chunks, feedback (with
sentiment_score + sentiment_label columns), audit_log, analytics_events,
system_config, scrape_jobs (30 target websites), translation_cache,
model_versions (model_id, version, eval_score, created_at, status, s3_path).
RBAC: roles table with 4 roles:
  - admin: full access (CRUD all, config, scrape, model management)
  - editor: manage documents, view analytics, trigger scrapes
  - viewer: read-only analytics and conversation browser
  - api_consumer: chatbot + search API access only (for embed widget)
permissions table with resource + action granularity, FK to roles.
users table with role_id FK to roles.
events table: cultural events extracted from websites (title, date, venue,
  description, source_url, language) — for search page event cards.
api_keys table: API key management for external integrations (key_hash,
  role_id, created_by, expires_at, is_active) — for widget embedding.
Include indexes, constraints, foreign keys, seed data.
Seed scrape_jobs with 30 Ministry of Culture ring-fenced website URLs.
Seed roles and permissions with the 4 roles above.
Use sequential SQL migration files (001 through 014).
Migration 013: create_events table. Migration 014: create_api_keys table.
```

