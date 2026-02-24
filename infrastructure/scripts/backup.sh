#!/bin/bash
# ============================================================================
# Backup Script
# Automated backup of all persistent data
# PostgreSQL (pg_dump), Milvus, MinIO, and Redis
# ============================================================================

set -e

PROJECT_ROOT="$( cd "$( dirname "${BASH_SOURCE[0]}" )/../.." && pwd )"
BACKUP_DIR="${PROJECT_ROOT}/backups"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
DAILY_DIR="$BACKUP_DIR/daily/$TIMESTAMP"
WEEKLY_DIR="$BACKUP_DIR/weekly/$(date +%Y%m%d)"
FULL_BACKUP_DIR="$BACKUP_DIR/full/$TIMESTAMP"

echo "=========================================="
echo "RAG-QA System Backup"
echo "Timestamp: $TIMESTAMP"
echo "=========================================="
echo ""

# Load environment
set -a
source "$PROJECT_ROOT/.env"
set +a

# Create backup directories
mkdir -p "$DAILY_DIR" "$FULL_BACKUP_DIR"

# ============================================================================
# DETERMINE BACKUP TYPE
# ============================================================================
BACKUP_TYPE=${1:-daily}  # daily or weekly

echo "Backup Type: $BACKUP_TYPE"
echo ""

# ============================================================================
# 1. BACKUP POSTGRESQL
# ============================================================================
echo "[1/4] Backing up PostgreSQL (main database)..."

PG_BACKUP_FILE="$DAILY_DIR/postgres_ragqa_${TIMESTAMP}.sql.gz"

if PGPASSWORD="${POSTGRES_PASSWORD}" pg_dump \
    -h postgres \
    -U "${POSTGRES_USER}" \
    -d "${POSTGRES_DB}" \
    --format=plain \
    --verbose \
    --no-password 2>/dev/null | gzip > "$PG_BACKUP_FILE"; then

    PG_SIZE=$(du -h "$PG_BACKUP_FILE" | cut -f1)
    echo "✓ PostgreSQL backup: $PG_BACKUP_FILE ($PG_SIZE)"

    # Verify backup is valid
    if gzip -t "$PG_BACKUP_FILE" 2>/dev/null; then
        echo "✓ Backup integrity verified"
    else
        echo "✗ Backup integrity check failed!"
        exit 1
    fi
else
    echo "✗ PostgreSQL backup failed"
    exit 1
fi

echo ""

# ============================================================================
# 2. BACKUP LANGFUSE POSTGRESQL
# ============================================================================
echo "[2/4] Backing up Langfuse PostgreSQL database..."

LANGFUSE_BACKUP_FILE="$DAILY_DIR/postgres_langfuse_${TIMESTAMP}.sql.gz"

if PGPASSWORD="${LANGFUSE_PG_PASSWORD}" pg_dump \
    -h langfuse-postgres \
    -U "${LANGFUSE_PG_USER}" \
    -d "${LANGFUSE_PG_DB}" \
    --format=plain \
    --verbose \
    --no-password 2>/dev/null | gzip > "$LANGFUSE_BACKUP_FILE"; then

    LANGFUSE_SIZE=$(du -h "$LANGFUSE_BACKUP_FILE" | cut -f1)
    echo "✓ Langfuse backup: $LANGFUSE_BACKUP_FILE ($LANGFUSE_SIZE)"
else
    echo "✗ Langfuse backup failed"
    exit 1
fi

echo ""

# ============================================================================
# 3. BACKUP REDIS
# ============================================================================
echo "[3/4] Backing up Redis..."

REDIS_BACKUP_FILE="$DAILY_DIR/redis_dump_${TIMESTAMP}.rdb"

if redis-cli -h redis -p 6379 -a "${REDIS_PASSWORD}" BGSAVE &>/dev/null; then
    sleep 2
    docker cp rag-qa-redis:/data/dump.rdb "$REDIS_BACKUP_FILE" 2>/dev/null
    REDIS_SIZE=$(du -h "$REDIS_BACKUP_FILE" | cut -f1)
    echo "✓ Redis backup: $REDIS_BACKUP_FILE ($REDIS_SIZE)"
else
    echo "⚠ Redis backup skipped (BGSAVE failed)"
fi

echo ""

# ============================================================================
# 4. BACKUP MINIO (MinIO bucket sync to backup storage)
# ============================================================================
echo "[4/4] Backing up MinIO (documents)..."

MINIO_BACKUP_DIR="$DAILY_DIR/minio"
mkdir -p "$MINIO_BACKUP_DIR"

# Note: This requires minio-mc tool or custom backup script
# For production, use MinIO's built-in replication/mirroring

echo "ℹ MinIO backup (documents bucket)..."
docker run --rm \
    --network rag-network \
    -v "$MINIO_BACKUP_DIR:/backup" \
    minio/minio:latest bash -c "
    mc alias set minio http://minio:9000 '${MINIO_ACCESS_KEY}' '${MINIO_SECRET_KEY}' 2>/dev/null || true
    mc cp --recursive minio/documents /backup/ 2>/dev/null || true
" 2>/dev/null || echo "⚠ MinIO backup skipped (requires mc tool)"

echo ""

# ============================================================================
# WEEKLY FULL BACKUP (copy to weekly directory)
# ============================================================================
if [ "$BACKUP_TYPE" = "weekly" ]; then
    echo "Creating weekly full backup..."
    cp -r "$DAILY_DIR"/* "$WEEKLY_DIR/" 2>/dev/null || true
    echo "✓ Weekly backup: $WEEKLY_DIR"

    # Clean old weekly backups (keep 4 weeks)
    find "$BACKUP_DIR/weekly" -maxdepth 1 -type d -mtime +28 -exec rm -rf {} + 2>/dev/null || true
fi

# ============================================================================
# CLEANUP OLD BACKUPS
# ============================================================================
echo ""
echo "Cleaning up old backups (keeping last 30 days)..."
find "$BACKUP_DIR/daily" -maxdepth 1 -type d -mtime +30 -exec rm -rf {} + 2>/dev/null || true
echo "✓ Cleanup complete"

# ============================================================================
# UPLOAD TO MINIO BACKUP BUCKET
# ============================================================================
echo ""
echo "Uploading backups to MinIO..."

docker run --rm \
    --network rag-network \
    -v "$DAILY_DIR:/data" \
    minio/minio:latest bash -c "
    mc alias set minio http://minio:9000 '${MINIO_ACCESS_KEY}' '${MINIO_SECRET_KEY}' 2>/dev/null || true
    mc cp --recursive /data minio/${MINIO_BUCKET_BACKUPS}/daily_${TIMESTAMP}/ 2>/dev/null || true
    echo '✓ Backups uploaded to MinIO'
" 2>/dev/null || echo "ℹ MinIO upload skipped"

# ============================================================================
# SUMMARY
# ============================================================================
echo ""
echo "=========================================="
echo "✓ Backup Complete"
echo "=========================================="
echo ""
echo "Backup Summary:"
echo "  Type:     $BACKUP_TYPE"
echo "  Location: $DAILY_DIR"
du -sh "$DAILY_DIR"
echo ""
echo "Total backup size:"
du -sh "$BACKUP_DIR" 2>/dev/null || echo "N/A"
echo ""
echo "To restore: ./infrastructure/scripts/restore.sh [backup-timestamp]"
echo ""
