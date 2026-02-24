---
name: db-migrate
description: Create and run PostgreSQL database migrations. Use when adding tables, columns, indexes, or modifying the database schema.
allowed-tools: Bash, Read, Write, Glob
---

# Database Migration Skill

## Creating a New Migration

1. Find the next migration number:
```bash
ls /sessions/amazing-wizardly-wright/mnt/rag-qa-hindi/database/migrations/ | tail -1
```

2. Create the migration file following this template:
```sql
-- NNN_description_of_change.sql
BEGIN;

-- Your DDL changes here
ALTER TABLE table_name ADD COLUMN new_column VARCHAR(255);
CREATE INDEX idx_table_new_column ON table_name(new_column);

COMMIT;
```

3. Rules:
   - NEVER modify existing migration files
   - Always wrap in BEGIN/COMMIT
   - Include rollback instructions in comments
   - Test locally: `psql postgresql://user:password@localhost:5432/ragqa < migration.sql`

## Running Migrations

Local:
```bash
cd /sessions/amazing-wizardly-wright/mnt/rag-qa-hindi/database && ./init-db.sh
```

AWS:
```bash
cd /sessions/amazing-wizardly-wright/mnt/rag-qa-hindi/aws/scripts && ./run-migrations.sh
```

## Current Schema

15 migrations (001-015). Key tables: users, roles, permissions, sessions, conversations, documents, document_chunks, feedback, audit_log, analytics_events, system_config, scrape_jobs, translation_cache, model_versions, events, api_keys.

See `database/migrations/` for full schema evolution.

## Migration Best Practices

- **Naming:** Use descriptive names: `NNN_add_user_profile_table.sql`
- **Idempotency:** Use `IF EXISTS` / `IF NOT EXISTS` for safety
- **One concern per migration:** Separate table creation from column additions
- **Backward compatibility:** Avoid breaking changes; add columns as nullable first
- **Testing:** Always test rollback on a local copy
- **Documentation:** Comment complex logic in migration files

## Common Migration Patterns

Add a column with default:
```sql
ALTER TABLE documents ADD COLUMN status VARCHAR(50) DEFAULT 'active' NOT NULL;
```

Create an index:
```sql
CREATE INDEX CONCURRENTLY idx_documents_status ON documents(status);
```

Add foreign key:
```sql
ALTER TABLE conversations ADD CONSTRAINT fk_conversations_user_id
  FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE;
```

Drop with safety:
```sql
DROP TABLE IF EXISTS old_table CASCADE;
```
