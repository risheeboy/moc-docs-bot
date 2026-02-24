# Database

PostgreSQL 16 on AWS RDS (Multi-AZ). 14 sequential SQL migrations (001-014). Tables for users, roles, documents, conversations, feedback, analytics, audit logs, configuration, scraping jobs, model versions.

## Key Files

- `migrations/001-014_*.sql` — Sequential schema migrations
- `seed-data.sh` — Initial data (4 roles, 30 Ministry URLs, admin user, system config)
- `init-db.sh` — Migration runner (called by deploy.sh)

## Key Tables

**Users & RBAC:**
- users (email, password_hash, role_id, name)
- roles (name: admin, editor, viewer, guest)
- permissions (role_id, resource, action: CREATE, READ, UPDATE, DELETE)

**Documents & Content:**
- documents (title, language, source_url, uploaded_by, metadata_json)
- document_chunks (document_id, chunk_text, embedding_id, token_count)

**Conversations & Feedback:**
- conversations (user_id, language, created_at)
- messages (conversation_id, role, content, timestamp)
- feedback (message_id, rating 1-5, suggestion_text)

**System Management:**
- api_keys (user_id, key_hash, permissions, expires_at)
- system_config (key, value, description, updated_by)
- audit_log (user_id, action, resource_type, resource_id, timestamp, details_json)
- analytics_events (event_type, user_id, context_json, timestamp)

**Data Ingestion & Models:**
- scrape_jobs (website_url, status, documents_found, config_json)
- translation_cache (text_hash, source_lang, target_lang, ttl)
- model_versions (model_name, base_model, version, metrics_json, deployed_at)

## Connection

- RDS: PostgreSQL 16 Multi-AZ (ap-south-1)
- Private subnet (no public access)
- Security group: allows port 5432 from ECS only
- Credentials: AWS Secrets Manager

## Connection Pool

- Default: 10 connections per service
- Max: 20, idle timeout: 15 minutes

## Backups

- Automated: Daily at 2 AM UTC
- Retention: 30 days
- Snapshots preserved during destroy

## Data Retention

- conversations/messages: indefinite
- audit_log: 365 days
- analytics_events: 90 days (TTL)
- translation_cache: 24 hours (TTL)

## Known Issues

1. **Migration 012** — Has `s3_path` column (should be `s3_path`). Create migration 015 to fix.
2. **Missing indexes** — analytics_events.timestamp, translation_cache.text_hash need indexes.
3. **Missing FK constraints** — document_chunks lacks unique on chunk_hash.
