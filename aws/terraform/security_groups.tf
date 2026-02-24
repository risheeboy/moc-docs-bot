# Security Group for ALB (public-facing)
resource "aws_security_group" "alb" {
  name        = "${var.project_name}-alb-sg"
  description = "Security group for Application Load Balancer"
  vpc_id      = aws_vpc.main.id

  # Inbound HTTP
  ingress {
    from_port   = 80
    to_port     = 80
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
    description = "HTTP from anywhere"
  }

  # Inbound HTTPS
  ingress {
    from_port   = 443
    to_port     = 443
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
    description = "HTTPS from anywhere"
  }

  # Outbound all
  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
    description = "All outbound traffic"
  }

  tags = {
    Name   = "${var.project_name}-alb-sg"
    Stream = "Security"
  }
}

# Security Group for ECS Frontend Services (chat-widget, search-page, admin-dashboard)
resource "aws_security_group" "ecs_frontend" {
  name        = "${var.project_name}-ecs-frontend-sg"
  description = "Security group for ECS frontend services"
  vpc_id      = aws_vpc.main.id

  # Inbound from ALB only
  ingress {
    from_port       = 3000
    to_port         = 3002
    protocol        = "tcp"
    security_groups = [aws_security_group.alb.id]
    description     = "Frontend ports from ALB"
  }

  # Outbound all
  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
    description = "All outbound traffic"
  }

  tags = {
    Name   = "${var.project_name}-ecs-frontend-sg"
    Stream = "Security"
  }
}

# Security Group for ECS Backend Services (API, RAG, LLM, Speech, Translation, OCR, etc.)
resource "aws_security_group" "ecs_backend" {
  name        = "${var.project_name}-ecs-backend-sg"
  description = "Security group for ECS backend services (internal only)"
  vpc_id      = aws_vpc.main.id

  # Inbound from ALB for API Gateway
  ingress {
    from_port       = 8000
    to_port         = 8000
    protocol        = "tcp"
    security_groups = [aws_security_group.alb.id]
    description     = "API Gateway from ALB"
  }

  # Inbound from VPC CIDR (internal service-to-service communication)
  ingress {
    from_port   = 8000
    to_port     = 8007
    protocol    = "tcp"
    cidr_blocks = [var.vpc_cidr]
    description = "Backend service ports from VPC"
  }

  # Inbound from within the same security group (for inter-service communication)
  ingress {
    from_port       = 0
    to_port         = 65535
    protocol        = "tcp"
    self            = true
    description     = "All TCP from same security group"
  }

  ingress {
    from_port       = 0
    to_port         = 65535
    protocol        = "udp"
    self            = true
    description     = "All UDP from same security group"
  }

  # Outbound all
  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
    description = "All outbound traffic"
  }

  tags = {
    Name   = "${var.project_name}-ecs-backend-sg"
    Stream = "Security"
  }
}

# Security Group for RDS PostgreSQL
resource "aws_security_group" "rds" {
  name        = "${var.project_name}-rds-sg"
  description = "Security group for RDS PostgreSQL"
  vpc_id      = aws_vpc.main.id

  # Inbound from ECS backend only
  ingress {
    from_port       = 5432
    to_port         = 5432
    protocol        = "tcp"
    security_groups = [aws_security_group.ecs_backend.id]
    description     = "PostgreSQL from ECS backend"
  }

  # Outbound all
  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
    description = "All outbound traffic"
  }

  tags = {
    Name   = "${var.project_name}-rds-sg"
    Stream = "Security"
  }
}

# Security Group for ElastiCache Redis
resource "aws_security_group" "elasticache" {
  name        = "${var.project_name}-elasticache-sg"
  description = "Security group for ElastiCache Redis"
  vpc_id      = aws_vpc.main.id

  # Inbound from ECS backend only
  ingress {
    from_port       = 6379
    to_port         = 6379
    protocol        = "tcp"
    security_groups = [aws_security_group.ecs_backend.id]
    description     = "Redis from ECS backend"
  }

  # Outbound all
  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
    description = "All outbound traffic"
  }

  tags = {
    Name   = "${var.project_name}-elasticache-sg"
    Stream = "Security"
  }
}

# Security Group for Milvus Vector Database
resource "aws_security_group" "milvus" {
  name        = "${var.project_name}-milvus-sg"
  description = "Security group for Milvus vector database"
  vpc_id      = aws_vpc.main.id

  # Inbound from ECS backend only
  ingress {
    from_port       = 19530
    to_port         = 19530
    protocol        = "tcp"
    security_groups = [aws_security_group.ecs_backend.id]
    description     = "Milvus from ECS backend"
  }

  # Outbound all
  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
    description = "All outbound traffic"
  }

  tags = {
    Name   = "${var.project_name}-milvus-sg"
    Stream = "Security"
  }
}

# Security Group for GPU instances (EC2 for training and inference)
resource "aws_security_group" "gpu" {
  name        = "${var.project_name}-gpu-sg"
  description = "Security group for GPU EC2 instances"
  vpc_id      = aws_vpc.main.id

  # Inbound from ECS backend
  ingress {
    from_port       = 0
    to_port         = 65535
    protocol        = "tcp"
    security_groups = [aws_security_group.ecs_backend.id]
    description     = "All TCP from ECS backend"
  }

  ingress {
    from_port       = 0
    to_port         = 65535
    protocol        = "udp"
    security_groups = [aws_security_group.ecs_backend.id]
    description     = "All UDP from ECS backend"
  }

  # Inbound from within VPC for inter-GPU communication (distributed training)
  ingress {
    from_port   = 0
    to_port     = 65535
    protocol    = "tcp"
    cidr_blocks = [var.vpc_cidr]
    description = "All TCP from VPC"
  }

  # Outbound all (for model downloads, package installations)
  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
    description = "All outbound traffic"
  }

  tags = {
    Name   = "${var.project_name}-gpu-sg"
    Stream = "Security"
  }
}

# Internal ALB Security Group
resource "aws_security_group" "internal_alb" {
  name        = "${var.project_name}-internal-alb-sg"
  description = "Security group for internal load balancer"
  vpc_id      = aws_vpc.main.id

  # Inbound from VPC CIDR only
  ingress {
    from_port   = 80
    to_port     = 80
    protocol    = "tcp"
    cidr_blocks = [var.vpc_cidr]
    description = "HTTP from VPC"
  }

  ingress {
    from_port   = 443
    to_port     = 443
    protocol    = "tcp"
    cidr_blocks = [var.vpc_cidr]
    description = "HTTPS from VPC"
  }

  # Outbound all
  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
    description = "All outbound traffic"
  }

  tags = {
    Name   = "${var.project_name}-internal-alb-sg"
    Stream = "Security"
  }
}

# Security Group for Langfuse
resource "aws_security_group" "langfuse" {
  name        = "${var.project_name}-langfuse-sg"
  description = "Security group for Langfuse observability service"
  vpc_id      = aws_vpc.main.id

  # Inbound from ALB
  ingress {
    from_port       = 3010
    to_port         = 3010
    protocol        = "tcp"
    security_groups = [aws_security_group.alb.id]
    description     = "Langfuse from ALB"
  }

  # Inbound from ECS backend (for LLM service metrics)
  ingress {
    from_port       = 3010
    to_port         = 3010
    protocol        = "tcp"
    security_groups = [aws_security_group.ecs_backend.id]
    description     = "Langfuse from ECS backend"
  }

  # Outbound all
  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
    description = "All outbound traffic"
  }

  tags = {
    Name   = "${var.project_name}-langfuse-sg"
    Stream = "Security"
  }
}
