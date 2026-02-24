---
name: monitor-aws
description: Monitor the RAG-QA platform on AWS. Check service health, view logs, analyze metrics, investigate errors, and troubleshoot performance issues. Use when checking system status, debugging errors, or analyzing performance.
allowed-tools: Bash, Read, Grep, Glob
---

# AWS Monitoring Skill

## Quick Health Check

Check all services are running:
```bash
# ECS service status
aws ecs list-services --cluster ragqa-cluster --region ap-south-1 --query 'serviceArns[*]' --output table
aws ecs describe-services --cluster ragqa-cluster --services ragqa-api-gateway ragqa-rag-service ragqa-llm-service ragqa-chat-widget --region ap-south-1 --query 'services[*].{name:serviceName,status:status,running:runningCount,desired:desiredCount}' --output table
```

Hit each service's health endpoint via API Gateway:
```bash
# From within VPC or via bastion host
curl http://api-gateway.ragqa.local:8000/health
curl http://rag-service.ragqa.local:8001/health
curl http://llm-service.ragqa.local:8002/health
curl http://speech-service.ragqa.local:8003/health
curl http://translation-service.ragqa.local:8004/health
curl http://ocr-service.ragqa.local:8005/health
curl http://data-ingestion.ragqa.local:8006/health
curl http://model-training.ragqa.local:8007/health
```

## View Logs

```bash
# Tail logs for a specific service
aws logs tail /ecs/ragqa-api-gateway --follow --region ap-south-1

# Search logs for errors (last 1 hour)
aws logs filter-log-events --log-group-name /ecs/ragqa-api-gateway --start-time $(date -d '1 hour ago' +%s000) --filter-pattern "ERROR" --region ap-south-1

# Search logs across all services
for svc in api-gateway rag-service llm-service speech-service translation-service ocr-service data-ingestion model-training; do
  echo "=== $svc ==="
  aws logs filter-log-events --log-group-name /ecs/ragqa-$svc --start-time $(date -d '1 hour ago' +%s000) --filter-pattern "ERROR" --max-items 5 --region ap-south-1 --query 'events[*].message' --output text
done
```

## Database Monitoring

```bash
# RDS instance status
aws rds describe-db-instances --db-instance-identifier ragqa-postgres --region ap-south-1 --query 'DBInstances[0].{status:DBInstanceStatus,cpu:PerformanceInsightsEnabled,storage:AllocatedStorage,connections:Endpoint}'

# Active connections (via psql)
psql "$DATABASE_URL" -c "SELECT count(*) as active_connections FROM pg_stat_activity WHERE state = 'active';"

# Slow queries
psql "$DATABASE_URL" -c "SELECT query, calls, mean_exec_time, total_exec_time FROM pg_stat_statements ORDER BY mean_exec_time DESC LIMIT 10;"

# Table sizes
psql "$DATABASE_URL" -c "SELECT relname, pg_size_pretty(pg_total_relation_size(relid)) FROM pg_catalog.pg_statio_user_tables ORDER BY pg_total_relation_size(relid) DESC LIMIT 10;"
```

## Redis Monitoring

```bash
# ElastiCache cluster status
aws elasticache describe-cache-clusters --cache-cluster-id ragqa-redis --show-cache-node-info --region ap-south-1

# Redis memory usage (via redis-cli with SSL)
redis-cli -h <elasticache-endpoint> --tls -p 6379 INFO memory
redis-cli -h <elasticache-endpoint> --tls -p 6379 INFO keyspace
```

## GPU Instance Monitoring

```bash
# Check GPU instances
aws ec2 describe-instances --filters "Name=tag:aws:ecs:cluster-name,Values=ragqa-cluster" "Name=instance-type,Values=g5.2xlarge" --query 'Reservations[*].Instances[*].{id:InstanceId,state:State.Name,type:InstanceType}' --output table --region ap-south-1

# SSH into GPU instance for nvidia-smi
aws ssm start-session --target <instance-id> --region ap-south-1
# Then run: nvidia-smi
```

## S3 Storage Monitoring

```bash
# Bucket sizes
for bucket in ragqa-documents ragqa-models ragqa-backups; do
  echo "=== $bucket ==="
  aws s3 ls s3://$bucket --recursive --summarize 2>/dev/null | tail -2
done
```

## CloudWatch Alarms

```bash
# List active alarms
aws cloudwatch describe-alarms --state-value ALARM --region ap-south-1 --query 'MetricAlarms[*].{name:AlarmName,metric:MetricName,state:StateValue}' --output table

# List all alarms
aws cloudwatch describe-alarms --region ap-south-1 --query 'MetricAlarms[*].{name:AlarmName,state:StateValue}' --output table
```

## ECS Task Debugging

```bash
# List stopped tasks (to find crash reasons)
aws ecs list-tasks --cluster ragqa-cluster --desired-status STOPPED --region ap-south-1

# Describe a stopped task for error details
aws ecs describe-tasks --cluster ragqa-cluster --tasks <task-arn> --region ap-south-1 --query 'tasks[0].{status:lastStatus,reason:stoppedReason,exitCode:containers[0].exitCode}'
```

## Performance Metrics

```bash
# ECS CPU/Memory utilization
aws cloudwatch get-metric-statistics --namespace AWS/ECS --metric-name CPUUtilization --dimensions Name=ClusterName,Value=ragqa-cluster Name=ServiceName,Value=ragqa-api-gateway --start-time $(date -u -d '1 hour ago' +%Y-%m-%dT%H:%M:%S) --end-time $(date -u +%Y-%m-%dT%H:%M:%S) --period 300 --statistics Average --region ap-south-1

# ALB request count and latency
aws cloudwatch get-metric-statistics --namespace AWS/ApplicationELB --metric-name TargetResponseTime --dimensions Name=LoadBalancer,Value=<alb-arn-suffix> --start-time $(date -u -d '1 hour ago' +%Y-%m-%dT%H:%M:%S) --end-time $(date -u +%Y-%m-%dT%H:%M:%S) --period 300 --statistics Average,p99 --region ap-south-1
```

## Grafana & Langfuse Access

- **Grafana:** https://<alb-domain>/grafana (port 3000 internally)
- **Langfuse:** https://<alb-domain>/langfuse (port 3001 internally)
- **Prometheus:** http://prometheus.ragqa.local:9090 (internal only)

## Common Issues

| Symptom | Likely Cause | Investigation |
|---------|-------------|---------------|
| 502 Bad Gateway | Service crashing | Check CloudWatch logs, ECS stopped tasks |
| High latency | LLM cold start / GPU OOM | Check nvidia-smi, vLLM logs |
| Search returns nothing | Milvus down or empty | Check Milvus health, collection count |
| Translation empty | IndicTrans2 not loaded | Check translation-service logs, GPU memory |
| Rate limit errors | Redis connection issue | Check ElastiCache status, Redis connectivity |
