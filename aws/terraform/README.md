# RAG-based Hindi & English, Search & QA System - AWS Terraform Infrastructure

This Terraform configuration deploys a production-ready, scalable infrastructure for the RAG-based Hindi & English, Search & QA system on AWS. The setup follows a VPC isolation model where public traffic is restricted to web frontends via ALB, while all backend APIs are internal-only, accessible only from within the VPC.

## Architecture Overview

### Network Architecture
- **VPC**: 10.0.0.0/16
  - **Public Subnets** (AZ1, AZ2): 10.0.1.0/24, 10.0.2.0/24
    - ALB, NAT Gateway (for outbound internet access)
  - **Private Subnets** (AZ1, AZ2): 10.0.10.0/24, 10.0.11.0/24
    - All backend services (ECS, RDS, ElastiCache, Milvus)

### Key Design Principles
1. **VPC Network Isolation**: Backend APIs are not publicly accessible. Security is enforced via network boundaries.
2. **Public Web Frontends**: Chat widget, search page, and admin dashboard accessible via ALB with HTTPS.
3. **Private Backend Services**: API Gateway and all data processing services in private subnets.
4. **Outbound Internet Access**: Data ingestion services use NAT Gateway for web scraping.
5. **Multi-AZ Deployment**: All critical services are Multi-AZ for high availability.

## AWS Services Deployed

### Core Infrastructure
- **VPC** with public and private subnets, Internet Gateway, NAT Gateway
- **Application Load Balancer** (public-facing) for web frontends
- **Internal ALB** for backend service-to-service communication

### Databases
- **RDS PostgreSQL 16** (db.r6g.large, Multi-AZ) for main application data
- **RDS PostgreSQL 16** (db.t4g.medium) for Langfuse observability
- Automated backups with 7-day retention
- Enhanced monitoring, Performance Insights enabled

### Cache
- **ElastiCache Redis 7.x** (cache.r6g.large, Multi-AZ) with automatic failover
- At-rest and in-transit encryption
- 4 logical databases:
  - DB 0: Query results and embeddings cache
  - DB 1: Rate limiting
  - DB 2: Session storage
  - DB 3: Translation cache

### Storage
- **S3 Documents Bucket**: Raw docs, processed text, thumbnails, images
- **S3 Models Bucket**: Base models, fine-tuned models, training/evaluation data
- **S3 Backups Bucket**: RDS snapshots, Milvus snapshots
- Versioning enabled, lifecycle policies (90 days to IA, 365 days to Glacier)
- Server-side encryption with KMS, block all public access

### Container Registry & Compute
- **ECR Repositories**: One per service (api-gateway, rag-service, llm-service, etc.)
  - Image scanning on push, KMS encryption, 10-image retention
- **ECS Cluster** with dual capacity providers:
  - **Fargate**: For non-GPU services (API, RAG, frontends)
  - **EC2 Auto Scaling Group**: g5.2xlarge GPU instances for LLM, speech, translation, model training
  - Min 1, Max 4 GPU instances (auto-scaling based on demand)

### Security
- **Security Groups**:
  - ALB: 80/443 from anywhere
  - Frontend Services: from ALB only
  - Backend Services: from ALB (API) and VPC CIDR (inter-service)
  - RDS: from backend services only
  - ElastiCache: from backend services only
  - Milvus: from backend services only
  - GPU instances: outbound all (for model downloads)

### Monitoring & Observability
- **CloudWatch Log Groups** (30-day retention) for each service
- **CloudWatch Alarms**: CPU > 80%, Memory > 80%, ALB 5xx > 1%, RDS connections high
- **SNS Topic** for alert notifications
- **VPC Flow Logs** for network debugging
- **CloudWatch Dashboard** for infrastructure overview

### Secrets Management
- AWS Secrets Manager for:
  - RDS passwords (main and Langfuse)
  - Redis AUTH token
  - JWT secret key
  - App secret key
  - Langfuse API keys

## Prerequisites

1. **AWS Account** with appropriate IAM permissions
2. **Domain Name** with validated ACM certificate in the target region
3. **Terraform** 1.5 or later
4. **AWS CLI** configured with credentials
5. **S3 Bucket** and **DynamoDB Table** for Terraform state (created separately)

## State Management Setup

Before deploying, create the S3 backend:

```bash
# Create S3 bucket for state
aws s3api create-bucket \
  --bucket ragqa-terraform-state \
  --region ap-south-1 \
  --create-bucket-configuration LocationConstraint=ap-south-1

# Enable versioning
aws s3api put-bucket-versioning \
  --bucket ragqa-terraform-state \
  --versioning-configuration Status=Enabled

# Create DynamoDB table for state locking
aws dynamodb create-table \
  --table-name ragqa-terraform-locks \
  --attribute-definitions AttributeName=LockID,AttributeType=S \
  --key-schema AttributeName=LockID,KeyType=HASH \
  --provisioned-throughput ReadCapacityUnits=5,WriteCapacityUnits=5 \
  --region ap-south-1
```

## Deployment Instructions

### 1. Prepare Configuration

```bash
# Copy the example variables file
cp terraform.tfvars.example terraform.tfvars

# Edit with your values
nano terraform.tfvars
```

Key variables to set:
- `domain_name`: Your domain for HTTPS (must have validated ACM certificate)
- `aws_region`: ap-south-1 (Mumbai, closest to India) or your preferred region
- `db_instance_class`: RDS instance type (default: db.r6g.large)
- `gpu_instance_type`: EC2 GPU instance type (default: g5.2xlarge)
- `min_gpu_instances` / `max_gpu_instances`: Auto-scaling limits

### 2. Initialize Terraform

```bash
terraform init
```

### 3. Review Plan

```bash
terraform plan -out=tfplan
```

### 4. Apply Configuration

```bash
terraform apply tfplan
```

The deployment will take 20-30 minutes as RDS instances and ECS services initialize.

### 5. Retrieve Outputs

```bash
terraform output -json > outputs.json
terraform output alb_url
terraform output alb_dns_name
```

## File Structure

```
terraform/
├── main.tf                 # Provider config, data sources, backend
├── variables.tf            # Variable definitions with validation
├── vpc.tf                  # VPC, subnets, IGW, NAT, route tables, NACLs
├── security_groups.tf      # All security group definitions
├── rds.tf                  # RDS PostgreSQL instances, parameter groups
├── elasticache.tf          # ElastiCache Redis cluster
├── s3.tf                   # S3 buckets with encryption, versioning, lifecycle
├── ecr.tf                  # ECR repositories with lifecycle policies
├── ecs.tf                  # ECS cluster, task definitions, services, ASG
├── iam.tf                  # IAM roles, policies, instance profiles
├── alb.tf                  # Public ALB, target groups, listener rules
├── secrets.tf              # Secrets Manager for sensitive data
├── cloudwatch.tf           # CloudWatch logs, alarms, dashboards
├── outputs.tf              # Output values
├── terraform.tfvars.example # Example variables
├── user_data.sh           # EC2 GPU instance setup script
└── README.md              # This file
```

## Security Considerations

### Network Security
- All backend services are in private subnets with no direct internet access
- NAT Gateway provides controlled outbound internet for data ingestion
- Network ACLs restrict traffic at subnet level
- VPC Flow Logs enabled for audit trail

### Data Security
- RDS encryption with KMS at rest
- RDS SSL/TLS for in-transit encryption
- Redis encryption at rest and in-transit
- S3 encryption with KMS, versioning, MFA delete capable
- All secrets in AWS Secrets Manager with KMS encryption

### Access Control
- Security groups provide application-level access control
- IAM policies follow least privilege principle
- Task execution role limited to ECR and Secrets Manager access
- Task role limited to required service permissions

### Compliance
- CloudWatch logs enable audit trail
- VPC Flow Logs for network forensics
- RDS automated backups with point-in-time recovery
- S3 versioning and lifecycle for data retention

## Cost Optimization

### Current Configuration Estimates (Monthly, ap-south-1)
- **RDS**: ~$300 (r6g.large Multi-AZ) + $100 (t4g.medium)
- **ElastiCache**: ~$250 (r6g.large)
- **ECS Fargate**: ~$200 (2 tasks, 512 CPU/1GB RAM)
- **EC2 GPU**: ~$800 (1x g5.2xlarge spot) - auto-scales based on demand
- **S3**: ~$50-100 (documents, models, backups)
- **Data Transfer**: ~$50-100 (outbound)
- **Other** (ALB, NAT, CloudWatch): ~$50-100

**Total**: ~$1,800-2,000/month

### Cost Reduction Tips
- Use Spot instances for GPU (set in `aws_autoscaling_group`)
- Adjust RDS backup retention
- Use Fargate Spot for non-critical services
- Archive old backups to Glacier

## Monitoring & Maintenance

### Key Metrics to Monitor
- **RDS**: CPU %, Database Connections, Free Storage
- **ElastiCache**: CPU %, Memory %, Evictions, Replication Lag
- **ECS**: CPU %, Memory %, Task Count, Service Health
- **ALB**: Request Count, Target Response Time, 4xx/5xx Errors

### CloudWatch Alarms
Check the CloudWatch console for active alarms. Key alarms include:
- RDS CPU > 80%
- Redis Memory > 80%
- ALB 5xx errors > 1
- ECS service CPU > 80%
- GPU ASG CPU > 80%

### Backup & Recovery
- **RDS**: Automated daily backups, 7-day retention (configurable)
- **Redis**: Snapshots every 5 minutes (configurable)
- **S3**: Versioning enabled, can restore from previous versions
- **Milvus**: Regular snapshots to S3 backups bucket

### Scaling
- **ECS Services**: Auto-scale based on CPU (70%) and Memory (80%)
- **GPU Instances**: Auto-scale 1-4 instances based on CloudWatch metrics
- **RDS**: Multi-AZ can handle failover, read replicas available
- **ElastiCache**: Cluster mode disabled, 1 replica for high availability

## Troubleshooting

### Health Checks
```bash
# Check ECS cluster status
aws ecs describe-clusters --clusters ragqa-cluster

# Check task definitions
aws ecs list-task-definitions

# View CloudWatch logs
aws logs tail /ecs/ragqa --follow
```

### Common Issues

**ALB returning 502 Bad Gateway**
- Check ECS service health: `aws ecs describe-services --cluster ragqa-cluster --services ragqa-api-gateway`
- Check security groups allow traffic between ALB and services
- Check service CPU/memory allocation is sufficient

**RDS connection timeouts**
- Verify security group allows 5432 from ecs-backend-sg
- Check RDS parameter group settings
- Monitor RDS connections: `SELECT count(*) FROM pg_stat_activity;`

**Redis AUTH errors**
- Verify AUTH token in Secrets Manager matches Redis configuration
- Check security group allows 6379 from backend services
- Verify Redis encryption settings

### Debugging
Enable VPC Flow Logs to troubleshoot network issues:
```bash
aws ec2 create-flow-logs \
  --resource-type VPC \
  --resource-ids vpc-xxxxx \
  --traffic-type ALL \
  --log-destination-type cloudwatch-logs \
  --log-group-name /aws/vpc/flowlogs
```

## Updates & Upgrades

### Terraform Updates
```bash
# Update provider versions
terraform init -upgrade

# Review changes
terraform plan

# Apply updates
terraform apply
```

### Database Updates
- RDS minor version: Automatic (configurable maintenance window)
- RDS major version: Manual (requires downtime)
- Use `terraform apply -target=aws_db_instance.main` to update

### ECS Service Updates
- Push new image to ECR
- Update task definition with new image tag
- ECS service automatically redeploys

## Destroying Infrastructure

**Warning**: This cannot be undone!

```bash
# List resources that will be deleted
terraform plan -destroy

# Delete all resources
terraform destroy

# If resources are protected (deletion_protection=true):
# 1. Modify terraform.tfvars: enable_deletion_protection = false
# 2. Run: terraform apply
# 3. Then run: terraform destroy
```

## Additional Resources

- [Terraform AWS Provider Documentation](https://registry.terraform.io/providers/hashicorp/aws/latest/docs)
- [AWS Best Practices for RDS](https://docs.aws.amazon.com/AmazonRDS/latest/UserGuide/CHAP_BestPractices.html)
- [AWS ECS Best Practices](https://docs.aws.amazon.com/AmazonECS/latest/developerguide/container_instance_launch_template.html)
- [VPC Design Patterns](https://aws.amazon.com/blogs/architecture/vpc-design-patterns/)

## Support & Contact

For issues, feature requests, or contributions, please refer to the main project repository.

---

**Last Updated**: February 2026
**Terraform Version**: 1.5+
**AWS Provider Version**: 5.0+
