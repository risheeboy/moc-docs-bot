.PHONY: help init plan apply destroy fmt validate taint untaint refresh output cost-estimate backend-setup

TERRAFORM := terraform
TF_DIR := .

help:
	@echo "RAG Search & QA System - Terraform Makefile"
	@echo ""
	@echo "Available targets:"
	@echo "  help              - Show this help message"
	@echo "  backend-setup     - Create S3 backend and DynamoDB lock table"
	@echo "  init              - Initialize Terraform working directory"
	@echo "  validate          - Validate Terraform configuration"
	@echo "  fmt               - Format Terraform files"
	@echo "  plan              - Generate execution plan"
	@echo "  apply             - Apply Terraform configuration"
	@echo "  destroy           - Destroy all AWS resources (DANGEROUS!)"
	@echo "  refresh           - Refresh Terraform state from AWS"
	@echo "  output            - Display Terraform outputs"
	@echo "  output-json       - Display outputs as JSON"
	@echo "  cost-estimate     - Estimate infrastructure costs"
	@echo "  taint [resource]  - Mark resource for recreation"
	@echo "  untaint [resource]- Remove taint from resource"
	@echo ""
	@echo "Examples:"
	@echo "  make plan"
	@echo "  make apply"
	@echo "  make taint resource=aws_db_instance.main"
	@echo "  make destroy"

backend-setup:
	@echo "Creating S3 backend and DynamoDB lock table..."
	@read -p "Enter AWS region (default: ap-south-1): " region; \
	region=$${region:-ap-south-1}; \
	aws s3api create-bucket \
		--bucket ragqa-terraform-state \
		--region $$region \
		--create-bucket-configuration LocationConstraint=$$region 2>/dev/null || echo "Bucket might already exist"; \
	aws s3api put-bucket-versioning \
		--bucket ragqa-terraform-state \
		--versioning-configuration Status=Enabled; \
	aws dynamodb create-table \
		--table-name ragqa-terraform-locks \
		--attribute-definitions AttributeName=LockID,AttributeType=S \
		--key-schema AttributeName=LockID,KeyType=HASH \
		--provisioned-throughput ReadCapacityUnits=5,WriteCapacityUnits=5 \
		--region $$region 2>/dev/null || echo "Table might already exist"; \
	echo "Backend setup complete!"

init:
	@echo "Initializing Terraform..."
	$(TERRAFORM) -chdir=$(TF_DIR) init
	@echo "Terraform initialized!"

validate:
	@echo "Validating Terraform configuration..."
	$(TERRAFORM) -chdir=$(TF_DIR) validate
	@echo "Configuration is valid!"

fmt:
	@echo "Formatting Terraform files..."
	$(TERRAFORM) -chdir=$(TF_DIR) fmt -recursive
	@echo "Formatting complete!"

plan:
	@echo "Generating Terraform plan..."
	$(TERRAFORM) -chdir=$(TF_DIR) plan -out=tfplan
	@echo "Plan saved to tfplan"

apply:
	@echo "Applying Terraform configuration..."
	@if [ -f tfplan ]; then \
		$(TERRAFORM) -chdir=$(TF_DIR) apply tfplan; \
		rm tfplan; \
	else \
		echo "No plan file found. Run 'make plan' first."; \
		exit 1; \
	fi
	@echo "Infrastructure deployed!"

destroy:
	@echo "WARNING: This will destroy all AWS resources!"
	@read -p "Are you sure? Type 'yes' to continue: " confirm; \
	if [ "$$confirm" = "yes" ]; then \
		$(TERRAFORM) -chdir=$(TF_DIR) destroy; \
	else \
		echo "Destroy cancelled."; \
	fi

refresh:
	@echo "Refreshing Terraform state..."
	$(TERRAFORM) -chdir=$(TF_DIR) refresh
	@echo "State refreshed!"

output:
	@echo "Terraform Outputs:"
	@$(TERRAFORM) -chdir=$(TF_DIR) output
	@echo ""

output-json:
	@$(TERRAFORM) -chdir=$(TF_DIR) output -json

cost-estimate:
	@echo "Infrastructure Cost Estimation (ap-south-1, monthly)"
	@echo "======================================================"
	@echo ""
	@echo "RDS PostgreSQL (db.r6g.large, Multi-AZ):"
	@echo "  - Compute + Storage + Backup: ~$400"
	@echo ""
	@echo "RDS PostgreSQL (db.t4g.medium, Single-AZ):"
	@echo "  - Compute + Storage: ~$100"
	@echo ""
	@echo "ElastiCache Redis (cache.r6g.large):"
	@echo "  - Compute + Data transfer: ~$250"
	@echo ""
	@echo "ECS Fargate (2 services, 512 CPU/1024 MB):"
	@echo "  - 2 services × 730 hours: ~$200"
	@echo ""
	@echo "EC2 GPU Instances (g5.2xlarge, 1-4 instances):"
	@echo "  - 1 instance × 730 hours: ~$800 (on-demand)"
	@echo "  - ~$250 (Spot instances - 70% savings)"
	@echo ""
	@echo "S3 Storage (documents, models, backups):"
	@echo "  - ~100 GB total: ~$50"
	@echo ""
	@echo "Data Transfer:"
	@echo "  - Outbound: ~$100"
	@echo ""
	@echo "ALB + NAT Gateway + CloudWatch:"
	@echo "  - ~$150"
	@echo ""
	@echo "======================================================"
	@echo "TOTAL (on-demand): ~$2,050/month"
	@echo "TOTAL (Spot for GPU): ~$1,300/month"
	@echo ""
	@echo "Cost optimization tips:"
	@echo "  - Enable Spot instances for GPU workloads (70% savings)"
	@echo "  - Use Fargate Spot for non-critical services"
	@echo "  - Reduce RDS backup retention"
	@echo "  - Archive old data to Glacier"

taint:
	@if [ -z "$(resource)" ]; then \
		echo "Usage: make taint resource=aws_resource_type.name"; \
		exit 1; \
	fi
	@echo "Tainting resource: $(resource)"
	$(TERRAFORM) -chdir=$(TF_DIR) taint $(resource)
	@echo "Resource tainted. Run 'make apply' to recreate it."

untaint:
	@if [ -z "$(resource)" ]; then \
		echo "Usage: make untaint resource=aws_resource_type.name"; \
		exit 1; \
	fi
	@echo "Untainting resource: $(resource)"
	$(TERRAFORM) -chdir=$(TF_DIR) untaint $(resource)
	@echo "Resource untainted."

# Development targets
.PHONY: dev-validate dev-plan dev-apply dev-destroy

dev-validate: fmt validate
	@echo "Development validation complete!"

dev-plan: fmt validate plan
	@echo "Development plan complete!"

dev-apply: dev-plan apply
	@echo "Development deployment complete!"

dev-destroy: destroy
	@echo "Development infrastructure destroyed!"

# Utility targets
.PHONY: state-list state-show state-lock-list clean

state-list:
	@$(TERRAFORM) -chdir=$(TF_DIR) state list

state-show:
	@if [ -z "$(resource)" ]; then \
		echo "Usage: make state-show resource=aws_resource_type.name"; \
		exit 1; \
	fi
	@$(TERRAFORM) -chdir=$(TF_DIR) state show $(resource)

state-lock-list:
	@echo "Checking Terraform lock status..."
	@aws dynamodb scan --table-name ragqa-terraform-locks --region ap-south-1

clean:
	@echo "Cleaning up Terraform files..."
	@rm -f tfplan tfplan.json
	@rm -rf .terraform.lock.hcl
	@find . -name ".terraform" -type d -exec rm -rf {} + 2>/dev/null || true
	@echo "Cleanup complete!"

# Health check
.PHONY: health-check logs

health-check:
	@echo "Infrastructure Health Check"
	@echo "=============================="
	@echo ""
	@echo "RDS Status:"
	@aws rds describe-db-instances --query 'DBInstances[?DBInstanceIdentifier==`ragqa-db-main`].DBInstanceStatus' --region ap-south-1 2>/dev/null || echo "Unable to check"
	@echo ""
	@echo "ElastiCache Status:"
	@aws elasticache describe-cache-clusters --cache-cluster-id ragqa-redis-main --query 'CacheClusters[0].CacheClusterStatus' --region ap-south-1 2>/dev/null || echo "Unable to check"
	@echo ""
	@echo "ECS Cluster Status:"
	@aws ecs describe-clusters --clusters ragqa-cluster --query 'clusters[0].status' --region ap-south-1 2>/dev/null || echo "Unable to check"
	@echo ""
	@echo "ALB Status:"
	@aws elbv2 describe-load-balancers --query 'LoadBalancers[?LoadBalancerName==`ragqa-alb`].State.Code' --region ap-south-1 2>/dev/null || echo "Unable to check"

logs:
	@echo "Tailing ECS logs (last 50 lines)..."
	@aws logs tail /ecs/ragqa --region ap-south-1 --follow 2>/dev/null || echo "Unable to access logs"
