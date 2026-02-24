# VPC Outputs
output "vpc_id" {
  description = "VPC ID"
  value       = aws_vpc.main.id
}

output "vpc_cidr" {
  description = "VPC CIDR block"
  value       = aws_vpc.main.cidr_block
}

output "public_subnet_1_id" {
  description = "Public Subnet 1 ID (AZ1)"
  value       = aws_subnet.public_1.id
}

output "public_subnet_2_id" {
  description = "Public Subnet 2 ID (AZ2)"
  value       = aws_subnet.public_2.id
}

output "private_subnet_1_id" {
  description = "Private Subnet 1 ID (AZ1)"
  value       = aws_subnet.private_1.id
}

output "private_subnet_2_id" {
  description = "Private Subnet 2 ID (AZ2)"
  value       = aws_subnet.private_2.id
}

output "nat_gateway_id" {
  description = "NAT Gateway ID"
  value       = try(aws_nat_gateway.main[0].id, null)
}

output "nat_gateway_ip" {
  description = "Elastic IP address for NAT Gateway"
  value       = try(aws_eip.nat[0].public_ip, null)
}

# Load Balancer Outputs
output "alb_dns_name" {
  description = "DNS name of the load balancer"
  value       = aws_lb.main.dns_name
}

output "alb_arn" {
  description = "ARN of the load balancer"
  value       = aws_lb.main.arn
}

output "alb_zone_id" {
  description = "Zone ID of the load balancer"
  value       = aws_lb.main.zone_id
}

output "alb_url" {
  description = "URL to access the load balancer"
  value       = "https://${var.domain_name}"
}

output "internal_alb_dns_name" {
  description = "DNS name of the internal load balancer"
  value       = aws_lb.internal.dns_name
}

output "internal_alb_arn" {
  description = "ARN of the internal load balancer"
  value       = aws_lb.internal.arn
}

# RDS Outputs
output "rds_endpoint" {
  description = "RDS PostgreSQL endpoint"
  value       = aws_db_instance.main.endpoint
  sensitive   = true
}

output "rds_address" {
  description = "RDS PostgreSQL host address"
  value       = aws_db_instance.main.address
}

output "rds_port" {
  description = "RDS PostgreSQL port"
  value       = aws_db_instance.main.port
}

output "rds_database_name" {
  description = "RDS PostgreSQL database name"
  value       = aws_db_instance.main.db_name
}

output "rds_username" {
  description = "RDS PostgreSQL master username"
  value       = aws_db_instance.main.username
  sensitive   = true
}

output "rds_password_secret_arn" {
  description = "ARN of the secret containing RDS password"
  value       = aws_secretsmanager_secret.rds_password.arn
}

output "rds_langfuse_endpoint" {
  description = "RDS Langfuse PostgreSQL endpoint"
  value       = aws_db_instance.langfuse.endpoint
  sensitive   = true
}

output "rds_langfuse_address" {
  description = "RDS Langfuse PostgreSQL host address"
  value       = aws_db_instance.langfuse.address
}

# ElastiCache Outputs
output "elasticache_endpoint" {
  description = "ElastiCache Redis endpoint"
  value       = aws_elasticache_cluster.main.cache_nodes[0].address
}

output "elasticache_port" {
  description = "ElastiCache Redis port"
  value       = aws_elasticache_cluster.main.port
}

output "elasticache_cluster_id" {
  description = "ElastiCache Redis cluster ID"
  value       = aws_elasticache_cluster.main.cluster_id
}

output "redis_auth_token_secret_arn" {
  description = "ARN of the secret containing Redis AUTH token"
  value       = aws_secretsmanager_secret.redis_auth_token.arn
}

# S3 Outputs
output "s3_documents_bucket" {
  description = "S3 bucket name for documents"
  value       = aws_s3_bucket.documents.id
}

output "s3_models_bucket" {
  description = "S3 bucket name for models"
  value       = aws_s3_bucket.models.id
}

output "s3_backups_bucket" {
  description = "S3 bucket name for backups"
  value       = aws_s3_bucket.backups.id
}

output "s3_alb_logs_bucket" {
  description = "S3 bucket name for ALB logs"
  value       = aws_s3_bucket.alb_logs.id
}

# ECR Outputs
output "ecr_api_gateway_repository_url" {
  description = "ECR API Gateway repository URL"
  value       = aws_ecr_repository.api_gateway.repository_url
}

output "ecr_rag_service_repository_url" {
  description = "ECR RAG Service repository URL"
  value       = aws_ecr_repository.rag_service.repository_url
}

output "ecr_llm_service_repository_url" {
  description = "ECR LLM Service repository URL"
  value       = aws_ecr_repository.llm_service.repository_url
}

output "ecr_chat_widget_repository_url" {
  description = "ECR Chat Widget repository URL"
  value       = aws_ecr_repository.chat_widget.repository_url
}

output "ecr_search_page_repository_url" {
  description = "ECR Search Page repository URL"
  value       = aws_ecr_repository.search_page.repository_url
}

output "ecr_admin_dashboard_repository_url" {
  description = "ECR Admin Dashboard repository URL"
  value       = aws_ecr_repository.admin_dashboard.repository_url
}

# ECS Outputs
output "ecs_cluster_name" {
  description = "ECS cluster name"
  value       = aws_ecs_cluster.main.name
}

output "ecs_cluster_arn" {
  description = "ECS cluster ARN"
  value       = aws_ecs_cluster.main.arn
}

output "ecs_api_gateway_service_name" {
  description = "ECS API Gateway service name"
  value       = aws_ecs_service.api_gateway.name
}

output "ecs_chat_widget_service_name" {
  description = "ECS Chat Widget service name"
  value       = aws_ecs_service.chat_widget.name
}

# IAM Outputs
output "ecs_task_execution_role_arn" {
  description = "ARN of the ECS task execution role"
  value       = aws_iam_role.ecs_task_execution_role.arn
}

output "ecs_task_role_arn" {
  description = "ARN of the ECS task role"
  value       = aws_iam_role.ecs_task_role.arn
}

output "ec2_gpu_instance_profile_arn" {
  description = "ARN of the EC2 GPU instance profile"
  value       = aws_iam_instance_profile.ec2_gpu.arn
}

# Auto Scaling Group Outputs
output "gpu_asg_name" {
  description = "GPU Auto Scaling Group name"
  value       = aws_autoscaling_group.gpu_instances.name
}

output "gpu_asg_min_size" {
  description = "GPU Auto Scaling Group minimum size"
  value       = aws_autoscaling_group.gpu_instances.min_size
}

output "gpu_asg_max_size" {
  description = "GPU Auto Scaling Group maximum size"
  value       = aws_autoscaling_group.gpu_instances.max_size
}

# Secrets Manager Outputs
output "jwt_secret_arn" {
  description = "ARN of JWT secret"
  value       = aws_secretsmanager_secret.jwt_secret.arn
}

output "app_secret_arn" {
  description = "ARN of app secret"
  value       = aws_secretsmanager_secret.app_secret.arn
}

output "langfuse_keys_secret_arn" {
  description = "ARN of Langfuse keys secret"
  value       = aws_secretsmanager_secret.langfuse_keys.arn
}

# Security Groups Outputs
output "alb_security_group_id" {
  description = "ID of ALB security group"
  value       = aws_security_group.alb.id
}

output "ecs_backend_security_group_id" {
  description = "ID of ECS backend security group"
  value       = aws_security_group.ecs_backend.id
}

output "ecs_frontend_security_group_id" {
  description = "ID of ECS frontend security group"
  value       = aws_security_group.ecs_frontend.id
}

output "rds_security_group_id" {
  description = "ID of RDS security group"
  value       = aws_security_group.rds.id
}

output "elasticache_security_group_id" {
  description = "ID of ElastiCache security group"
  value       = aws_security_group.elasticache.id
}

# SNS Topic Outputs
output "sns_alerts_topic_arn" {
  description = "ARN of SNS topic for alerts"
  value       = aws_sns_topic.alerts.arn
}

# CloudWatch Outputs
output "cloudwatch_log_group_ecs" {
  description = "CloudWatch log group for ECS"
  value       = aws_cloudwatch_log_group.ecs.name
}

output "cloudwatch_log_group_api_gateway" {
  description = "CloudWatch log group for API Gateway"
  value       = aws_cloudwatch_log_group.api_gateway.name
}

output "cloudwatch_dashboard_url" {
  description = "URL to CloudWatch dashboard"
  value       = "https://console.aws.amazon.com/cloudwatch/home?region=${var.aws_region}#dashboards:name=${aws_cloudwatch_dashboard.main.dashboard_name}"
}

# Summary Information
output "infrastructure_summary" {
  description = "Summary of the deployed infrastructure"
  value = {
    region              = var.aws_region
    project_name        = var.project_name
    environment         = var.environment
    vpc_cidr            = aws_vpc.main.cidr_block
    alb_dns_name        = aws_lb.main.dns_name
    rds_endpoint        = aws_db_instance.main.address
    redis_endpoint      = aws_elasticache_cluster.main.cache_nodes[0].address
    ecs_cluster_name    = aws_ecs_cluster.main.name
    s3_buckets = {
      documents = aws_s3_bucket.documents.id
      models    = aws_s3_bucket.models.id
      backups   = aws_s3_bucket.backups.id
    }
  }

  sensitive = false
}
