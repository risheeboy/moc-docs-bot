# RAG QA Hindi - AWS ECS Deployment Guide

Complete guide for deploying the RAG-based Hindi QA system on AWS using ECS with Fargate and EC2 GPU instances.

## Table of Contents

- [Architecture Overview](#architecture-overview)
- [Prerequisites](#prerequisites)
- [Configuration](#configuration)
- [One-Click Deployment](#one-click-deployment)
- [Accessing the Application](#accessing-the-application)
- [Monitoring](#monitoring)
- [Backup and Restore](#backup-and-restore)
- [Cost Estimation](#cost-estimation)
- [Troubleshooting](#troubleshooting)
- [Teardown](#teardown)

## Architecture Overview

### System Components

The deployment consists of multiple service tiers:

```
┌─────────────────────────────────────────────────────────────┐
│                    Internet / Load Balancer                  │
│                        (ALB Port 80)                         │
└────────────────────┬────────────────────────────────────────┘
                     │
        ┌────────────┼────────────┐
        │            │            │
    ┌───▼────┐  ┌───▼────┐  ┌───▼────┐
    │ Chat   │  │ Search │  │ Admin  │
    │ Widget │  │ Page   │  │ Dash   │
    │(0.5vCPU)│ │(0.5vCPU)│ │(0.5vCPU)│
    └────────┘  └────────┘  └────────┘
        │            │            │
        └────────────┬────────────┘
                     │
                ┌────▼─────────────────────────────────────────┐
                │      ECS Cluster (VPC)                       │
                │  Cloud Map Service Discovery (ragqa.local)  │
                │                                              │
    ┌───────────┼────────────────────────────────────────┐    │
    │           │                                        │    │
┌───▼───┐   ┌───▼────────┐   ┌────────────────────┐     │    │
│ API   │   │ RAG Service│   │ Data Ingestion     │     │    │
│Gateway│   │(4vCPU,16GB)│   │(2vCPU, 4GB)        │     │    │
│(2vCPU)│   └────────────┘   └────────────────────┘     │    │
└───────┘   ┌──────────────────────┐                     │    │
            │ Milvus Vector DB     │                     │    │
            │(4vCPU, 16GB + EFS)   │                     │    │
            └──────────────────────┘                     │    │
            ┌──────────────────────┐                     │    │
            │ Langfuse Observ.     │                     │    │
            │(1vCPU, 2GB)          │                     │    │
            └──────────────────────┘                     │    │
    │                                        │    │
    └────────────────────────────────────────┘    │
                     │
         ┌───────────┼───────────┬───────────┐    │
         │           │           │           │    │
    ┌────▼──┐   ┌───▼──┐   ┌───▼──┐   ┌───▼──┐  │
    │LLM    │   │Speech│   │Trans │   │OCR   │  │
    │Service│   │Svc   │   │Svc   │   │Svc   │  │
    │(GPU)  │   │(GPU) │   │(GPU) │   │      │  │
    │EC2    │   │EC2   │   │EC2   │   │      │  │
    └───────┘   └──────┘   └──────┘   └──────┘  │
                                                 │
    ┌──────────────────────────────────────────┐ │
    │   Infrastructure Services (Fargate)      │ │
    │  - Prometheus (9090)                     │ │
    │  - Grafana (3000)                        │ │
    │  - PostgreSQL (via RDS)                  │ │
    │  - Redis (via ElastiCache)               │ │
    └──────────────────────────────────────────┘ │
    └─────────────────────────────────────────────┘
            │
    ┌───────┴─────────────────┐
    │                         │
┌───▼─────┐            ┌─────▼────┐
│   RDS   │            │ElastiCache│
│PostgreSQL            │  Redis    │
└─────────┘            └──────────┘
```

### Service Specifications

#### Fargate Services (No GPU required)

| Service | CPU | Memory | Instances | Port | Description |
|---------|-----|--------|-----------|------|-------------|
| api-gateway | 2 vCPU | 4 GB | 2 | 8000 | API gateway and routing |
| rag-service | 4 vCPU | 16 GB | 1 | 8001 | RAG retrieval engine |
| ocr-service | 2 vCPU | 8 GB | 1 | 8005 | Document OCR processing |
| data-ingestion | 2 vCPU | 4 GB | 1 | 8006 | Web scraping and document ingestion |
| chat-widget | 0.5 vCPU | 1 GB | 2 | 80 | Chat interface frontend |
| search-page | 0.5 vCPU | 1 GB | 2 | 80 | Search UI frontend |
| admin-dashboard | 0.5 vCPU | 1 GB | 2 | 80 | Admin panel frontend |
| milvus | 4 vCPU | 16 GB | 1 | 19530 | Vector database |
| langfuse | 1 vCPU | 2 GB | 1 | 3001 | LLM observability |
| grafana | 0.5 vCPU | 1 GB | 1 | 3000 | Monitoring dashboards |
| prometheus | 0.5 vCPU | 1 GB | 1 | 9090 | Metrics collection |

#### EC2 GPU Services (g5.2xlarge instances)

| Service | GPU | Port | Instances | Description |
|---------|-----|------|-----------|-------------|
| llm-service | 1x NVIDIA A100 | 8002 | 1 | LLM inference engine |
| speech-service | 1x NVIDIA A100 | 8003 | 1 | Speech-to-text and TTS |
| translation-service | 1x NVIDIA A100 | 8004 | 1 | IndicTrans2 translation |
| model-training | 1x NVIDIA A100 | 8007 | 0* | Model fine-tuning |

*model-training starts with 0 instances and scales up on demand.

### Infrastructure Components

- **VPC**: Custom VPC with public/private subnets across 2 AZs
- **Load Balancer**: Application Load Balancer with path-based routing
- **RDS**: PostgreSQL 16 on db.r6g.xlarge
- **ElastiCache**: Redis cluster on cache.r6g.xlarge
- **EFS**: Shared storage for models and document uploads
- **Service Discovery**: AWS Cloud Map private DNS namespace (ragqa.local)
- **Logging**: CloudWatch Logs with log groups per service

## Prerequisites

### AWS Account Requirements

- AWS account with appropriate permissions (EC2, ECS, RDS, ElastiCache, VPC, IAM, S3, ECR)
- VPC quotas for the services (default usually sufficient)
- EC2 quota for g5.2xlarge instances (may need quota increase)
- S3 bucket for Terraform state (create manually or use provided script)

### Local Requirements

- **AWS CLI** v2.x or later
- **Terraform** v1.5 or later
- **Docker** 20.10 or later
- **jq** for JSON processing
- **Git** for cloning the repository

### Installation

```bash
# macOS (using Homebrew)
brew install awscli terraform docker jq

# Ubuntu/Debian
sudo apt-get install -y awscli terraform docker.io jq

# Verify installations
aws --version
terraform --version
docker --version
jq --version
```

### AWS Credentials

Configure AWS credentials:

```bash
aws configure

# Or set environment variables
export AWS_ACCESS_KEY_ID="your-access-key"
export AWS_SECRET_ACCESS_KEY="your-secret-key"
export AWS_DEFAULT_REGION="ap-south-1"
```

### Terraform Backend Setup

Create S3 bucket and DynamoDB table for Terraform state:

```bash
# Set variables
export TERRAFORM_BUCKET="ragqa-terraform-state"
export TERRAFORM_REGION="ap-south-1"

# Create S3 bucket
aws s3api create-bucket \
    --bucket $TERRAFORM_BUCKET \
    --region $TERRAFORM_REGION \
    --create-bucket-configuration LocationConstraint=$TERRAFORM_REGION

# Enable versioning
aws s3api put-bucket-versioning \
    --bucket $TERRAFORM_BUCKET \
    --versioning-configuration Status=Enabled

# Enable server-side encryption
aws s3api put-bucket-encryption \
    --bucket $TERRAFORM_BUCKET \
    --server-side-encryption-configuration '{
        "Rules": [{
            "ApplyServerSideEncryptionByDefault": {
                "SSEAlgorithm": "AES256"
            }
        }]
    }'

# Create DynamoDB table for locks
aws dynamodb create-table \
    --table-name ragqa-terraform-locks \
    --attribute-definitions AttributeName=LockID,AttributeType=S \
    --key-schema AttributeName=LockID,KeyType=HASH \
    --provisioned-throughput ReadCapacityUnits=5,WriteCapacityUnits=5 \
    --region $TERRAFORM_REGION
```

## Configuration

### Step 1: Prepare Configuration Files

Navigate to the Terraform directory:

```bash
cd /path/to/rag-qa-hindi/aws/terraform
```

Create or edit `terraform.tfvars`:

```hcl
aws_region     = "ap-south-1"
environment    = "production"
project_name   = "ragqa"

# Network Configuration
vpc_cidr           = "10.0.0.0/16"
private_subnets   = ["10.0.1.0/24", "10.0.2.0/24"]
public_subnets    = ["10.0.101.0/24", "10.0.102.0/24"]
availability_zones = ["ap-south-1a", "ap-south-1b"]

# RDS Configuration
rds_engine_version    = "16.0"
rds_instance_class    = "db.r6g.xlarge"
rds_allocated_storage = 100

# ElastiCache Configuration
elasticache_node_type       = "cache.r6g.xlarge"
elasticache_num_cache_nodes = 1

# ECS Configuration
fargate_instance_count = 1
ec2_instance_count     = 1
ec2_instance_type      = "g5.2xlarge"

# Container Configuration
image_tag = "latest"
```

### Step 2: Create AWS Secrets

Store sensitive configuration in AWS Secrets Manager:

```bash
# Create secrets for various components
aws secretsmanager create-secret \
    --name ragqa/app-secret-key \
    --secret-string "$(openssl rand -base64 32)" \
    --region ap-south-1

aws secretsmanager create-secret \
    --name ragqa/jwt-secret-key \
    --secret-string "$(openssl rand -base64 32)" \
    --region ap-south-1

aws secretsmanager create-secret \
    --name ragqa/postgres-password \
    --secret-string "$(openssl rand -base64 32)" \
    --region ap-south-1

aws secretsmanager create-secret \
    --name ragqa/redis-password \
    --secret-string "$(openssl rand -base64 32)" \
    --region ap-south-1

aws secretsmanager create-secret \
    --name ragqa/grafana-admin-password \
    --secret-string "$(openssl rand -base64 32)" \
    --region ap-south-1

# For Langfuse
aws secretsmanager create-secret \
    --name ragqa/langfuse-nextauth-secret \
    --secret-string "$(openssl rand -base64 32)" \
    --region ap-south-1

aws secretsmanager create-secret \
    --name ragqa/langfuse-salt \
    --secret-string "$(openssl rand -base64 32)" \
    --region ap-south-1
```

## One-Click Deployment

### Basic Deployment

```bash
cd /path/to/rag-qa-hindi/aws

# Deploy to production (default)
./deploy.sh production apply

# Deploy to staging
./deploy.sh staging apply

# Deploy with custom image tag
IMAGE_TAG="v1.0.0" ./deploy.sh production apply
```

### Deployment Process

The deployment script performs these steps:

1. **Prerequisite Checks** - Verifies AWS CLI, Terraform, Docker are installed
2. **Configuration Loading** - Loads terraform.tfvars or prompts for values
3. **Terraform Validation** - Validates Terraform configuration
4. **Terraform Planning** - Creates deployment plan
5. **Terraform Apply** - Creates AWS infrastructure
6. **Infrastructure Ready Check** - Waits for resources to be available
7. **Task Definition Registration** - Registers ECS task definitions
8. **Docker Build & Push** - Builds and pushes images to ECR
9. **Database Migrations** - Runs database schema migrations
10. **Data Seeding** - Seeds initial roles, permissions, and targets
11. **Service Health Check** - Waits for services to become healthy
12. **Summary** - Prints deployment summary with URLs

### Deployment Logs

Deployment logs are saved to:
```
/path/to/rag-qa-hindi/aws/deployment-YYYYMMDD-HHMMSS.log
```

### Troubleshooting Deployments

If deployment fails at any step:

1. **Check logs** - Review the deployment log file
2. **Verify prerequisites** - Run prerequisite checks manually
3. **Check AWS console** - Verify resources in AWS Management Console
4. **Review error messages** - Look for specific error details
5. **Retry with verbose output** - Add debugging flags

## Accessing the Application

### Get Application URL

After deployment, retrieve the ALB URL:

```bash
cd /path/to/rag-qa-hindi/aws/terraform

# Get the ALB DNS name
terraform output alb_dns_name

# Example output:
# ragqa-alb-1234567890.ap-south-1.elb.amazonaws.com
```

### Service Access Points

| Service | URL | Purpose |
|---------|-----|---------|
| API Gateway | http://alb-dns/api | REST API endpoints |
| Chat Widget | http://alb-dns/widget | Chat interface |
| Search Page | http://alb-dns/search | Document search UI |
| Admin Dashboard | http://alb-dns/admin | Administration panel |
| Grafana | http://alb-dns/grafana | Monitoring dashboards |
| Prometheus | http://alb-dns/prometheus | Metrics scraper |
| Langfuse | http://alb-dns/langfuse | LLM observability |

### Default Credentials

- **Grafana Admin Username**: admin
- **Grafana Admin Password**: Check AWS Secrets Manager (ragqa/grafana-admin-password)

## Monitoring

### CloudWatch Logs

Access logs for each service:

```bash
# View logs for API Gateway
aws logs tail /ecs/ragqa-api-gateway --follow --region ap-south-1

# View logs for RAG Service
aws logs tail /ecs/ragqa-rag-service --follow --region ap-south-1

# View logs for specific time range
aws logs tail /ecs/ragqa-api-gateway --since 1h --region ap-south-1
```

### Grafana Dashboards

Grafana is pre-configured with Prometheus as data source:

1. Access Grafana at http://alb-dns/grafana
2. Log in with admin credentials
3. Import dashboards from provisioning directory
4. Create custom dashboards for your metrics

### Prometheus Metrics

Prometheus scrapes metrics from:
- ECS services (port 9090 on each task)
- EC2 instances (node exporter)
- RDS (CloudWatch)
- ECS cluster metrics

### CloudWatch Alarms

Create alarms for critical services:

```bash
# Example: High CPU utilization on API Gateway
aws cloudwatch put-metric-alarm \
    --alarm-name ragqa-api-gateway-high-cpu \
    --alarm-description "Alert when API Gateway CPU > 80%" \
    --metric-name CPUUtilization \
    --namespace AWS/ECS \
    --statistic Average \
    --period 300 \
    --threshold 80 \
    --comparison-operator GreaterThanThreshold \
    --evaluation-periods 2 \
    --region ap-south-1
```

## Backup and Restore

### RDS Backups

Automated backups are enabled with 7-day retention:

```bash
# List available snapshots
aws rds describe-db-snapshots \
    --db-instance-identifier ragqa-postgres \
    --region ap-south-1

# Create manual snapshot
aws rds create-db-snapshot \
    --db-instance-identifier ragqa-postgres \
    --db-snapshot-identifier ragqa-postgres-manual-$(date +%Y%m%d) \
    --region ap-south-1

# Restore from snapshot
aws rds restore-db-instance-from-db-snapshot \
    --db-instance-identifier ragqa-postgres-restore \
    --db-snapshot-identifier ragqa-postgres-manual-YYYYMMDD \
    --region ap-south-1
```

### EFS Backups

Backup EFS for models and uploads:

```bash
# Create backup of EFS
aws efs create-backup-vault \
    --backup-vault-name ragqa-efs-backup \
    --region ap-south-1

# Create backup
aws efs start-backup-job \
    --file-system-id fs-xxxxxxxx \
    --backup-vault-name ragqa-efs-backup \
    --region ap-south-1
```

### Database Export

Export RDS data:

```bash
aws rds start-export-task \
    --export-task-identifier ragqa-export-$(date +%Y%m%d) \
    --source-arn arn:aws:rds:ap-south-1:ACCOUNT_ID:db:ragqa-postgres \
    --s3-bucket-name ragqa-exports \
    --s3-prefix database-exports/ \
    --iam-role-arn arn:aws:iam::ACCOUNT_ID:role/RDSExportRole \
    --region ap-south-1
```

## Cost Estimation

### Monthly Service Costs (Approximate)

Based on production configuration with 1 month usage:

#### Compute
- ECS Fargate (services): ~$500-700
- EC2 (GPU instances g5.2xlarge): ~$2,000-2,500
- **Subtotal**: ~$2,500-3,200

#### Database
- RDS PostgreSQL (db.r6g.xlarge): ~$400-500
- Automated backups: ~$50
- **Subtotal**: ~$450-550

#### Caching
- ElastiCache Redis (cache.r6g.xlarge): ~$300-400
- **Subtotal**: ~$300-400

#### Storage
- EFS (standard): ~$0.30/GB/month (~$30-50 for 100-150GB)
- S3 (Terraform state, backups): ~$5-10
- **Subtotal**: ~$35-60

#### Networking
- Load Balancer: ~$18 + data transfer
- NAT Gateway: ~$30 + data transfer
- CloudWatch Logs (ingestion): ~$0.50/GB
- **Subtotal**: ~$50-100

#### Monitoring
- CloudWatch: ~$10-20
- **Subtotal**: ~$10-20

### Total Monthly Cost: ~$3,345-4,230

### Cost Optimization

1. **Use Savings Plans** - 1-year or 3-year commitment for 15-30% discount
2. **Reserved Instances** - For steady-state EC2 workloads
3. **Spot Instances** - For training jobs (up to 70% discount)
4. **Scale Down** - Reduce instance counts in non-production
5. **Right-sizing** - Adjust CPU/memory based on actual usage
6. **Data Transfer** - Minimize cross-region transfers

## Troubleshooting

### Common Issues

#### 1. Deployment Fails with Terraform Errors

**Symptom**: `terraform plan` or `terraform apply` fails

**Solutions**:
```bash
# Reinitialize Terraform
cd terraform
terraform init -upgrade

# Validate configuration
terraform validate

# Check state
terraform state list
terraform state show
```

#### 2. ECS Services Not Starting

**Symptom**: Tasks fail to start or keep stopping

**Solutions**:
```bash
# Check task definitions
aws ecs describe-task-definition \
    --task-definition ragqa-api-gateway:1 \
    --region ap-south-1

# Check service events
aws ecs describe-services \
    --cluster ragqa-cluster \
    --services ragqa-api-gateway \
    --region ap-south-1

# View task logs
aws logs tail /ecs/ragqa-api-gateway --follow
```

#### 3. Database Connection Errors

**Symptom**: Services can't connect to RDS

**Solutions**:
```bash
# Verify RDS is accessible
aws rds describe-db-instances \
    --db-instance-identifier ragqa-postgres \
    --region ap-south-1

# Check security group rules
aws ec2 describe-security-groups \
    --group-ids sg-xxxxxxxx \
    --region ap-south-1

# Test connectivity from bastion or service
psql -h ragqa-postgres.XXXX.ap-south-1.rds.amazonaws.com \
     -U postgres -d ragqa
```

#### 4. High CPU or Memory Usage

**Symptom**: Services running with high resource utilization

**Solutions**:
```bash
# Check CloudWatch metrics
aws cloudwatch get-metric-statistics \
    --namespace AWS/ECS \
    --metric-name CPUUtilization \
    --dimensions Name=ServiceName,Value=ragqa-api-gateway \
    --statistics Average,Maximum \
    --start-time 2024-01-01T00:00:00Z \
    --end-time 2024-01-02T00:00:00Z \
    --period 300 \
    --region ap-south-1

# Scale up service
aws ecs update-service \
    --cluster ragqa-cluster \
    --service ragqa-api-gateway \
    --desired-count 4 \
    --region ap-south-1
```

#### 5. ECR Image Push Failures

**Symptom**: Docker push to ECR fails

**Solutions**:
```bash
# Re-authenticate with ECR
aws ecr get-login-password --region ap-south-1 | \
    docker login --username AWS --password-stdin \
    ACCOUNT_ID.dkr.ecr.ap-south-1.amazonaws.com

# Check repository exists
aws ecr describe-repositories --region ap-south-1

# Check image tags
aws ecr describe-images \
    --repository-name ragqa/api-gateway \
    --region ap-south-1
```

### Getting Help

1. **Check CloudWatch Logs** - Most issues are visible in logs
2. **Review AWS Events** - Check CloudTrail for API errors
3. **Verify IAM Permissions** - Ensure roles have required permissions
4. **Check Service Quotas** - Verify you haven't hit account limits
5. **Test Connectivity** - Use bastion host or VPC endpoints

## Teardown

### Complete Infrastructure Removal

```bash
cd /path/to/rag-qa-hindi/aws

# Destroy production environment
./destroy.sh production

# Destroy with force flag (skip confirmation)
./destroy.sh production --force

# Keep RDS/ElastiCache data snapshots
./destroy.sh production --keep-data
```

### Selective Destruction

To destroy specific resources:

```bash
cd terraform

# Destroy specific service
terraform destroy \
    -target=aws_ecs_service.api_gateway \
    -var-file=terraform.tfvars

# Destroy without databases
terraform destroy \
    -var=skip_final_snapshot=true \
    -var-file=terraform.tfvars
```

### Post-Destruction Cleanup

After running destroy, verify cleanup:

```bash
# Check for remaining resources
aws ec2 describe-instances \
    --filters "Name=tag:Project,Values=ragqa" \
    --region ap-south-1

# Check load balancers
aws elbv2 describe-load-balancers --region ap-south-1

# Check ECR repositories (may be kept for reuse)
aws ecr describe-repositories --region ap-south-1

# Check S3 buckets (state bucket is kept)
aws s3 ls | grep ragqa
```

### Data Retention

Data retained after destruction:

- S3 Terraform state bucket (for audit trail)
- RDS snapshots (if `--keep-data` flag used)
- ECR images (for faster redeployment)
- CloudWatch Logs (configurable retention)
- CloudTrail logs (if enabled)

To permanently delete:

```bash
# Delete S3 state bucket
aws s3 rb s3://ragqa-terraform-state --force

# Delete RDS snapshots
aws rds delete-db-snapshot \
    --db-snapshot-identifier ragqa-postgres-manual-YYYYMMDD \
    --region ap-south-1

# Delete ECR repositories
aws ecr delete-repository \
    --repository-name ragqa/api-gateway \
    --force \
    --region ap-south-1
```

## Additional Resources

- [AWS ECS Documentation](https://docs.aws.amazon.com/ecs/)
- [Terraform AWS Provider](https://registry.terraform.io/providers/hashicorp/aws/latest/docs)
- [AWS CloudMap Service Discovery](https://docs.aws.amazon.com/cloud-map/)
- [ECS Task Definitions](https://docs.aws.amazon.com/AmazonECS/latest/developerguide/task_definitions.html)
- [Fargate Pricing](https://aws.amazon.com/fargate/pricing/)

## Support

For issues or questions:

1. Check the Troubleshooting section
2. Review CloudWatch Logs
3. Check AWS Console for resource status
4. Review deployment logs
5. Open an issue in the project repository

---

Last Updated: February 2024
