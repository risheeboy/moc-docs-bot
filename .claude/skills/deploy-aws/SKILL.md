---
name: deploy-aws
description: Deploy the RAG-QA platform to AWS. Handles Terraform infrastructure, Docker image builds, ECR pushes, ECS service updates, and database migrations. Use when deploying, updating, or troubleshooting AWS infrastructure.
allowed-tools: Bash, Read, Edit, Write, Glob, Grep
---

# AWS Deployment Skill

## Prerequisites Check

Before deploying, verify:
1. AWS CLI configured: `aws sts get-caller-identity`
2. Terraform installed: `terraform --version` (need 1.6+)
3. Docker running: `docker info`
4. ECR login: `aws ecr get-login-password --region ap-south-1 | docker login --username AWS --password-stdin <account-id>.dkr.ecr.ap-south-1.amazonaws.com`

## Full Deployment

Run the one-click deployment:
```bash
cd /sessions/amazing-wizardly-wright/mnt/rag-qa-hindi/aws && ./deploy.sh
```

This script:
1. Validates Terraform configuration
2. Applies infrastructure (VPC, RDS, ElastiCache, S3, ECS, ALB, IAM)
3. Builds Docker images for all 13 services
4. Pushes images to ECR
5. Runs database migrations against RDS
6. Updates ECS task definitions
7. Health-checks all services

## Individual Service Deployment

To deploy a single service without full infrastructure update:

```bash
# Build and push one service
SERVICE=api-gateway
cd /sessions/amazing-wizardly-wright/mnt/rag-qa-hindi
docker build -t ragqa-${SERVICE}:latest ./${SERVICE}/
aws ecr get-login-password --region ap-south-1 | docker login --username AWS --password-stdin $(aws sts get-caller-identity --query Account --output text).dkr.ecr.ap-south-1.amazonaws.com
docker tag ragqa-${SERVICE}:latest $(aws sts get-caller-identity --query Account --output text).dkr.ecr.ap-south-1.amazonaws.com/ragqa-${SERVICE}:latest
docker push $(aws sts get-caller-identity --query Account --output text).dkr.ecr.ap-south-1.amazonaws.com/ragqa-${SERVICE}:latest

# Force new deployment
aws ecs update-service --cluster ragqa-cluster --service ragqa-${SERVICE} --force-new-deployment --region ap-south-1
```

## Infrastructure Only

```bash
cd /sessions/amazing-wizardly-wright/mnt/rag-qa-hindi/aws/terraform
terraform init
terraform plan -var-file=terraform.tfvars
terraform apply -var-file=terraform.tfvars -auto-approve
```

## Database Migrations Only

```bash
cd /sessions/amazing-wizardly-wright/mnt/rag-qa-hindi/aws/scripts
./run-migrations.sh
```

## Rollback

To roll back a service to previous version:
```bash
# List previous task definition revisions
aws ecs list-task-definitions --family-prefix ragqa-api-gateway --sort DESC --max-items 5 --region ap-south-1

# Update service to previous revision
aws ecs update-service --cluster ragqa-cluster --service ragqa-api-gateway --task-definition ragqa-api-gateway:<previous-revision> --region ap-south-1
```

## Destroy Infrastructure

```bash
cd /sessions/amazing-wizardly-wright/mnt/rag-qa-hindi/aws && ./destroy.sh
```

## Key Configuration Files

- `aws/terraform/terraform.tfvars.example` — Copy to terraform.tfvars and fill in values
- `aws/terraform/variables.tf` — All configurable parameters
- `aws/ecs/task-definitions/*.json` — Service container definitions
- `aws/terraform/security_groups.tf` — Network security rules

## Troubleshooting

- **ECS service won't start:** Check CloudWatch logs at `/ecs/ragqa-<service>`
- **RDS connection failed:** Verify security group allows port 5432 from ECS tasks
- **S3 access denied:** Check IAM role has s3:GetObject, s3:PutObject on ragqa-* buckets
- **ALB health check failing:** Service must respond 200 on GET /health within 30s
- **GPU instance not launching:** Check g5.2xlarge quota in ap-south-1
