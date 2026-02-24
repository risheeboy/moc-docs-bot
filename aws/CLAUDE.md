# AWS Infrastructure

Terraform-managed deployment. VPC, RDS PostgreSQL 16, ElastiCache Redis, S3, ECS Fargate, ALB, ECR, CloudWatch, Secrets Manager, Cloud Map.

## Key Files

- `deploy.sh` — One-click deploy (build, push ECR, terraform apply, migrate DB)
- `destroy.sh` — One-click destroy (with confirmation, preserves RDS snapshots)
- `build-and-push.sh` — Docker build + ECR push
- `terraform/main.tf` — VPC, networking (10.0.0.0/16)
- `terraform/ecs.tf` — ECS Fargate cluster, task definitions
- `terraform/rds.tf` — PostgreSQL 16 Multi-AZ, automated backups
- `terraform/elasticache.tf` — Redis Multi-AZ, auto-failover
- `terraform/s3.tf` — 3 buckets (documents, models, backups)
- `terraform/alb.tf` — Application Load Balancer, target groups
- `terraform/ecr.tf` — Container registries (one per service)
- `terraform/iam.tf` — IAM roles for ECS S3 access
- `terraform/cloudwatch.tf` — Logs, alarms, metrics
- `ecs/task-definitions/` — Service definitions (JSON)

## Infrastructure

- **Region:** ap-south-1 (Mumbai)
- **Subnets:** 2 public (ALB, NAT), 2 private (services, DBs)
- **Security Groups:** ALB, ECS, RDS, ElastiCache
- **Compute:** ECS Fargate + EC2 g5.2xlarge (GPU)
- **Database:** RDS PostgreSQL 16 Multi-AZ, 30-day backups
- **Cache:** ElastiCache Redis Multi-AZ
- **Storage:** S3 (documents, models, backups), versioning enabled
- **Service Discovery:** Cloud Map namespace `ragqa.local`
- **Monitoring:** CloudWatch Logs, Alarms, Prometheus

## Deployment

```bash
cd aws
./deploy.sh       # One-click (build, push, terraform, migrate)
./destroy.sh      # One-click destroy (with safety confirmation)
```

## Configuration

- `terraform/terraform.tfvars` — AWS region, environment, VPC CIDR, RDS storage, ALB port
- Task definitions: CPU, memory, env vars, log routing
- IAM roles: ECS → S3 permissions

## Scaling

- ECS auto-scaling: 70% CPU target
- RDS storage auto-scaling: enabled
- CloudWatch alarms: SNS on high error rate

## Known Issues

1. **build-and-push.sh path errors** — Uses wrong paths (services/api-gateway instead of api-gateway).
2. **No HTTPS** — ALB listens on HTTP only.
3. **Hardcoded secrets** — Some in task definitions instead of Secrets Manager.
4. **No CI/CD** — Manual deploy script, no pre-deploy testing.
