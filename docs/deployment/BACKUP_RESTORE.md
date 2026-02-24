# Backup & Restore Guide

**Version:** 1.0.0
**Last Updated:** February 24, 2026
**RFP Requirement:** Backup procedures for PostgreSQL, Milvus, MinIO, Redis

---

## Overview

Backup strategy for all critical data stores:

| Component | Data | Backup Method | Frequency | Retention |
|---|---|---|---|---|
| PostgreSQL | Conversations, metadata | pg_dump | Daily | 30 days |
| Milvus | Vector embeddings | Milvus snapshot | Daily | 7 days |
| MinIO | Documents, models | Bucket sync | Daily | 14 days |
| Redis | Cache, sessions | RDB dump | Hourly | 1 day |

---

## PostgreSQL Backup

### Full Backup

```bash
# Backup entire database
docker-compose exec -T postgres pg_dump \
    -U ragqa_user \
    -d ragqa \
    --format=plain \
    > /mnt/backup/postgres/ragqa_$(date +%Y%m%d_%H%M%S).sql

# Backup with compression
docker-compose exec -T postgres pg_dump \
    -U ragqa_user \
    -d ragqa \
    --format=custom \
    > /mnt/backup/postgres/ragqa_$(date +%Y%m%d_%H%M%S).dump

# Check backup size
ls -lh /mnt/backup/postgres/
```

### Incremental Backup (using WAL)

```bash
# PostgreSQL with WAL archiving enabled in docker-compose.yml:
# POSTGRES_INITDB_ARGS: "-c wal_level=replica"

# Archive WAL files
docker-compose exec -T postgres \
    mkdir -p /var/lib/postgresql/wal_archive

# Configure PostgreSQL for WAL archiving (in postgresql.conf)
# archive_mode = on
# archive_command = 'test ! -f /var/lib/postgresql/wal_archive/%f && cp %p /var/lib/postgresql/wal_archive/%f'
```

### Scheduled Daily Backup

```bash
# Create backup script: /opt/rag-qa-hindi/scripts/backup_postgres.sh

#!/bin/bash
set -e

BACKUP_DIR="/mnt/backup/postgres"
RETENTION_DAYS=30
TIMESTAMP=$(date +%Y%m%d_%H%M%S)

# Create backup directory
mkdir -p $BACKUP_DIR

# Backup database
docker-compose -f /opt/rag-qa-hindi/docker-compose.yml exec -T postgres pg_dump \
    -U ragqa_user \
    -d ragqa \
    --format=custom \
    | gzip > $BACKUP_DIR/ragqa_$TIMESTAMP.dump.gz

# Verify backup
if [ -s $BACKUP_DIR/ragqa_$TIMESTAMP.dump.gz ]; then
    echo "✓ PostgreSQL backup succeeded: $BACKUP_DIR/ragqa_$TIMESTAMP.dump.gz"

    # Delete old backups
    find $BACKUP_DIR -name "*.dump.gz" -mtime +$RETENTION_DAYS -delete
else
    echo "✗ PostgreSQL backup failed"
    exit 1
fi

# Schedule in crontab:
# 2 * * * * /opt/rag-qa-hindi/scripts/backup_postgres.sh >> /var/log/rag-qa/backup.log 2>&1
```

### PostgreSQL Restore

```bash
# Restore from dump file
docker-compose exec -T postgres psql \
    -U ragqa_user \
    -d ragqa \
    < /mnt/backup/postgres/ragqa_20260224_020000.sql

# Restore from compressed dump
gunzip -c /mnt/backup/postgres/ragqa_20260224_020000.dump.gz | \
    docker-compose exec -T postgres pg_restore \
    -U ragqa_user \
    -d ragqa

# Verify restore
docker-compose exec -T postgres psql \
    -U ragqa_user \
    -d ragqa \
    -c "SELECT count(*) FROM documents"
```

---

## Milvus Backup

### Create Snapshot

```bash
# Connect to Milvus
docker-compose exec milvus milvus_cli

# Inside Milvus CLI:
> connect
> show collections
> backup create -n ministry_backup -c ministry_text,ministry_images

# Exit CLI
> exit
```

### Export Collections

```bash
# Export collection data as JSON
docker-compose exec -T milvus python3 <<'EOF'
from pymilvus import Collection

# Export ministry_text collection
collection = Collection("ministry_text")
data = collection.query(expr="", output_fields=["*"])

import json
with open("/var/lib/milvus/backups/ministry_text_export.json", "w") as f:
    json.dump(data, f)

print(f"Exported {len(data)} vectors")
EOF
```

### Scheduled Milvus Backup

```bash
#!/bin/bash
# /opt/rag-qa-hindi/scripts/backup_milvus.sh

BACKUP_DIR="/mnt/backup/milvus"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)

mkdir -p $BACKUP_DIR

# Create Milvus snapshot
docker-compose -f /opt/rag-qa-hindi/docker-compose.yml exec -T milvus milvus_cli <<EOF
connect
backup create -n ministry_backup_$TIMESTAMP -c ministry_text,ministry_images
exit
EOF

echo "✓ Milvus backup created: ministry_backup_$TIMESTAMP"

# Copy backup to persistent storage
docker cp \
    rag-qa-milvus:/var/lib/milvus/backups \
    $BACKUP_DIR/$TIMESTAMP/

# Cleanup old backups
find $BACKUP_DIR -type d -mtime +7 -exec rm -rf {} \;
```

### Milvus Restore

```bash
# Restore from backup
docker-compose exec -T milvus milvus_cli <<EOF
connect
restore -n ministry_backup_20260224_020000
exit
EOF

# Or reimport JSON data if needed
docker-compose exec -T milvus python3 <<'EOF'
import json
from pymilvus import Collection

with open("/var/lib/milvus/backups/ministry_text_export.json") as f:
    data = json.load(f)

collection = Collection("ministry_text")
collection.insert(data)
print(f"Restored {len(data)} vectors")
EOF
```

---

## MinIO Backup

### Bucket Structure (§16 from Shared Contracts)

```
documents/
├── raw/                 # Raw HTML/PDF files
├── processed/           # Extracted text
├── thumbnails/          # Generated thumbnails
└── images/              # Extracted images

models/
├── base/                # Base model weights
├── finetuned/           # Fine-tuned adapters
├── training_data/       # Training datasets
└── eval_data/           # Eval datasets

backups/
├── postgres/
├── milvus/
├── redis/
└── minio/
```

### Full Bucket Backup (using mc)

```bash
# Access MinIO CLI
docker-compose exec minio mc alias set \
    minio-local \
    http://minio:9000 \
    minioadmin \
    $(grep MINIO_SECRET_KEY .env | cut -d= -f2)

# Backup all buckets
docker-compose exec -T minio bash <<'EOF'
BACKUP_DIR="/backups/minio/$(date +%Y%m%d_%H%M%S)"
mkdir -p $BACKUP_DIR

for bucket in documents models backups; do
    echo "Backing up bucket: $bucket"
    mc cp --recursive minio-local/$bucket $BACKUP_DIR/$bucket/
done

echo "✓ MinIO backup complete: $BACKUP_DIR"
EOF
```

### Incremental Sync

```bash
# Mirror documents to backup location (faster than full copy)
docker-compose exec -T minio mc mirror \
    --remove \
    minio-local/documents \
    /mnt/backup/minio/documents

# Or to remote S3
docker-compose exec -T minio mc mirror \
    minio-local/documents \
    s3-remote/rag-qa-backups/documents
```

### MinIO Restore

```bash
# Restore bucket from backup
docker-compose exec -T minio mc cp --recursive \
    /mnt/backup/minio/documents \
    minio-local/documents

# Verify restore
docker-compose exec -T minio mc ls -r minio-local/documents | head -20
```

---

## Redis Backup

### Enable RDB Persistence

```bash
# Verify in docker-compose.yml:
redis:
  command: redis-server --appendonly yes --appendfsync everysec

# This creates:
# - /data/dump.rdb (point-in-time snapshot)
# - /data/appendonly.aof (continuous write log)
```

### Backup RDB File

```bash
# Copy RDB snapshot
docker-compose exec -T redis redis-cli BGSAVE

# Wait for save to complete
docker-compose exec -T redis redis-cli LASTSAVE

# Backup the dump file
cp /mnt/data/redis/dump.rdb /mnt/backup/redis/dump_$(date +%Y%m%d_%H%M%S).rdb

# Verify
ls -lh /mnt/backup/redis/
```

### Redis Restore

```bash
# Stop Redis
docker-compose stop redis

# Copy backup RDB
cp /mnt/backup/redis/dump_20260224_020000.rdb /mnt/data/redis/dump.rdb

# Start Redis (will load from dump.rdb)
docker-compose up -d redis

# Verify
docker-compose exec -T redis redis-cli KEYS "*" | wc -l
```

---

## Complete Backup Script

```bash
#!/bin/bash
# /opt/rag-qa-hindi/scripts/backup_all.sh
# Run daily at 2 AM via crontab

set -e

BACKUP_BASE="/mnt/backup"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
LOG_FILE="/var/log/rag-qa/backup_$TIMESTAMP.log"

mkdir -p $(dirname $LOG_FILE)

{
    echo "=========================================="
    echo "RAG-QA Backup Started: $(date)"
    echo "=========================================="

    # 1. PostgreSQL
    echo -e "\n[1/4] Backing up PostgreSQL..."
    mkdir -p $BACKUP_BASE/postgres
    docker-compose -f /opt/rag-qa-hindi/docker-compose.yml exec -T postgres pg_dump \
        -U ragqa_user \
        -d ragqa \
        --format=custom \
        | gzip > $BACKUP_BASE/postgres/ragqa_$TIMESTAMP.dump.gz
    echo "✓ PostgreSQL backup complete ($(du -h $BACKUP_BASE/postgres/ragqa_$TIMESTAMP.dump.gz | cut -f1))"

    # 2. Milvus
    echo -e "\n[2/4] Backing up Milvus..."
    mkdir -p $BACKUP_BASE/milvus/$TIMESTAMP
    docker-compose -f /opt/rag-qa-hindi/docker-compose.yml exec -T milvus bash -c \
        "cp -r /var/lib/milvus/data $BACKUP_BASE/milvus/$TIMESTAMP/"
    echo "✓ Milvus backup complete"

    # 3. MinIO
    echo -e "\n[3/4] Backing up MinIO..."
    mkdir -p $BACKUP_BASE/minio
    docker-compose -f /opt/rag-qa-hindi/docker-compose.yml exec -T minio mc mirror \
        --remove \
        minio-local/documents \
        $BACKUP_BASE/minio/documents/latest/
    echo "✓ MinIO backup complete"

    # 4. Redis
    echo -e "\n[4/4] Backing up Redis..."
    mkdir -p $BACKUP_BASE/redis
    docker-compose -f /opt/rag-qa-hindi/docker-compose.yml exec -T redis redis-cli BGSAVE
    sleep 5  # Wait for save
    cp /mnt/data/redis/dump.rdb $BACKUP_BASE/redis/dump_$TIMESTAMP.rdb
    echo "✓ Redis backup complete"

    # Cleanup old backups (retention policies)
    echo -e "\n[Cleanup] Removing old backups..."
    find $BACKUP_BASE/postgres -name "*.dump.gz" -mtime +30 -delete
    find $BACKUP_BASE/milvus -type d -mtime +7 -exec rm -rf {} \;
    find $BACKUP_BASE/redis -name "*.rdb" -mtime +1 -delete
    echo "✓ Cleanup complete"

    # Summary
    echo -e "\n=========================================="
    echo "Backup Summary:"
    echo "PostgreSQL: $(du -sh $BACKUP_BASE/postgres | cut -f1)"
    echo "Milvus: $(du -sh $BACKUP_BASE/milvus | cut -f1)"
    echo "MinIO: $(du -sh $BACKUP_BASE/minio | cut -f1)"
    echo "Redis: $(du -sh $BACKUP_BASE/redis | cut -f1)"
    echo "=========================================="
    echo "Backup completed successfully at $(date)"

} 2>&1 | tee -a $LOG_FILE

# Email backup status (optional)
if [ $? -ne 0 ]; then
    SUBJECT="[ERROR] RAG-QA Backup Failed: $TIMESTAMP"
else
    SUBJECT="[OK] RAG-QA Backup Completed: $TIMESTAMP"
fi

# Uncomment to enable email alerts:
# mail -s "$SUBJECT" ops@culture.gov.in < $LOG_FILE
```

### Schedule Backup

```bash
# Add to crontab
crontab -e

# Daily backup at 2 AM
0 2 * * * /opt/rag-qa-hindi/scripts/backup_all.sh

# Verify
crontab -l | grep backup_all
```

---

## Restore Procedures

### Full System Restore

```bash
# 1. Stop all services
docker-compose down

# 2. Restore PostgreSQL
BACKUP_FILE="/mnt/backup/postgres/ragqa_20260224_020000.dump.gz"
gunzip -c $BACKUP_FILE | \
    docker-compose exec -T postgres pg_restore \
    -U ragqa_user \
    -d ragqa \
    --clean \
    --if-exists

# 3. Restore Milvus
cp -r /mnt/backup/milvus/20260224_020000/* /mnt/data/milvus-data/

# 4. Restore MinIO
docker-compose exec -T minio mc mirror \
    /mnt/backup/minio/documents \
    minio-local/documents

# 5. Restore Redis
cp /mnt/backup/redis/dump_20260224_020000.rdb /mnt/data/redis/dump.rdb

# 6. Start services
docker-compose up -d

# 7. Verify
docker-compose exec -T postgres psql -U ragqa_user -d ragqa -c "SELECT count(*) FROM documents"
```

---

## Backup Verification

### Test Restores

```bash
# Monthly: Test full restore to staging environment
docker-compose -f docker-compose.staging.yml down
docker-compose -f docker-compose.staging.yml up -d

# Restore from backup
./scripts/backup_all.sh --restore --from-date 2026-02-20 --target staging

# Verify data integrity
docker-compose -f docker-compose.staging.yml exec -T postgres \
    psql -U ragqa_user -d ragqa \
    -c "SELECT count(*) FROM documents, conversations, feedback"
```

### Backup Integrity Checks

```bash
#!/bin/bash
# Verify backup files are not corrupted

# PostgreSQL dump
gunzip -t /mnt/backup/postgres/ragqa_*.dump.gz

# Milvus data
ls -la /mnt/backup/milvus/*/var/lib/milvus/data/

# MinIO buckets
mc ls -r /mnt/backup/minio/documents | wc -l

# Redis RDB
redis-check-rdb /mnt/backup/redis/dump_*.rdb
```

---

## Disaster Recovery

For complete disaster recovery procedures, see [DISASTER_RECOVERY.md](DISASTER_RECOVERY.md)

**RTO Target:** <4 hours
**RPO Target:** <1 hour

---

**Last Updated:** February 24, 2026
