# Deployment Guide: RAG Hindi & English, Search & QA System on AWS

This guide walks you through deploying the complete RAG system infrastructure on AWS using Terraform.

## Table of Contents
1. [Prerequisites](#prerequisites)
2. [Pre-Deployment Setup](#pre-deployment-setup)
3. [Configuration](#configuration)
4. [Deployment](#deployment)
5. [Post-Deployment](#post-deployment)
6. [Validation](#validation)
7. [Troubleshooting](#troubleshooting)

## Prerequisites

### AWS Account Setup
- AWS account with appropriate permissions (Admin or custom policy with services listed below)
- AWS CLI v2 installed: https://docs.aws.amazon.com/cli/latest/userguide/getting-started-install.html
- AWS credentials configured: `aws configure`

### Local Tools
- Terraform 1.5 or later: https://www.terraform.io/downloads.html
- Make: `brew install make` (macOS) or `apt-get install make` (Linux)
- jq: `brew install jq` (optional, for JSON parsing)
- git: For version control

### Domain & SSL Certificate
- Registered domain name (e.g., ragqa.example.com)
- ACM certificate for the domain in ap-south-1 (or your target region)
  - Certificate can be self-signed for testing, but HTTPS requires a valid cert

### AWS IAM Permissions Required
The deployment requires permissions for these services:
- EC2 (VPC, Subnets, Security Groups, Auto Scaling Groups, Launch Templates)
- RDS (DB Instances, DB Subnet Groups, Parameter Groups)
- ElastiCache (Replication Groups, Subnet Groups)
- ECS (Clusters, Task Definitions, Services)
- ECR (Repositories)
- ALB/NLB (Load Balancers, Target Groups, Listeners)
- S3 (Buckets, Bucket Policies)
- IAM (Roles, Policies, Instance Profiles)
- CloudWatch (Log Groups, Alarms, Dashboards)
- Secrets Manager (Secrets)
- KMS (Keys)
- SNS (Topics)
- CloudFormation (for stacks, if used)

## Pre-Deployment Setup

### Step 1: Create S3 Backend Infrastructure

The Terraform state must be stored remotely for team collaboration and safety.

```bash
# Create S3 bucket for state
REGION=ap-south-1
ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)

aws s3api create-bucket \
  --bucket ragqa-terraform-state-${ACCOUNT_ID} \
  --region ${REGION} \
  --create-bucket-configuration LocationConstraint=${REGION}

# Enable versioning for state backup
aws s3api put-bucket-versioning \
  --bucket ragqa-terraform-state-${ACCOUNT_ID} \
  --versioning-configuration Status=Enabled

# Block public access
aws s3api put-public-access-block \
  --bucket ragqa-terraform-state-${ACCOUNT_ID} \
  --public-access-block-configuration \
    "BlockPublicAcls=true,IgnorePublicAcls=true,BlockPublicPolicy=true,RestrictPublicBuckets=true"

# Enable encryption
aws s3api put-bucket-encryption \
  --bucket ragqa-terraform-state-${ACCOUNT_ID} \
  --server-side-encryption-configuration \
    '{"Rules": [{"ApplyServerSideEncryptionByDefault": {"SSEAlgorithm": "AES256"}}]}'

# Create DynamoDB table for state locking
aws dynamodb create-table \
  --table-name ragqa-terraform-locks \
  --attribute-definitions AttributeName=LockID,AttributeType=S \
  --key-schema AttributeName=LockID,KeyType=HASH \
  --provisioned-throughput ReadCapacityUnits=5,WriteCapacityUnits=5 \
  --region ${REGION} \
  --tags Key=Environment,Value=production Key=Project,Value=ragqa

echo "Backend created successfully!"
```

### Step 2: Update main.tf Backend Configuration

Edit the `backend` block in main.tf:

```hcl
backend "s3" {
  bucket         = "ragqa-terraform-state-{ACCOUNT_ID}"  # Replace with actual account ID
  key            = "production/terraform.tfstate"
  region         = "ap-south-1"
  encrypt        = true
  dynamodb_table = "ragqa-terraform-locks"
}
```

### Step 3: Create ACM Certificate

If you don't have an ACM certificate:

```bash
DOMAIN_NAME="ragqa.example.com"
REGION=ap-south-1

aws acm request-certificate \
  --domain-name ${DOMAIN_NAME} \
  --subject-alternative-names "*.${DOMAIN_NAME}" \
  --validation-method DNS \
  --region ${REGION}

# Get certificate ARN and verify the domain via DNS
# (Follow the AWS console or CLI prompts for DNS validation)
```

For production, use a domain you control and validate ownership.

## Configuration

### Step 1: Prepare Variables

```bash
cd aws/terraform

# Copy the example file
cp terraform.tfvars.example terraform.tfvars

# Edit with your values
nano terraform.tfvars  # or vi, code, etc.
```

### Step 2: Key Configuration Values

Edit `terraform.tfvars`:

```hcl
# Project and Environment
project_name = "ragqa"
environment  = "production"
aws_region   = "ap-south-1"    # Mumbai - closest to India

# Domain (MUST have ACM certificate)
domain_name = "ragqa.yourdomain.com"

# VPC Settings (use defaults or customize)
vpc_cidr              = "10.0.0.0/16"
public_subnet_1_cidr  = "10.0.1.0/24"
public_subnet_2_cidr  = "10.0.2.0/24"
private_subnet_1_cidr = "10.0.10.0/24"
private_subnet_2_cidr = "10.0.11.0/24"

# Database (production defaults)
db_instance_class         = "db.r6g.large"   # 2 vCPU, 16GB RAM, Multi-AZ
db_allocated_storage      = 100              # 100 GB initial
db_backup_retention_days  = 7                # 7 days of backups

# Cache (production)
cache_instance_type = "cache.r6g.large"      # 2 vCPU, 16GB RAM, Multi-AZ

# GPU Compute
gpu_instance_type   = "g5.2xlarge"           # 1 GPU (24GB), 8 vCPU, 32GB RAM
min_gpu_instances   = 1                      # Minimum 1 instance
max_gpu_instances   = 4                      # Can scale to 4 instances

# Cost Control
enable_deletion_protection = true             # Prevent accidental deletion
enable_nat_gateway         = true             # Required for data ingestion
enable_flow_logs           = true             # For network debugging

# Tags
tags = {
  CostCenter = "Engineering"
  Team       = "Data"
  Owner      = "Your Name"
}
```

### Step 3: Validate Configuration

```bash
# Format files
make fmt

# Validate syntax
terraform validate

# Check for issues
terraform plan -input=false > plan.txt
cat plan.txt | head -50  # Review changes
```

## Deployment

### Step 1: Initialize Terraform

```bash
# Initialize working directory
terraform init

# Verify state is stored in S3
aws s3 ls s3://ragqa-terraform-state-${ACCOUNT_ID}/
```

### Step 2: Review Deployment Plan

```bash
# Generate detailed plan
make plan

# Review the plan carefully
cat tfplan | grep -E "^  + " | head -30

# Or convert to JSON for detailed review
terraform show -json tfplan | jq '.resource_changes[0:5]'
```

**Key resources that will be created:**
- 1 VPC with 4 subnets
- 1 ALB + 1 internal ALB
- 2 RDS instances (Multi-AZ)
- 1 ElastiCache cluster (Multi-AZ)
- 3 S3 buckets
- 13 ECR repositories
- 1 ECS cluster with Fargate + EC2 capacity providers
- Multiple security groups and IAM roles
- CloudWatch logs, alarms, and dashboards

### Step 3: Deploy Infrastructure

```bash
# Apply the plan
make apply

# Or manually
terraform apply tfplan

# Wait for completion (20-30 minutes for RDS to initialize)
# Monitor in AWS Console or run:
watch -n 10 'aws rds describe-db-instances --query "DBInstances[0].DBInstanceStatus" --region ap-south-1'
```

### Step 4: Capture Outputs

```bash
# Save outputs for reference
terraform output -json > outputs.json

# Display key outputs
terraform output alb_url
terraform output rds_endpoint
terraform output elasticache_endpoint
terraform output ecs_cluster_name

# Get all outputs in nice format
make output
```

## Post-Deployment

### Step 1: Update DNS

Point your domain to the ALB:

```bash
# Get ALB DNS name
ALB_DNS=$(terraform output -raw alb_dns_name)

# Create CNAME record in your DNS provider
# CNAME: ragqa.yourdomain.com -> $ALB_DNS
```

Wait for DNS propagation (typically 5 minutes to 24 hours).

### Step 2: Verify ALB Configuration

```bash
# Check ALB health
aws elbv2 describe-load-balancers \
  --query 'LoadBalancers[?LoadBalancerName==`ragqa-alb`]' \
  --region ap-south-1

# Check target groups
aws elbv2 describe-target-groups \
  --query 'TargetGroups[?LoadBalancerArn]' \
  --region ap-south-1
```

### Step 3: Retrieve Secrets

```bash
# RDS Password
aws secretsmanager get-secret-value \
  --secret-id ragqa/rds/main/password \
  --region ap-south-1 \
  --query SecretString \
  --output text | jq .password

# Redis AUTH Token
aws secretsmanager get-secret-value \
  --secret-id ragqa/redis/auth-token \
  --region ap-south-1 \
  --query SecretString \
  --output text | jq .auth_token
```

### Step 4: Deploy ECS Task Definitions

The current configuration has basic API Gateway and Chat Widget services. For other services:

```bash
# Register additional task definitions
aws ecs register-task-definition --cli-input-json file://rag-service-task-def.json

# Create services for other workloads
# (You'll need to create task definitions for each service)
```

### Step 5: Configure Auto Scaling

The template includes auto-scaling policies. To monitor:

```bash
# Check ECS service scaling
aws autoscaling describe-auto-scaling-groups \
  --auto-scaling-group-names ragqa-gpu-asg \
  --region ap-south-1

# Check ECS service target tracking
aws appautoscaling describe-scalable-targets \
  --service-namespace ecs \
  --region ap-south-1
```

## Validation

### Step 1: Health Checks

```bash
# Check all resources are healthy
make health-check

# Or manually:

# RDS
aws rds describe-db-instances \
  --db-instance-identifier ragqa-db-main \
  --query 'DBInstances[0].[DBInstanceStatus, Engine, DBInstanceClass]' \
  --region ap-south-1

# ElastiCache
aws elasticache describe-cache-clusters \
  --cache-cluster-id ragqa-redis-main \
  --show-cache-node-info \
  --query 'CacheClusters[0].[CacheClusterStatus, Engine, CacheNodeType]' \
  --region ap-south-1

# ECS
aws ecs describe-services \
  --cluster ragqa-cluster \
  --services ragqa-api-gateway ragqa-chat-widget \
  --region ap-south-1
```

### Step 2: Test ALB

```bash
# Get the URL
ALB_URL=$(terraform output -raw alb_url)

# Test HTTPS
curl -I ${ALB_URL}/

# Should return 200 or 301 (redirect)
```

### Step 3: Check CloudWatch Logs

```bash
# View recent logs
aws logs tail /ecs/ragqa --region ap-south-1 --follow --since 10m

# Or view in console
# https://ap-south-1.console.aws.amazon.com/cloudwatch/home
```

### Step 4: Test Database

```bash
# Get RDS endpoint
RDS_ENDPOINT=$(terraform output -raw rds_address)
RDS_PASSWORD=$(aws secretsmanager get-secret-value \
  --secret-id ragqa/rds/main/password \
  --region ap-south-1 \
  --query 'SecretString' \
  --output text | jq -r .password)

# Connect to RDS (requires psql)
psql -h ${RDS_ENDPOINT} -U ragqaadmin -d ragqa

# Or test connectivity with AWS RDS proxy
```

### Step 5: Test Redis

```bash
# Get Redis endpoint
REDIS_ENDPOINT=$(terraform output -raw elasticache_endpoint)

# Connect with redis-cli
redis-cli -h ${REDIS_ENDPOINT} -p 6379 --auth <AUTH_TOKEN> ping

# Should return PONG
```

## Troubleshooting

### Common Issues

#### 1. ALB Returns 503 Service Unavailable

**Cause**: ECS services not running or unhealthy

```bash
# Check ECS service status
aws ecs describe-services \
  --cluster ragqa-cluster \
  --services ragqa-api-gateway \
  --region ap-south-1

# Check task status
aws ecs list-tasks --cluster ragqa-cluster --region ap-south-1
aws ecs describe-tasks --cluster ragqa-cluster --tasks <TASK_ARN> --region ap-south-1

# Check CloudWatch logs
aws logs tail /ecs/ragqa/api-gateway --region ap-south-1 --follow
```

**Solution**:
- Ensure ECS services have desired_count > 0
- Check CPU and memory are sufficient
- Verify security groups allow traffic

#### 2. RDS Connection Timeout

**Cause**: Security group or network issue

```bash
# Verify security group allows RDS port
aws ec2 describe-security-groups \
  --group-ids sg-xxxxxx \
  --region ap-south-1 \
  --query 'SecurityGroups[0].IpPermissions'

# Check VPC endpoint routes
aws ec2 describe-route-tables \
  --filters "Name=vpc-id,Values=vpc-xxxxxx" \
  --region ap-south-1
```

**Solution**:
- Ensure ecs-backend-sg includes RDS security group in ingress rules
- Verify RDS is in private subnets with NAT Gateway
- Check route tables for correct target

#### 3. NAT Gateway Connectivity Issues

**Cause**: Data ingestion services can't reach internet

```bash
# Check NAT Gateway status
aws ec2 describe-nat-gateways \
  --filter Name=vpc-id,Values=vpc-xxxxxx \
  --region ap-south-1

# Check Elastic IP
aws ec2 describe-addresses \
  --query 'Addresses[?AssociationId]' \
  --region ap-south-1
```

**Solution**:
- Ensure NAT Gateway is in public subnet
- Check route table routes private → NAT
- Verify security groups allow outbound traffic

#### 4. Terraform State Lock

**Cause**: Another user has lock on state

```bash
# View locks
aws dynamodb scan \
  --table-name ragqa-terraform-locks \
  --region ap-south-1

# Force unlock (dangerous!)
aws dynamodb delete-item \
  --table-name ragqa-terraform-locks \
  --key '{"LockID":{"S":"path/to/resource"}}' \
  --region ap-south-1
```

#### 5. Out of Capacity (GPU)

**Cause**: g5 instances not available in region

```bash
# Check available instance types
aws ec2 describe-instance-types \
  --filters "Name=instance-type,Values=g5*" \
  --region ap-south-1

# Try different region or instance type
# Update terraform.tfvars:
# gpu_instance_type = "g4dn.xlarge"  # Older generation
```

## Cleanup

To destroy all resources:

```bash
# Disable deletion protection if enabled
# Edit terraform.tfvars: enable_deletion_protection = false
terraform apply

# Then destroy
terraform destroy

# Verify S3 state bucket still exists (for future recovery)
aws s3 ls s3://ragqa-terraform-state-${ACCOUNT_ID}/
```

## Next Steps

1. **Push Docker images** to ECR repositories
2. **Update task definitions** with actual image URIs
3. **Deploy remaining ECS services** (rag-service, llm-service, etc.)
4. **Configure Milvus** vector database
5. **Set up data ingestion** pipeline
6. **Configure monitoring and alerting** beyond defaults
7. **Set up CI/CD pipeline** for deployments

## Support

For issues or questions:
1. Check CloudWatch logs: `/ecs/ragqa/*`
2. Review AWS console for resource status
3. Check Terraform state: `terraform state list`
4. Enable debug logging: `export TF_LOG=DEBUG`

---

**Estimated Deployment Time**: 25-35 minutes
**Estimated Monthly Cost**: $1,300-2,000 (depending on GPU usage and data transfer)
