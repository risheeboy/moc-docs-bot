# ECR Repository for API Gateway
resource "aws_ecr_repository" "api_gateway" {
  name                 = "${var.project_name}/api-gateway"
  image_tag_mutability = "IMMUTABLE"

  image_scanning_configuration {
    scan_on_push = true
  }

  encryption_configuration {
    encryption_type = "KMS"
    kms_key         = aws_kms_key.ecr.arn
  }

  tags = {
    Name   = "${var.project_name}-api-gateway"
    Stream = "Container"
  }
}

# ECR Repository for RAG Service
resource "aws_ecr_repository" "rag_service" {
  name                 = "${var.project_name}/rag-service"
  image_tag_mutability = "IMMUTABLE"

  image_scanning_configuration {
    scan_on_push = true
  }

  encryption_configuration {
    encryption_type = "KMS"
    kms_key         = aws_kms_key.ecr.arn
  }

  tags = {
    Name   = "${var.project_name}-rag-service"
    Stream = "Container"
  }
}

# ECR Repository for LLM Service
resource "aws_ecr_repository" "llm_service" {
  name                 = "${var.project_name}/llm-service"
  image_tag_mutability = "IMMUTABLE"

  image_scanning_configuration {
    scan_on_push = true
  }

  encryption_configuration {
    encryption_type = "KMS"
    kms_key         = aws_kms_key.ecr.arn
  }

  tags = {
    Name   = "${var.project_name}-llm-service"
    Stream = "Container"
  }
}

# ECR Repository for Speech Service
resource "aws_ecr_repository" "speech_service" {
  name                 = "${var.project_name}/speech-service"
  image_tag_mutability = "IMMUTABLE"

  image_scanning_configuration {
    scan_on_push = true
  }

  encryption_configuration {
    encryption_type = "KMS"
    kms_key         = aws_kms_key.ecr.arn
  }

  tags = {
    Name   = "${var.project_name}-speech-service"
    Stream = "Container"
  }
}

# ECR Repository for Translation Service
resource "aws_ecr_repository" "translation_service" {
  name                 = "${var.project_name}/translation-service"
  image_tag_mutability = "IMMUTABLE"

  image_scanning_configuration {
    scan_on_push = true
  }

  encryption_configuration {
    encryption_type = "KMS"
    kms_key         = aws_kms_key.ecr.arn
  }

  tags = {
    Name   = "${var.project_name}-translation-service"
    Stream = "Container"
  }
}

# ECR Repository for OCR Service
resource "aws_ecr_repository" "ocr_service" {
  name                 = "${var.project_name}/ocr-service"
  image_tag_mutability = "IMMUTABLE"

  image_scanning_configuration {
    scan_on_push = true
  }

  encryption_configuration {
    encryption_type = "KMS"
    kms_key         = aws_kms_key.ecr.arn
  }

  tags = {
    Name   = "${var.project_name}-ocr-service"
    Stream = "Container"
  }
}

# ECR Repository for Data Ingestion
resource "aws_ecr_repository" "data_ingestion" {
  name                 = "${var.project_name}/data-ingestion"
  image_tag_mutability = "IMMUTABLE"

  image_scanning_configuration {
    scan_on_push = true
  }

  encryption_configuration {
    encryption_type = "KMS"
    kms_key         = aws_kms_key.ecr.arn
  }

  tags = {
    Name   = "${var.project_name}-data-ingestion"
    Stream = "Container"
  }
}

# ECR Repository for Model Training
resource "aws_ecr_repository" "model_training" {
  name                 = "${var.project_name}/model-training"
  image_tag_mutability = "IMMUTABLE"

  image_scanning_configuration {
    scan_on_push = true
  }

  encryption_configuration {
    encryption_type = "KMS"
    kms_key         = aws_kms_key.ecr.arn
  }

  tags = {
    Name   = "${var.project_name}-model-training"
    Stream = "Container"
  }
}

# ECR Repository for Chat Widget
resource "aws_ecr_repository" "chat_widget" {
  name                 = "${var.project_name}/chat-widget"
  image_tag_mutability = "IMMUTABLE"

  image_scanning_configuration {
    scan_on_push = true
  }

  encryption_configuration {
    encryption_type = "KMS"
    kms_key         = aws_kms_key.ecr.arn
  }

  tags = {
    Name   = "${var.project_name}-chat-widget"
    Stream = "Container"
  }
}

# ECR Repository for Search Page
resource "aws_ecr_repository" "search_page" {
  name                 = "${var.project_name}/search-page"
  image_tag_mutability = "IMMUTABLE"

  image_scanning_configuration {
    scan_on_push = true
  }

  encryption_configuration {
    encryption_type = "KMS"
    kms_key         = aws_kms_key.ecr.arn
  }

  tags = {
    Name   = "${var.project_name}-search-page"
    Stream = "Container"
  }
}

# ECR Repository for Admin Dashboard
resource "aws_ecr_repository" "admin_dashboard" {
  name                 = "${var.project_name}/admin-dashboard"
  image_tag_mutability = "IMMUTABLE"

  image_scanning_configuration {
    scan_on_push = true
  }

  encryption_configuration {
    encryption_type = "KMS"
    kms_key         = aws_kms_key.ecr.arn
  }

  tags = {
    Name   = "${var.project_name}-admin-dashboard"
    Stream = "Container"
  }
}

# ECR Repository for Milvus
resource "aws_ecr_repository" "milvus" {
  name                 = "${var.project_name}/milvus"
  image_tag_mutability = "IMMUTABLE"

  image_scanning_configuration {
    scan_on_push = true
  }

  encryption_configuration {
    encryption_type = "KMS"
    kms_key         = aws_kms_key.ecr.arn
  }

  tags = {
    Name   = "${var.project_name}-milvus"
    Stream = "Container"
  }
}

# ECR Repository for Langfuse
resource "aws_ecr_repository" "langfuse" {
  name                 = "${var.project_name}/langfuse"
  image_tag_mutability = "IMMUTABLE"

  image_scanning_configuration {
    scan_on_push = true
  }

  encryption_configuration {
    encryption_type = "KMS"
    kms_key         = aws_kms_key.ecr.arn
  }

  tags = {
    Name   = "${var.project_name}-langfuse"
    Stream = "Container"
  }
}

# KMS Key for ECR encryption
resource "aws_kms_key" "ecr" {
  description             = "KMS key for ECR encryption"
  deletion_window_in_days = 10
  enable_key_rotation     = true

  tags = {
    Name   = "${var.project_name}-ecr-key"
    Stream = "Security"
  }
}

resource "aws_kms_alias" "ecr" {
  name          = "alias/${var.project_name}-ecr"
  target_key_id = aws_kms_key.ecr.key_id
}

# ECR Lifecycle Policy - Keep last N images
locals {
  ecr_repositories = {
    api_gateway       = aws_ecr_repository.api_gateway.name
    rag_service       = aws_ecr_repository.rag_service.name
    llm_service       = aws_ecr_repository.llm_service.name
    speech_service    = aws_ecr_repository.speech_service.name
    translation_service = aws_ecr_repository.translation_service.name
    ocr_service       = aws_ecr_repository.ocr_service.name
    data_ingestion    = aws_ecr_repository.data_ingestion.name
    model_training    = aws_ecr_repository.model_training.name
    chat_widget       = aws_ecr_repository.chat_widget.name
    search_page       = aws_ecr_repository.search_page.name
    admin_dashboard   = aws_ecr_repository.admin_dashboard.name
    milvus            = aws_ecr_repository.milvus.name
    langfuse          = aws_ecr_repository.langfuse.name
  }
}

resource "aws_ecr_lifecycle_policy" "all" {
  for_each   = local.ecr_repositories
  repository = each.value

  policy = jsonencode({
    rules = [
      {
        rulePriority = 1
        description  = "Keep last ${var.ecr_image_retention_count} images"
        selection = {
          tagStatus     = "any"
          countType     = "imageCountMoreThan"
          countNumber   = var.ecr_image_retention_count
        }
        action = {
          type = "expire"
        }
      }
    ]
  })
}

# ECR Pull-through Cache Rule (optional, for caching public images)
resource "aws_ecr_pull_through_cache_rule" "docker_hub" {
  ecr_repository_prefix = "dockerhub"
  upstream_registry_url = "registry-1.docker.io"

  depends_on = [aws_ecr_repository.api_gateway]
}
