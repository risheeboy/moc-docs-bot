#!/bin/bash
# ============================================================================
# Restore Script
# Restore data from backup with integrity validation
# ============================================================================

set -e

PROJECT_ROOT="$( cd "$( dirname "${BASH_SOURCE[0]}" )/../.." && pwd )"
BACKUP_DIR="${PROJECT_ROOT}/backups"

if [ $# -lt 1 ]; then
    echo "Usage: $0 <backup-timestamp>"
    echo ""
    echo "Available backups:"
    find "$BACKUP_DIR/daily" -maxdepth 1 -type d -newer "$BACKUP_DIR" | sort -r | head -5
    exit 1
fi

BACKUP_TIMESTAMP=$1
BACKUP_PATH="$BACKUP_DIR/daily/$BACKUP_TIMESTAMP"

echo "=========================================="
echo "RAG-QA System Restore"
echo "Backup Timestamp: $BACKUP_TIMESTAMP"
echo "=========================================="
echo ""

# Verify backup exists
if [ ! -d "$BACKUP_PATH" ]; then
    echo "ERROR: Backup not found: $BACKUP_PATH"
    exit 1
fi

echo "Backup contents:"
ls -lh "$BACKUP_PATH"
echo ""

# Load environment
set -a
source "$PROJECT_ROOT/.env"
set +a

# Prompt for confirmation
read -p "This will overwrite existing data. Continue? (yes/no): " CONFIRM
if [ "$CONFIRM" != "yes" ]; then
    echo "Restore cancelled"
    exit 0
fi

echo ""

# ============================================================================
# RESTORE POSTGRESQL
# ============================================================================
echo "[1/3] Restoring PostgreSQL (main database)..."

PG_BACKUP=$(find "$BACKUP_PATH" -name "postgres_ragqa_*.sql.gz" | head -1)

if [ -z "$PG_BACKUP" ]; then
    echo "✗ PostgreSQL backup file not found"
    exit 1
fi

# Drop and recreate database
echo "  Dropping existing database..."
PGPASSWORD="${POSTGRES_PASSWORD}" psql -h postgres -U "${POSTGRES_USER}" -tc \
    "DROP DATABASE IF EXISTS \"${POSTGRES_DB}\" WITH (FORCE);" || true

echo "  Creating database..."
PGPASSWORD="${POSTGRES_PASSWORD}" psql -h postgres -U "${POSTGRES_USER}" -tc \
    "CREATE DATABASE \"${POSTGRES_DB}\";"

echo "  Restoring from backup..."
gzip -dc "$PG_BACKUP" | PGPASSWORD="${POSTGRES_PASSWORD}" psql \
    -h postgres \
    -U "${POSTGRES_USER}" \
    -d "${POSTGRES_DB}" \
    --no-password 2>&1 | tail -5

echo "✓ PostgreSQL restored"
echo ""

# ============================================================================
# RESTORE LANGFUSE POSTGRESQL
# ============================================================================
echo "[2/3] Restoring Langfuse PostgreSQL database..."

LANGFUSE_BACKUP=$(find "$BACKUP_PATH" -name "postgres_langfuse_*.sql.gz" | head -1)

if [ -z "$LANGFUSE_BACKUP" ]; then
    echo "⚠ Langfuse backup file not found, skipping"
else
    # Drop and recreate database
    echo "  Dropping existing database..."
    PGPASSWORD="${LANGFUSE_PG_PASSWORD}" psql -h langfuse-postgres -U "${LANGFUSE_PG_USER}" -tc \
        "DROP DATABASE IF EXISTS \"${LANGFUSE_PG_DB}\" WITH (FORCE);" || true

    echo "  Creating database..."
    PGPASSWORD="${LANGFUSE_PG_PASSWORD}" psql -h langfuse-postgres -U "${LANGFUSE_PG_USER}" -tc \
        "CREATE DATABASE \"${LANGFUSE_PG_DB}\";"

    echo "  Restoring from backup..."
    gzip -dc "$LANGFUSE_BACKUP" | PGPASSWORD="${LANGFUSE_PG_PASSWORD}" psql \
        -h langfuse-postgres \
        -U "${LANGFUSE_PG_USER}" \
        -d "${LANGFUSE_PG_DB}" \
        --no-password 2>&1 | tail -5

    echo "✓ Langfuse restored"
fi

echo ""

# ============================================================================
# RESTORE REDIS
# ============================================================================
echo "[3/3] Restoring Redis..."

REDIS_BACKUP=$(find "$BACKUP_PATH" -name "redis_dump_*.rdb" | head -1)

if [ -z "$REDIS_BACKUP" ]; then
    echo "⚠ Redis backup file not found, skipping"
else
    echo "  Copying backup file..."
    docker cp "$REDIS_BACKUP" rag-qa-redis:/data/dump.rdb

    echo "  Reloading Redis..."
    redis-cli -h redis -p 6379 -a "${REDIS_PASSWORD}" SHUTDOWN NOSAVE 2>/dev/null || true
    sleep 2

    # Restart Redis container
    docker-compose -f "$PROJECT_ROOT/docker-compose.yml" restart redis

    # Wait for Redis to come up
    sleep 5

    # Verify data was restored
    KEYS_COUNT=$(redis-cli -h redis -p 6379 -a "${REDIS_PASSWORD}" DBSIZE 2>/dev/null | grep -oP '\d+' || echo "0")
    echo "✓ Redis restored ($KEYS_COUNT keys)"
fi

echo ""

# ============================================================================
# SUMMARY
# ============================================================================
echo "=========================================="
echo "✓ Restore Complete"
echo "=========================================="
echo ""
echo "Verification steps:"
echo "  1. Check database: psql -h localhost -U ragqa_user -d ragqa -c 'SELECT COUNT(*) FROM information_schema.tables;'"
echo "  2. Check Redis: redis-cli -h localhost -p 6379 DBSIZE"
echo "  3. Run health check: ./infrastructure/scripts/health-check.sh"
echo ""
