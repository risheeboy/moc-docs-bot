#!/bin/bash
set -e

# Terraform Infrastructure Validation Script
# Validates HCL files, checks prerequisites, and runs pre-deployment checks

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}===============================================${NC}"
echo -e "${BLUE}RAG Search & QA System - Terraform Validation${NC}"
echo -e "${BLUE}===============================================${NC}"
echo ""

# Counter for issues
ERRORS=0
WARNINGS=0

# Helper functions
print_success() {
  echo -e "${GREEN}✓${NC} $1"
}

print_error() {
  echo -e "${RED}✗${NC} $1"
  ((ERRORS++))
}

print_warning() {
  echo -e "${YELLOW}⚠${NC} $1"
  ((WARNINGS++))
}

print_section() {
  echo ""
  echo -e "${BLUE}→ $1${NC}"
}

# 1. Check prerequisites
print_section "Checking prerequisites"

# Check Terraform
if ! command -v terraform &> /dev/null; then
  print_error "Terraform not installed"
else
  TF_VERSION=$(terraform --version | head -n1 | awk '{print $2}')
  print_success "Terraform $TF_VERSION installed"
fi

# Check AWS CLI
if ! command -v aws &> /dev/null; then
  print_error "AWS CLI not installed"
else
  AWS_VERSION=$(aws --version | awk '{print $1}' | cut -d'/' -f2)
  print_success "AWS CLI v$AWS_VERSION installed"
fi

# Check jq (optional)
if ! command -v jq &> /dev/null; then
  print_warning "jq not installed (optional, for JSON parsing)"
else
  print_success "jq installed"
fi

# Check AWS credentials
print_section "Checking AWS credentials"
if aws sts get-caller-identity &> /dev/null; then
  ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
  USER_ARN=$(aws sts get-caller-identity --query Arn --output text)
  print_success "AWS credentials configured"
  echo "  Account ID: $ACCOUNT_ID"
  echo "  User/Role: $USER_ARN"
else
  print_error "AWS credentials not configured or invalid"
fi

# 2. Validate HCL syntax
print_section "Validating Terraform HCL syntax"

if terraform init -input=false &> /dev/null; then
  print_success "Terraform initialized"
else
  print_error "Failed to initialize Terraform"
fi

if terraform validate &> /dev/null; then
  print_success "All .tf files have valid syntax"
else
  print_error "HCL validation failed"
  terraform validate
fi

# 3. Check terraform.tfvars
print_section "Checking terraform.tfvars configuration"

if [ ! -f terraform.tfvars ]; then
  print_error "terraform.tfvars not found (copy from terraform.tfvars.example)"
else
  print_success "terraform.tfvars exists"

  # Check required variables
  if grep -q "domain_name" terraform.tfvars; then
    DOMAIN=$(grep "domain_name" terraform.tfvars | cut -d'=' -f2 | xargs)
    print_success "domain_name configured: $DOMAIN"

    # Warn if using example domain
    if [[ "$DOMAIN" == *"example.com"* ]]; then
      print_warning "domain_name contains 'example.com' - change to your actual domain"
    fi
  else
    print_error "domain_name not set in terraform.tfvars"
  fi

  # Check other important variables
  if grep -q "aws_region" terraform.tfvars; then
    REGION=$(grep "aws_region" terraform.tfvars | cut -d'=' -f2 | xargs)
    print_success "aws_region configured: $REGION"
  else
    print_warning "aws_region not explicitly set (will use default)"
  fi
fi

# 4. Check AWS region capabilities
print_section "Checking AWS region capabilities"

REGION=$(grep "aws_region" terraform.tfvars 2>/dev/null | cut -d'=' -f2 | xargs || echo "ap-south-1")

# Check RDS availability
if aws ec2 describe-instance-types \
  --region ${REGION} \
  --filters "Name=instance-type,Values=db.r6g.large" \
  &> /dev/null; then
  print_success "RDS instance type available in $REGION"
else
  print_warning "RDS instance type may not be available in $REGION"
fi

# Check ElastiCache availability
if aws ec2 describe-instance-types \
  --region ${REGION} \
  --filters "Name=instance-type,Values=cache.r6g.large" \
  &> /dev/null; then
  print_success "ElastiCache instance type available in $REGION"
else
  print_warning "ElastiCache instance type may not be available in $REGION"
fi

# Check GPU availability
if aws ec2 describe-instance-types \
  --region ${REGION} \
  --filters "Name=instance-type,Values=g5.2xlarge" \
  &> /dev/null; then
  print_success "GPU instance type available in $REGION"
else
  print_warning "GPU instance type (g5) may not be available in $REGION"
  echo "  Consider using a different region or changing gpu_instance_type"
fi

# 5. Check S3 backend
print_section "Checking Terraform S3 backend"

BACKEND_BUCKET="ragqa-terraform-state-${ACCOUNT_ID}"
if aws s3 ls s3://${BACKEND_BUCKET} &> /dev/null; then
  print_success "Backend S3 bucket exists: $BACKEND_BUCKET"
else
  print_warning "Backend S3 bucket not found"
  echo "  Run: make backend-setup"
fi

# 6. Check ACM certificate
print_section "Checking ACM certificate"

if [ -f terraform.tfvars ]; then
  DOMAIN=$(grep "domain_name" terraform.tfvars 2>/dev/null | cut -d'=' -f2 | xargs || echo "")

  if [ -n "$DOMAIN" ] && [ "$DOMAIN" != "example.com" ]; then
    # Check if certificate exists
    CERT_COUNT=$(aws acm list-certificates \
      --region ${REGION} \
      --query "CertificateSummaryList[?DomainName=='${DOMAIN}'].CertificateArn" \
      --output text | wc -w)

    if [ $CERT_COUNT -gt 0 ]; then
      print_success "ACM certificate found for $DOMAIN"
    else
      print_error "ACM certificate NOT found for $DOMAIN"
      echo "  You must create and validate the certificate first:"
      echo "  aws acm request-certificate --domain-name $DOMAIN --region $REGION"
    fi
  fi
fi

# 7. Validate terraform plan
print_section "Generating Terraform plan"

if terraform plan -input=false -out=tfplan.test &> /dev/null; then
  RESOURCE_COUNT=$(terraform show -json tfplan.test | jq '.resource_changes | length')
  print_success "Terraform plan generated successfully"
  echo "  Resources to be created: $RESOURCE_COUNT"
  rm -f tfplan.test
else
  print_error "Failed to generate Terraform plan"
  terraform plan -input=false
fi

# 8. Check file integrity
print_section "Checking Terraform file integrity"

# Count .tf files
TF_FILES=$(find . -maxdepth 1 -name "*.tf" -type f | wc -l)
print_success "Found $TF_FILES Terraform files"

# Check for syntax errors
if terraform fmt -check &> /dev/null; then
  print_success "All Terraform files are properly formatted"
else
  print_warning "Some Terraform files need formatting"
  echo "  Run: make fmt"
fi

# 9. Environment checks
print_section "Checking environment"

# Check if running in production
if [ "$TERM" == "dumb" ] || [ -z "$TERM" ]; then
  print_warning "Running in non-interactive environment (CI/CD?)"
fi

# Check git status
if command -v git &> /dev/null && [ -d .git ]; then
  GIT_STATUS=$(git status --porcelain 2>/dev/null | wc -l)
  if [ $GIT_STATUS -gt 0 ]; then
    print_warning "Uncommitted changes in git (not an error, but best practice is to commit)"
  fi
fi

# 10. Final recommendations
print_section "Recommendations before deployment"

echo ""
if [ $ERRORS -eq 0 ]; then
  print_success "All critical checks passed!"
  echo ""
  echo "Next steps:"
  echo "1. Review the Terraform plan carefully"
  echo "2. Run: make apply"
  echo "3. Monitor: AWS CloudFormation console or 'make health-check'"
  echo "4. Verify: Check CloudWatch logs and ALB status"
else
  print_error "Please fix the errors above before deploying"
  exit 1
fi

echo ""
echo -e "${BLUE}===============================================${NC}"
echo -e "${BLUE}Validation Summary${NC}"
echo -e "${BLUE}===============================================${NC}"
echo "Errors:   $ERRORS"
echo "Warnings: $WARNINGS"
echo ""

# Exit with appropriate code
if [ $ERRORS -gt 0 ]; then
  exit 1
elif [ $WARNINGS -gt 0 ]; then
  exit 0  # Continue despite warnings
else
  exit 0
fi
