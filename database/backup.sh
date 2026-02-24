#!/bin/bash

# backup.sh - Create PostgreSQL backups and store in MinIO
# Backs up the entire ragqa database to a timestamped SQL dump
# Usage: ./backup.sh [--full] [--incremental] [--upload]
# Environment variables: POSTGRES_* (connection), MINIO_* (storage)

set -e

# Color output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Configuration
POSTGRES_HOST="${POSTGRES_HOST:-localhost}"
POSTGRES_PORT="${POSTGRES_PORT:-5432}"
POSTGRES_DB="${POSTGRES_DB:-ragqa}"
POSTGRES_USER="${POSTGRES_USER:-ragqa_user}"
POSTGRES_PASSWORD="${POSTGRES_PASSWORD:-}"

MINIO_ENDPOINT="${MINIO_ENDPOINT:-minio:9000}"
MINIO_ACCESS_KEY="${MINIO_ACCESS_KEY:-}"
MINIO_SECRET_KEY="${MINIO_SECRET_KEY:-}"
MINIO_BUCKET="${MINIO_BUCKET:-backups}"

BACKUP_DIR="${BACKUP_DIR:-/tmp/backups}"
RETENTION_DAYS="${RETENTION_DAYS:-30}"

# Backup type
BACKUP_TYPE="full"
UPLOAD_TO_MINIO=false

if [[ "$1" == "--incremental" ]]; then
    BACKUP_TYPE="incremental"
fi

if [[ "$1" == "--upload" ]] || [[ "$2" == "--upload" ]]; then
    UPLOAD_TO_MINIO=true
fi

# Create backup directory if it doesn't exist
mkdir -p "$BACKUP_DIR"

# Timestamp for backup file
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
DATE=$(date +%Y-%m-%d)
BACKUP_FILE="$BACKUP_DIR/ragqa_backup_${TIMESTAMP}.sql.gz"
BACKUP_MANIFEST="$BACKUP_DIR/ragqa_backup_${TIMESTAMP}.manifest"

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}PostgreSQL Backup Script${NC}"
echo -e "${BLUE}========================================${NC}"
echo "Backup Type: $BACKUP_TYPE"
echo "Host: $POSTGRES_HOST"
echo "Database: $POSTGRES_DB"
echo "Backup Directory: $BACKUP_DIR"
echo "Upload to MinIO: $UPLOAD_TO_MINIO"
echo ""

# Verify PostgreSQL connection
echo -e "${YELLOW}Verifying PostgreSQL connection...${NC}"
if ! PGPASSWORD="$POSTGRES_PASSWORD" psql \
    -h "$POSTGRES_HOST" \
    -p "$POSTGRES_PORT" \
    -U "$POSTGRES_USER" \
    -d "$POSTGRES_DB" \
    -c "SELECT 1" > /dev/null 2>&1; then
    echo -e "${RED}✗ Cannot connect to PostgreSQL${NC}"
    exit 1
fi
echo -e "${GREEN}✓ PostgreSQL connection verified${NC}"
echo ""

# Perform backup
echo -e "${YELLOW}Creating database backup...${NC}"
if PGPASSWORD="$POSTGRES_PASSWORD" pg_dump \
    -h "$POSTGRES_HOST" \
    -p "$POSTGRES_PORT" \
    -U "$POSTGRES_USER" \
    -d "$POSTGRES_DB" \
    --verbose \
    --format=plain \
    | gzip > "$BACKUP_FILE"; then
    echo -e "${GREEN}✓ Backup created: $BACKUP_FILE${NC}"
else
    echo -e "${RED}✗ Backup failed${NC}"
    exit 1
fi

# Get backup statistics
BACKUP_SIZE=$(du -h "$BACKUP_FILE" | cut -f1)
BACKUP_SIZE_BYTES=$(stat -f%z "$BACKUP_FILE" 2>/dev/null || stat -c%s "$BACKUP_FILE" 2>/dev/null)
TABLE_COUNT=$(PGPASSWORD="$POSTGRES_PASSWORD" psql \
    -h "$POSTGRES_HOST" \
    -p "$POSTGRES_PORT" \
    -U "$POSTGRES_USER" \
    -d "$POSTGRES_DB" \
    -t -c "SELECT COUNT(*) FROM information_schema.tables WHERE table_schema='public'")

# Create manifest file
cat > "$BACKUP_MANIFEST" <<EOF
{
  "timestamp": "$(date -u +%Y-%m-%dT%H:%M:%SZ)",
  "backup_type": "$BACKUP_TYPE",
  "database": "$POSTGRES_DB",
  "host": "$POSTGRES_HOST",
  "port": "$POSTGRES_PORT",
  "backup_file": "$(basename $BACKUP_FILE)",
  "backup_size_bytes": $BACKUP_SIZE_BYTES,
  "backup_size_human": "$BACKUP_SIZE",
  "table_count": $TABLE_COUNT,
  "compression": "gzip"
}
EOF

echo -e "${GREEN}✓ Backup manifest: $BACKUP_MANIFEST${NC}"
echo ""

# Display statistics
echo -e "${BLUE}Backup Statistics:${NC}"
echo "  Size: $BACKUP_SIZE"
echo "  Tables: $TABLE_COUNT"
echo "  Timestamp: $TIMESTAMP"
echo ""

# Upload to MinIO if requested
if [ "$UPLOAD_TO_MINIO" = true ]; then
    if [ -z "$MINIO_ACCESS_KEY" ] || [ -z "$MINIO_SECRET_KEY" ]; then
        echo -e "${RED}✗ MinIO credentials not configured (MINIO_ACCESS_KEY, MINIO_SECRET_KEY)${NC}"
        exit 1
    fi

    echo -e "${YELLOW}Uploading backup to MinIO...${NC}"
    MINIO_PATH="s3://$MINIO_ENDPOINT/$MINIO_BUCKET/postgres/$DATE/$(basename $BACKUP_FILE)"

    # Use mc (MinIO client) if available, otherwise show instructions
    if command -v mc &> /dev/null; then
        # Configure MinIO alias if needed
        if ! mc alias list | grep -q "minio"; then
            mc alias set minio "https://$MINIO_ENDPOINT" "$MINIO_ACCESS_KEY" "$MINIO_SECRET_KEY"
        fi

        if mc cp "$BACKUP_FILE" "minio/$MINIO_BUCKET/postgres/$DATE/$(basename $BACKUP_FILE)"; then
            echo -e "${GREEN}✓ Backup uploaded to MinIO${NC}"
            echo "  Location: $MINIO_PATH"
        else
            echo -e "${RED}✗ MinIO upload failed${NC}"
            exit 1
        fi
    else
        echo -e "${YELLOW}MinIO client (mc) not found. Installation instructions:${NC}"
        echo "  curl https://dl.min.io/client/mc/release/linux-amd64/mc -o mc && chmod +x mc"
        echo "  Then use: mc cp $BACKUP_FILE minio/$MINIO_BUCKET/postgres/$DATE/"
    fi
    echo ""
fi

# Cleanup old backups (retention policy)
echo -e "${YELLOW}Cleaning up backups older than $RETENTION_DAYS days...${NC}"
find "$BACKUP_DIR" -name "ragqa_backup_*.sql.gz" -mtime +$RETENTION_DAYS -delete
find "$BACKUP_DIR" -name "ragqa_backup_*.manifest" -mtime +$RETENTION_DAYS -delete
echo -e "${GREEN}✓ Cleanup completed${NC}"
echo ""

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}Backup completed successfully!${NC}"
echo -e "${GREEN}========================================${NC}"
