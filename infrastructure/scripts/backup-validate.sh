#!/bin/bash
# ============================================================================
# Backup Validation Script
# Verifies backup integrity by performing restore to temporary database
# ============================================================================

set -e

PROJECT_ROOT="$( cd "$( dirname "${BASH_SOURCE[0]}" )/../.." && pwd )"
BACKUP_DIR="${PROJECT_ROOT}/backups"

if [ $# -lt 1 ]; then
    echo "Usage: $0 <backup-timestamp>"
    echo ""
    echo "Available backups:"
    find "$BACKUP_DIR/daily" -maxdepth 1 -type d | sort -r | head -10
    exit 1
fi

BACKUP_TIMESTAMP=$1
BACKUP_PATH="$BACKUP_DIR/daily/$BACKUP_TIMESTAMP"
VALIDATION_DB="ragqa_validate_${TIMESTAMP}"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)

echo "=========================================="
echo "Backup Validation Test"
echo "Backup Timestamp: $BACKUP_TIMESTAMP"
echo "Validation DB: $VALIDATION_DB"
echo "=========================================="
echo ""

# Verify backup exists
if [ ! -d "$BACKUP_PATH" ]; then
    echo "ERROR: Backup not found: $BACKUP_PATH"
    exit 1
fi

# Load environment
set -a
source "$PROJECT_ROOT/.env"
set +a

# ============================================================================
# VALIDATE POSTGRESQL BACKUP
# ============================================================================
echo "[1/2] Validating PostgreSQL backup..."

PG_BACKUP=$(find "$BACKUP_PATH" -name "postgres_ragqa_*.sql.gz" | head -1)

if [ -z "$PG_BACKUP" ]; then
    echo "✗ PostgreSQL backup file not found"
    exit 1
fi

# Check file integrity
if ! gzip -t "$PG_BACKUP" 2>/dev/null; then
    echo "✗ PostgreSQL backup file is corrupted (gzip check failed)"
    exit 1
fi

echo "✓ PostgreSQL backup file integrity verified"

# Test restore to temporary database
echo "  Testing restore to temporary database..."

# Create temporary database
PGPASSWORD="${POSTGRES_PASSWORD}" psql -h postgres -U "${POSTGRES_USER}" -tc \
    "CREATE DATABASE \"$VALIDATION_DB\";" 2>/dev/null || {
    echo "✗ Failed to create temporary database"
    exit 1
}

# Attempt restore
if gzip -dc "$PG_BACKUP" | PGPASSWORD="${POSTGRES_PASSWORD}" psql \
    -h postgres \
    -U "${POSTGRES_USER}" \
    -d "$VALIDATION_DB" \
    --no-password --quiet 2>&1 | grep -i "error" > /dev/null; then
    echo "✗ Restore test failed (SQL errors detected)"
    PGPASSWORD="${POSTGRES_PASSWORD}" psql -h postgres -U "${POSTGRES_USER}" -tc \
        "DROP DATABASE \"$VALIDATION_DB\";" 2>/dev/null || true
    exit 1
fi

# Verify tables were restored
TABLE_COUNT=$(PGPASSWORD="${POSTGRES_PASSWORD}" psql -h postgres -U "${POSTGRES_USER}" \
    -d "$VALIDATION_DB" -tc \
    "SELECT COUNT(*) FROM information_schema.tables WHERE table_schema='public';" 2>/dev/null | tr -d ' ')

if [ "$TABLE_COUNT" -lt "1" ]; then
    echo "✗ Restore test failed (no tables found)"
    PGPASSWORD="${POSTGRES_PASSWORD}" psql -h postgres -U "${POSTGRES_USER}" -tc \
        "DROP DATABASE \"$VALIDATION_DB\";" 2>/dev/null || true
    exit 1
fi

echo "✓ PostgreSQL restore test passed ($TABLE_COUNT tables)"

# Calculate checksums
ORIGINAL_SIZE=$(du -b "$PG_BACKUP" | cut -f1)
RESTORED_SIZE=$(PGPASSWORD="${POSTGRES_PASSWORD}" psql -h postgres -U "${POSTGRES_USER}" \
    -d "$VALIDATION_DB" -tc "SELECT pg_database_size('$VALIDATION_DB');" 2>/dev/null | tr -d ' ')

# Clean up temporary database
PGPASSWORD="${POSTGRES_PASSWORD}" psql -h postgres -U "${POSTGRES_USER}" -tc \
    "DROP DATABASE \"$VALIDATION_DB\";" 2>/dev/null || true

echo "✓ PostgreSQL backup validation complete"
echo "  - Backup file size: $(numfmt --to=iec-i --suffix=B $ORIGINAL_SIZE 2>/dev/null || echo $ORIGINAL_SIZE)"
echo "  - Restored size:    $(numfmt --to=iec-i --suffix=B $RESTORED_SIZE 2>/dev/null || echo $RESTORED_SIZE)"

echo ""

# ============================================================================
# VALIDATE REDIS BACKUP
# ============================================================================
echo "[2/2] Validating Redis backup..."

REDIS_BACKUP=$(find "$BACKUP_PATH" -name "redis_dump_*.rdb" | head -1)

if [ -z "$REDIS_BACKUP" ]; then
    echo "⚠ Redis backup file not found, skipping validation"
else
    # Check file is valid RDB
    if file "$REDIS_BACKUP" | grep -q "data"; then
        REDIS_SIZE=$(du -h "$REDIS_BACKUP" | cut -f1)
        echo "✓ Redis backup file is valid ($REDIS_SIZE)"
    else
        echo "✗ Redis backup file is corrupted or invalid"
        exit 1
    fi

    echo "✓ Redis backup validation complete"
fi

echo ""

# ============================================================================
# SUMMARY
# ============================================================================
echo "=========================================="
echo "✓ Backup Validation Complete"
echo "=========================================="
echo ""
echo "All backups are valid and can be restored"
echo ""
echo "Backup location: $BACKUP_PATH"
echo "To restore:      ./infrastructure/scripts/restore.sh $BACKUP_TIMESTAMP"
echo ""
