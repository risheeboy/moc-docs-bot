# AWS Cloud Map Service Discovery Configuration
# Provides private DNS-based service discovery for inter-service communication

# Private DNS Namespace
resource "aws_service_discovery_private_dns_namespace" "ragqa" {
  name            = "ragqa.local"
  description     = "Private DNS namespace for RAG QA services"
  vpc             = var.vpc_id
  tags = {
    Name = "ragqa-local"
  }
}

# Service Discovery Services

# API Gateway Service Discovery
resource "aws_service_discovery_service" "api_gateway" {
  name            = "api-gateway"
  description     = "API Gateway Service Discovery"
  namespace_id    = aws_service_discovery_private_dns_namespace.ragqa.id
  dns_config {
    namespace_id = aws_service_discovery_private_dns_namespace.ragqa.id
    dns_records {
      ttl  = 300
      type = "A"
    }
    routing_policy = "MULTIVALUE"
  }
  health_check_custom_config {
    failure_threshold = 1
  }
  tags = {
    Service = "api-gateway"
  }
}

# RAG Service Discovery
resource "aws_service_discovery_service" "rag_service" {
  name            = "rag-service"
  description     = "RAG Service Discovery"
  namespace_id    = aws_service_discovery_private_dns_namespace.ragqa.id
  dns_config {
    namespace_id = aws_service_discovery_private_dns_namespace.ragqa.id
    dns_records {
      ttl  = 300
      type = "A"
    }
    routing_policy = "MULTIVALUE"
  }
  health_check_custom_config {
    failure_threshold = 1
  }
  tags = {
    Service = "rag-service"
  }
}

# LLM Service Discovery
resource "aws_service_discovery_service" "llm_service" {
  name            = "llm-service"
  description     = "LLM Service Discovery"
  namespace_id    = aws_service_discovery_private_dns_namespace.ragqa.id
  dns_config {
    namespace_id = aws_service_discovery_private_dns_namespace.ragqa.id
    dns_records {
      ttl  = 300
      type = "A"
    }
    routing_policy = "MULTIVALUE"
  }
  health_check_custom_config {
    failure_threshold = 1
  }
  tags = {
    Service = "llm-service"
  }
}

# Speech Service Discovery
resource "aws_service_discovery_service" "speech_service" {
  name            = "speech-service"
  description     = "Speech Service Discovery"
  namespace_id    = aws_service_discovery_private_dns_namespace.ragqa.id
  dns_config {
    namespace_id = aws_service_discovery_private_dns_namespace.ragqa.id
    dns_records {
      ttl  = 300
      type = "A"
    }
    routing_policy = "MULTIVALUE"
  }
  health_check_custom_config {
    failure_threshold = 1
  }
  tags = {
    Service = "speech-service"
  }
}

# Translation Service Discovery
resource "aws_service_discovery_service" "translation_service" {
  name            = "translation-service"
  description     = "Translation Service Discovery"
  namespace_id    = aws_service_discovery_private_dns_namespace.ragqa.id
  dns_config {
    namespace_id = aws_service_discovery_private_dns_namespace.ragqa.id
    dns_records {
      ttl  = 300
      type = "A"
    }
    routing_policy = "MULTIVALUE"
  }
  health_check_custom_config {
    failure_threshold = 1
  }
  tags = {
    Service = "translation-service"
  }
}

# OCR Service Discovery
resource "aws_service_discovery_service" "ocr_service" {
  name            = "ocr-service"
  description     = "OCR Service Discovery"
  namespace_id    = aws_service_discovery_private_dns_namespace.ragqa.id
  dns_config {
    namespace_id = aws_service_discovery_private_dns_namespace.ragqa.id
    dns_records {
      ttl  = 300
      type = "A"
    }
    routing_policy = "MULTIVALUE"
  }
  health_check_custom_config {
    failure_threshold = 1
  }
  tags = {
    Service = "ocr-service"
  }
}

# Data Ingestion Service Discovery
resource "aws_service_discovery_service" "data_ingestion" {
  name            = "data-ingestion"
  description     = "Data Ingestion Service Discovery"
  namespace_id    = aws_service_discovery_private_dns_namespace.ragqa.id
  dns_config {
    namespace_id = aws_service_discovery_private_dns_namespace.ragqa.id
    dns_records {
      ttl  = 300
      type = "A"
    }
    routing_policy = "MULTIVALUE"
  }
  health_check_custom_config {
    failure_threshold = 1
  }
  tags = {
    Service = "data-ingestion"
  }
}

# Model Training Service Discovery
resource "aws_service_discovery_service" "model_training" {
  name            = "model-training"
  description     = "Model Training Service Discovery"
  namespace_id    = aws_service_discovery_private_dns_namespace.ragqa.id
  dns_config {
    namespace_id = aws_service_discovery_private_dns_namespace.ragqa.id
    dns_records {
      ttl  = 300
      type = "A"
    }
    routing_policy = "MULTIVALUE"
  }
  health_check_custom_config {
    failure_threshold = 1
  }
  tags = {
    Service = "model-training"
  }
}

# Chat Widget Service Discovery
resource "aws_service_discovery_service" "chat_widget" {
  name            = "chat-widget"
  description     = "Chat Widget Service Discovery"
  namespace_id    = aws_service_discovery_private_dns_namespace.ragqa.id
  dns_config {
    namespace_id = aws_service_discovery_private_dns_namespace.ragqa.id
    dns_records {
      ttl  = 300
      type = "A"
    }
    routing_policy = "MULTIVALUE"
  }
  health_check_custom_config {
    failure_threshold = 1
  }
  tags = {
    Service = "chat-widget"
  }
}

# Search Page Service Discovery
resource "aws_service_discovery_service" "search_page" {
  name            = "search-page"
  description     = "Search Page Service Discovery"
  namespace_id    = aws_service_discovery_private_dns_namespace.ragqa.id
  dns_config {
    namespace_id = aws_service_discovery_private_dns_namespace.ragqa.id
    dns_records {
      ttl  = 300
      type = "A"
    }
    routing_policy = "MULTIVALUE"
  }
  health_check_custom_config {
    failure_threshold = 1
  }
  tags = {
    Service = "search-page"
  }
}

# Admin Dashboard Service Discovery
resource "aws_service_discovery_service" "admin_dashboard" {
  name            = "admin-dashboard"
  description     = "Admin Dashboard Service Discovery"
  namespace_id    = aws_service_discovery_private_dns_namespace.ragqa.id
  dns_config {
    namespace_id = aws_service_discovery_private_dns_namespace.ragqa.id
    dns_records {
      ttl  = 300
      type = "A"
    }
    routing_policy = "MULTIVALUE"
  }
  health_check_custom_config {
    failure_threshold = 1
  }
  tags = {
    Service = "admin-dashboard"
  }
}

# Milvus Service Discovery
resource "aws_service_discovery_service" "milvus" {
  name            = "milvus"
  description     = "Milvus Vector DB Service Discovery"
  namespace_id    = aws_service_discovery_private_dns_namespace.ragqa.id
  dns_config {
    namespace_id = aws_service_discovery_private_dns_namespace.ragqa.id
    dns_records {
      ttl  = 300
      type = "A"
    }
    routing_policy = "MULTIVALUE"
  }
  health_check_custom_config {
    failure_threshold = 1
  }
  tags = {
    Service = "milvus"
  }
}

# Langfuse Service Discovery
resource "aws_service_discovery_service" "langfuse" {
  name            = "langfuse"
  description     = "Langfuse Observability Service Discovery"
  namespace_id    = aws_service_discovery_private_dns_namespace.ragqa.id
  dns_config {
    namespace_id = aws_service_discovery_private_dns_namespace.ragqa.id
    dns_records {
      ttl  = 300
      type = "A"
    }
    routing_policy = "MULTIVALUE"
  }
  health_check_custom_config {
    failure_threshold = 1
  }
  tags = {
    Service = "langfuse"
  }
}

# Grafana Service Discovery
resource "aws_service_discovery_service" "grafana" {
  name            = "grafana"
  description     = "Grafana Monitoring Service Discovery"
  namespace_id    = aws_service_discovery_private_dns_namespace.ragqa.id
  dns_config {
    namespace_id = aws_service_discovery_private_dns_namespace.ragqa.id
    dns_records {
      ttl  = 300
      type = "A"
    }
    routing_policy = "MULTIVALUE"
  }
  health_check_custom_config {
    failure_threshold = 1
  }
  tags = {
    Service = "grafana"
  }
}

# Prometheus Service Discovery
resource "aws_service_discovery_service" "prometheus" {
  name            = "prometheus"
  description     = "Prometheus Metrics Service Discovery"
  namespace_id    = aws_service_discovery_private_dns_namespace.ragqa.id
  dns_config {
    namespace_id = aws_service_discovery_private_dns_namespace.ragqa.id
    dns_records {
      ttl  = 300
      type = "A"
    }
    routing_policy = "MULTIVALUE"
  }
  health_check_custom_config {
    failure_threshold = 1
  }
  tags = {
    Service = "prometheus"
  }
}

# Database Service Discovery (for RDS)
resource "aws_service_discovery_service" "postgres" {
  name            = "postgres"
  description     = "PostgreSQL Database Service Discovery"
  namespace_id    = aws_service_discovery_private_dns_namespace.ragqa.id
  dns_config {
    namespace_id = aws_service_discovery_private_dns_namespace.ragqa.id
    dns_records {
      ttl  = 300
      type = "A"
    }
    routing_policy = "MULTIVALUE"
  }
  health_check_custom_config {
    failure_threshold = 1
  }
  tags = {
    Service = "postgres"
  }
}

# Redis Service Discovery (for ElastiCache)
resource "aws_service_discovery_service" "redis" {
  name            = "redis"
  description     = "Redis Cache Service Discovery"
  namespace_id    = aws_service_discovery_private_dns_namespace.ragqa.id
  dns_config {
    namespace_id = aws_service_discovery_private_dns_namespace.ragqa.id
    dns_records {
      ttl  = 300
      type = "A"
    }
    routing_policy = "MULTIVALUE"
  }
  health_check_custom_config {
    failure_threshold = 1
  }
  tags = {
    Service = "redis"
  }
}

# Output service discovery endpoints
output "service_discovery_namespace" {
  description = "Service discovery private DNS namespace"
  value       = aws_service_discovery_private_dns_namespace.ragqa.name
}

output "service_discovery_services" {
  description = "Map of service discovery service ARNs"
  value = {
    api_gateway         = aws_service_discovery_service.api_gateway.arn
    rag_service         = aws_service_discovery_service.rag_service.arn
    llm_service         = aws_service_discovery_service.llm_service.arn
    speech_service      = aws_service_discovery_service.speech_service.arn
    translation_service = aws_service_discovery_service.translation_service.arn
    ocr_service         = aws_service_discovery_service.ocr_service.arn
    data_ingestion      = aws_service_discovery_service.data_ingestion.arn
    model_training      = aws_service_discovery_service.model_training.arn
    chat_widget         = aws_service_discovery_service.chat_widget.arn
    search_page         = aws_service_discovery_service.search_page.arn
    admin_dashboard     = aws_service_discovery_service.admin_dashboard.arn
    milvus              = aws_service_discovery_service.milvus.arn
    langfuse            = aws_service_discovery_service.langfuse.arn
    grafana             = aws_service_discovery_service.grafana.arn
    prometheus          = aws_service_discovery_service.prometheus.arn
    postgres            = aws_service_discovery_service.postgres.arn
    redis               = aws_service_discovery_service.redis.arn
  }
}
