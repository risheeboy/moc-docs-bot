---
description: AWS Terraform and deployment rules
paths:
  - "aws/**/*.tf"
  - "aws/**/*.sh"
  - "aws/**/*.json"
---

# AWS Infrastructure Rules

## Core Configuration

- **Region:** ap-south-1 (Mumbai)
- **VPC CIDR:** 10.0.0.0/16 with 2 public + 2 private subnets
- **Service discovery:** Cloud Map namespace `ragqa.local`
- **Secrets:** AWS Secrets Manager (never hardcode)

## Compute

- **ECS Fargate:** Most services (0.5-2 vCPU, 512MB-4GB RAM)
- **EC2 g5.2xlarge:** GPU instances for LLM, Speech, Translation, Model Training
- **Auto Scaling:** 1-4 GPU instances based on queue depth

## Managed Services

- **RDS PostgreSQL 16:** Multi-AZ, 30-day automated backups, SSL encrypted
- **ElastiCache Redis 7.x:** Multi-AZ, password-protected, auto-failover
- **S3 Buckets:**
  - `ragqa-documents` — Scraped documents, PDFs, images
  - `ragqa-models` — Fine-tuned model checkpoints
  - `ragqa-backups` — PostgreSQL backups, config snapshots

## Networking

- All services in private subnets
- Public ALB exposes frontends only (Chat Widget, Search Page, Admin Dashboard)
- API Gateway accessible only inside VPC via internal ALB
- Security groups: api-gateway-sg, rag-service-sg, public-alb-sg, database-sg

## Terraform

- State: configure remote backend before production
- Files: `aws/terraform/*.tf` (complete IaC)
- Variables: `aws/terraform/terraform.tfvars`

## Deployment

```bash
# One-click: builds, pushes ECR, applies Terraform, runs migrations
cd aws
./deploy.sh

# Destroy with safety confirmation
./destroy.sh

# View logs
aws logs tail /ecs/ragqa-[service-name] --follow

# SSH into GPU instance
aws ssm start-session --target <instance-id>
```

## ECS Task Definitions

- Located: `aws/ecs/task-definitions/*.json`
- Env vars, resource limits, log routing configured here
- Update via `aws/deploy.sh` (do not manually edit)

## IAM Roles

- Services: assume role for S3 access (credentials via STS)
- No hardcoded access keys in code or containers
