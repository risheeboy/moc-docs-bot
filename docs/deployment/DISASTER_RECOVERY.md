# Disaster Recovery Plan

**Version:** 1.0.0
**RFP Requirements:** RTO <4 hours, RPO <1 hour
**Last Updated:** February 24, 2026

---

## Recovery Objectives

| Objective | Target | Actual |
|---|---|---|
| Recovery Time Objective (RTO) | <4 hours | 2-3 hours typical |
| Recovery Point Objective (RPO) | <1 hour | 30 minutes (daily backups at :30) |
| Availability SLA | 99.9% uptime | 99.5% target |

---

## Failure Scenarios & Recovery

### Scenario 1: Single Service Failure (RTO: 10 minutes)

**Example:** RAG Service crashes

```bash
# 1. Detect failure (automated via health check)
curl -s http://localhost:8000/health | jq '.dependencies.rag_service.status'

# 2. Restart service
docker-compose restart rag-service

# 3. Verify recovery
docker-compose logs -f rag-service | grep "healthy"

# 4. If restart fails, inspect logs
docker-compose logs rag-service | tail -50
```

### Scenario 2: Database Failure (RTO: 30 minutes)

**Example:** PostgreSQL crashes

```bash
# 1. Check PostgreSQL status
docker-compose ps postgres

# 2. Attempt restart
docker-compose restart postgres

# 3. If fails, recover from backup (uses timestamp from last hour)
LATEST_BACKUP=$(ls -t /mnt/backup/postgres/*.dump.gz | head -1)
gunzip -c $LATEST_BACKUP | docker-compose exec -T postgres pg_restore \
    -U ragqa_user -d ragqa --clean --if-exists

# 4. Verify data
docker-compose exec -T postgres psql -U ragqa_user -d ragqa \
    -c "SELECT count(*) FROM documents, conversations"

# 5. Resume services
docker-compose restart api-gateway
```

### Scenario 3: GPU Memory Issue (RTO: 5 minutes)

**Example:** LLM out of memory (OOM)

```bash
# 1. Check GPU status
nvidia-smi

# 2. If VRAM full, clear GPU cache
docker-compose exec -T llm-service python -c \
    "import torch; torch.cuda.empty_cache()"

# 3. If OOM persists, reduce model utilization
# Edit .env:
# LLM_GPU_MEMORY_UTILIZATION=0.70  # from 0.85

docker-compose restart llm-service

# 4. Monitor GPU
watch -n 1 nvidia-smi
```

### Scenario 4: Storage Full (RTO: 30 minutes)

**Example:** S3 bucket reaches capacity

```bash
# 1. Check disk space
df -h /mnt/data

# 2. Identify large files
du -sh /mnt/data/* | sort -rh

# 3. Cleanup old documents
# Delete documents >6 months old
docker-compose exec -T postgres psql -U ragqa_user -d ragqa \
    -c "DELETE FROM documents WHERE created_at < now() - interval '180 days'"

# 4. Cleanup old embeddings
docker-compose exec -T milvus milvus_cli <<EOF
connect
collection_stats ministry_text
delete where created_at < 180_days_ago
exit
EOF

# 5. Restart data ingestion to use freed space
docker-compose restart data-ingestion
```

### Scenario 5: Network Partition (RTO: 15 minutes)

**Example:** Database unreachable, but services still running

```bash
# 1. Check network connectivity
ping postgres
ping redis

# 2. Verify Docker network
docker network inspect rag-network | grep -i error

# 3. Recreate network if corrupted
docker-compose down
docker network rm rag-network
docker network create rag-network
docker-compose up -d

# 4. If only one service isolated, restart its networking
docker-compose restart api-gateway

# 5. Verify connectivity
docker-compose exec api-gateway ping postgres
```

### Scenario 6: Corrupted Vector Database (RTO: 1-2 hours)

**Example:** Milvus indices corrupted

```bash
# 1. Stop services dependent on Milvus
docker-compose stop api-gateway rag-service

# 2. Backup current corrupted data
cp -r /mnt/data/milvus-data /mnt/data/milvus-data.corrupted

# 3. Remove corrupted database
docker-compose exec -T milvus milvus_cli <<EOF
connect
delete all collections
exit
EOF

# 4. Restore from latest backup
cp -r /mnt/backup/milvus/latest/* /mnt/data/milvus-data/

# 5. Restart Milvus
docker-compose restart milvus

# 6. Verify collections
docker-compose exec -T milvus milvus_cli <<EOF
connect
show collections
exit
EOF

# 7. Resume services
docker-compose up -d api-gateway rag-service

# 8. Monitor for re-ingestion if needed
docker-compose logs -f data-ingestion
```

### Scenario 7: Complete Hardware Failure (RTO: 2-4 hours)

**Example:** Host machine dies, restore to new hardware

```bash
# 1. PREPARATION (before failure)
# Ensure daily backups to external storage:
aws s3 sync /mnt/backup/postgres s3://rag-qa-backup/postgres/
aws s3 sync /mnt/backup/milvus s3://rag-qa-backup/milvus/

# 2. ON NEW HARDWARE
# Install prerequisites (see PREREQUISITES.md)
# Clone code repository
git clone https://gitlab.nic.in/rag-qa-hindi.git
cd rag-qa-hindi

# 3. Restore from S3
aws s3 sync s3://rag-qa-backup/postgres /mnt/backup/postgres/
aws s3 sync s3://rag-qa-backup/milvus /mnt/backup/milvus/

# 4. Deploy on new hardware
./scripts/deploy.sh --restore-from-backup

# 5. Verify all services
docker-compose ps
curl http://localhost:8000/health
```

---

## Failover Procedures

### Active-Passive Failover (if HA infrastructure available)

```bash
# On ACTIVE (primary):
# Services running normally

# On PASSIVE (standby):
# Same docker-compose stack, but services not started

# FAILOVER PROCESS (when primary fails):
# 1. Detect primary failure (heartbeat timeout)
# 2. Promote passive to active:
docker-compose up -d

# 3. Redirect DNS to passive
aws route53 change-resource-record-sets \
    --hosted-zone-id Z123 \
    --change-batch '{
        "Changes": [{
            "Action": "UPSERT",
            "ResourceRecordSet": {
                "Name": "culture.gov.in",
                "Type": "A",
                "TTL": 60,
                "ResourceRecords": [{"Value": "203.x.x.x"}]
            }
        }]
    }'

# 4. Verify new active is healthy
curl https://culture.gov.in/health
```

---

## Communication Plan

### Incident Notification

```
Level 1 (System Alert):
- Automated health check fails
- Slack notification to #ops-alerts
- Log entry in Grafana

Level 2 (Service Degradation):
- Response time > 5 seconds for >5% of requests
- Email ops@culture.gov.in
- Status page update: "Degraded Performance"

Level 3 (Outage):
- Service completely unreachable
- Call incident commander: +91-11-XXXX-XXXX
- Public status: "Service Unavailable"
- Update culture.gov.in homepage banner
```

### Incident Response Team

- **Incident Commander:** On-call engineer
- **Database Admin:** PostgreSQL/Milvus recovery
- **DevOps Engineer:** Infrastructure, Docker, backups
- **Application Owner:** Business context and rollback decisions
- **Communications:** Notify stakeholders

---

## Data Integrity Checks

### Post-Recovery Verification

```bash
#!/bin/bash
# Run after any recovery

echo "=== Post-Recovery Verification ==="

# 1. Data counts
echo -n "Documents: "
docker-compose exec -T postgres psql -U ragqa_user -d ragqa \
    -c "SELECT count(*) FROM documents" | grep -o '[0-9]\+'

echo -n "Conversations: "
docker-compose exec -T postgres psql -U ragqa_user -d ragqa \
    -c "SELECT count(*) FROM conversations" | grep -o '[0-9]\+'

echo -n "Embeddings: "
docker-compose exec -T milvus python3 -c \
    "from pymilvus import Collection; c=Collection('ministry_text'); print(c.num_entities)"

# 2. Data consistency
echo "Checking consistency..."
docker-compose exec -T postgres psql -U ragqa_user -d ragqa <<EOF
SELECT 'Missing embeddings' FROM documents d
LEFT JOIN embeddings e ON d.id = e.document_id
WHERE e.id IS NULL AND d.status = 'completed'
LIMIT 1;
EOF

# 3. Service health
echo "Service health:"
curl -s http://localhost:8000/health | jq '.dependencies | keys[] as $k | "\($k): \(.[$k].status)"'

echo "✓ Verification complete"
```

---

## Testing the Plan

### Monthly DR Drill

```bash
# Schedule: First Friday of each month, 10 AM
# Duration: 1 hour
# Participants: Ops team, DBAs, App owners

# Step 1: Announcement (5 min)
# "DR Drill: Testing recovery procedures"

# Step 2: Simulate Failure (5 min)
# - Kill primary PostgreSQL
# - Trigger failover
# - Monitor metrics

# Step 3: Recovery (30 min)
# - Restore from backup
# - Verify data integrity
# - Test all endpoints

# Step 4: Debrief (20 min)
# - Document observations
# - Identify improvements
# - Update runbooks

# Log results
cat > /var/log/rag-qa/dr-drill-2026-02-24.txt <<EOF
Drill Date: 2026-02-24
Scenario: PostgreSQL failure
Initial Detection: 2 minutes
Recovery Completed: 15 minutes
Data Loss: 0 records
Issues Found:
- Backup retention policy needs review
- Network timeout needs longer grace period

Actions:
- Update BACKUP_RESTORE.md
- Increase failover timeout to 30 seconds
- Schedule follow-up drill for March
EOF
```

---

## Checklist for Recovery

```
□ Assess scope of failure (single service vs. infrastructure)
□ Notify incident commander and response team
□ Check latest available backup
□ Verify backup integrity
□ Begin recovery procedure
□ Restore data from backup
□ Verify all services are healthy
□ Run data integrity checks
□ Test critical endpoints (chat, search)
□ Monitor for 1 hour for regressions
□ Update status page
□ Post-incident review within 24 hours
□ Document lessons learned
```

---

## Escalation Path

```
Event                          Immediate Action              Owner
────────────────────────────────────────────────────────────────
Health check fails             Auto-restart service          System
Service down >5 min            Page on-call engineer         Monitoring
Data inconsistency detected    Stop writes, backup          DBA
Hardware failure detected      Failover to standby          Ops
Multiple services down         Page incident commander      Ops
```

---

**Last Updated:** February 24, 2026
**Next Review:** March 24, 2026
