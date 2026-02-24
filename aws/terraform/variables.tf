variable "project_name" {
  description = "Project name for all AWS resources"
  type        = string
  default     = "ragqa"

  validation {
    condition     = can(regex("^[a-z][a-z0-9-]*$", var.project_name))
    error_message = "Project name must start with lowercase letter and contain only lowercase letters, numbers, and hyphens."
  }
}

variable "environment" {
  description = "Environment name (production, staging, development)"
  type        = string
  default     = "production"

  validation {
    condition     = contains(["production", "staging", "development"], var.environment)
    error_message = "Environment must be one of: production, staging, development."
  }
}

variable "aws_region" {
  description = "AWS region for all resources"
  type        = string
  default     = "ap-south-1"

  validation {
    condition     = can(regex("^[a-z]{2}-[a-z]+-[0-9]{1}$", var.aws_region))
    error_message = "AWS region must be a valid region code."
  }
}

variable "vpc_cidr" {
  description = "CIDR block for VPC"
  type        = string
  default     = "10.0.0.0/16"

  validation {
    condition     = can(cidrhost(var.vpc_cidr, 0))
    error_message = "VPC CIDR must be a valid CIDR block."
  }
}

variable "public_subnet_1_cidr" {
  description = "CIDR block for public subnet 1"
  type        = string
  default     = "10.0.1.0/24"
}

variable "public_subnet_2_cidr" {
  description = "CIDR block for public subnet 2"
  type        = string
  default     = "10.0.2.0/24"
}

variable "private_subnet_1_cidr" {
  description = "CIDR block for private subnet 1"
  type        = string
  default     = "10.0.10.0/24"
}

variable "private_subnet_2_cidr" {
  description = "CIDR block for private subnet 2"
  type        = string
  default     = "10.0.11.0/24"
}

variable "db_instance_class" {
  description = "RDS instance class for PostgreSQL"
  type        = string
  default     = "db.r6g.large"

  validation {
    condition     = can(regex("^db\\.[a-z0-9]+\\.[a-z]+$", var.db_instance_class))
    error_message = "Database instance class must be a valid RDS instance type."
  }
}

variable "db_allocated_storage" {
  description = "Allocated storage for RDS PostgreSQL in GB"
  type        = number
  default     = 100

  validation {
    condition     = var.db_allocated_storage >= 20 && var.db_allocated_storage <= 65536
    error_message = "Database allocated storage must be between 20 and 65536 GB."
  }
}

variable "db_backup_retention_days" {
  description = "RDS backup retention period in days"
  type        = number
  default     = 7

  validation {
    condition     = var.db_backup_retention_days >= 1 && var.db_backup_retention_days <= 35
    error_message = "Backup retention days must be between 1 and 35."
  }
}

variable "cache_instance_type" {
  description = "ElastiCache Redis instance type"
  type        = string
  default     = "cache.r6g.large"

  validation {
    condition     = can(regex("^cache\\.[a-z0-9]+\\.[a-z]+$", var.cache_instance_type))
    error_message = "Cache instance type must be a valid ElastiCache instance type."
  }
}

variable "gpu_instance_type" {
  description = "EC2 instance type for GPU workloads (LLM, speech, translation, training)"
  type        = string
  default     = "g5.2xlarge"

  validation {
    condition     = can(regex("^(g5|g6|p4d|p5)\\.[a-z]+$", var.gpu_instance_type))
    error_message = "GPU instance type must be a valid GPU-enabled instance type."
  }
}

variable "min_gpu_instances" {
  description = "Minimum number of GPU instances in Auto Scaling Group"
  type        = number
  default     = 1

  validation {
    condition     = var.min_gpu_instances >= 1 && var.min_gpu_instances <= 10
    error_message = "Minimum GPU instances must be between 1 and 10."
  }
}

variable "max_gpu_instances" {
  description = "Maximum number of GPU instances in Auto Scaling Group"
  type        = number
  default     = 4

  validation {
    condition     = var.max_gpu_instances >= var.min_gpu_instances && var.max_gpu_instances <= 10
    error_message = "Maximum GPU instances must be >= minimum and <= 10."
  }
}

variable "domain_name" {
  description = "Domain name for ACM certificate and ALB (required for HTTPS)"
  type        = string

  validation {
    condition     = can(regex("^[a-z0-9]([a-z0-9-]*[a-z0-9])?(\\.[a-z0-9]([a-z0-9-]*[a-z0-9])?)*$", var.domain_name))
    error_message = "Domain name must be a valid FQDN."
  }
}

variable "enable_nat_gateway" {
  description = "Enable NAT Gateway for private subnet outbound internet access"
  type        = bool
  default     = true
}

variable "enable_flow_logs" {
  description = "Enable VPC Flow Logs for network debugging"
  type        = bool
  default     = true
}

variable "rds_backup_window" {
  description = "RDS backup window in UTC (HH:MM-HH:MM)"
  type        = string
  default     = "03:00-04:00"
}

variable "rds_maintenance_window" {
  description = "RDS maintenance window (ddd:HH:MM-ddd:HH:MM)"
  type        = string
  default     = "sun:04:30-sun:05:30"
}

variable "redis_snapshot_retention_days" {
  description = "Redis automatic snapshot retention days"
  type        = number
  default     = 5

  validation {
    condition     = var.redis_snapshot_retention_days >= 0 && var.redis_snapshot_retention_days <= 35
    error_message = "Redis snapshot retention must be between 0 and 35 days."
  }
}

variable "cloudwatch_log_retention_days" {
  description = "CloudWatch log retention period in days"
  type        = number
  default     = 30

  validation {
    condition     = contains([1, 3, 5, 7, 14, 30, 60, 90, 120, 150, 180, 365, 400, 545, 731, 1827, 3653], var.cloudwatch_log_retention_days)
    error_message = "CloudWatch log retention must be a valid CloudWatch retention period."
  }
}

variable "s3_lifecycle_transition_days" {
  description = "Days before S3 objects transition to Infrequent Access"
  type        = number
  default     = 90

  validation {
    condition     = var.s3_lifecycle_transition_days >= 30
    error_message = "S3 lifecycle transition days must be >= 30."
  }
}

variable "s3_lifecycle_glacier_days" {
  description = "Days before S3 objects transition to Glacier"
  type        = number
  default     = 365

  validation {
    condition     = var.s3_lifecycle_glacier_days >= var.s3_lifecycle_transition_days
    error_message = "Glacier transition days must be >= IA transition days."
  }
}

variable "ecr_image_retention_count" {
  description = "Number of ECR images to retain"
  type        = number
  default     = 10

  validation {
    condition     = var.ecr_image_retention_count >= 3 && var.ecr_image_retention_count <= 100
    error_message = "ECR image retention count must be between 3 and 100."
  }
}

variable "enable_deletion_protection" {
  description = "Enable deletion protection for ALB and RDS"
  type        = bool
  default     = true
}

variable "tags" {
  description = "Additional tags to apply to all resources"
  type        = map(string)
  default     = {}
}

# Services configuration
variable "services" {
  description = "ECS services configuration"
  type = map(object({
    cpu        = number
    memory     = number
    desired_count = number
    requires_gpu = bool
    port       = number
  }))

  default = {
    "api-gateway" = {
      cpu           = 512
      memory        = 1024
      desired_count = 2
      requires_gpu  = false
      port          = 8000
    }
    "rag-service" = {
      cpu           = 1024
      memory        = 2048
      desired_count = 2
      requires_gpu  = false
      port          = 8001
    }
    "llm-service" = {
      cpu           = 4096
      memory        = 16384
      desired_count = 1
      requires_gpu  = true
      port          = 8002
    }
    "speech-service" = {
      cpu           = 2048
      memory        = 4096
      desired_count = 1
      requires_gpu  = true
      port          = 8003
    }
    "translation-service" = {
      cpu           = 2048
      memory        = 4096
      desired_count = 1
      requires_gpu  = true
      port          = 8004
    }
    "ocr-service" = {
      cpu           = 1024
      memory        = 2048
      desired_count = 1
      requires_gpu  = false
      port          = 8005
    }
    "data-ingestion" = {
      cpu           = 1024
      memory        = 2048
      desired_count = 1
      requires_gpu  = false
      port          = 8006
    }
    "model-training" = {
      cpu           = 4096
      memory        = 16384
      desired_count = 0
      requires_gpu  = true
      port          = 8007
    }
    "chat-widget" = {
      cpu           = 512
      memory        = 512
      desired_count = 2
      requires_gpu  = false
      port          = 3000
    }
    "search-page" = {
      cpu           = 512
      memory        = 512
      desired_count = 2
      requires_gpu  = false
      port          = 3001
    }
    "admin-dashboard" = {
      cpu           = 512
      memory        = 512
      desired_count = 1
      requires_gpu  = false
      port          = 3002
    }
    "milvus" = {
      cpu           = 2048
      memory        = 4096
      desired_count = 1
      requires_gpu  = false
      port          = 19530
    }
    "langfuse" = {
      cpu           = 1024
      memory        = 2048
      desired_count = 1
      requires_gpu  = false
      port          = 3010
    }
  }
}
