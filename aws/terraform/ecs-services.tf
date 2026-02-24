# ECS Services Configuration
# Defines all application services with proper clustering, load balancing, and service discovery

locals {
  service_configs = {
    api_gateway = {
      name                = "api-gateway"
      container_name      = "api-gateway"
      port                = 8000
      desired_count       = 2
      launch_type         = "FARGATE"
      requires_lb         = true
      health_check_path   = "/health"
      cpu                 = "2048"
      memory              = "4096"
    }
    rag_service = {
      name                = "rag-service"
      container_name      = "rag-service"
      port                = 8001
      desired_count       = 1
      launch_type         = "FARGATE"
      requires_lb         = false
      health_check_path   = "/health"
      cpu                 = "4096"
      memory              = "16384"
    }
    llm_service = {
      name                = "llm-service"
      container_name      = "llm-service"
      port                = 8002
      desired_count       = 1
      launch_type         = "EC2"
      requires_lb         = false
      health_check_path   = "/health"
      instance_type       = "g5.2xlarge"
    }
    speech_service = {
      name                = "speech-service"
      container_name      = "speech-service"
      port                = 8003
      desired_count       = 1
      launch_type         = "EC2"
      requires_lb         = false
      health_check_path   = "/health"
      instance_type       = "g5.2xlarge"
    }
    translation_service = {
      name                = "translation-service"
      container_name      = "translation-service"
      port                = 8004
      desired_count       = 1
      launch_type         = "EC2"
      requires_lb         = false
      health_check_path   = "/health"
      instance_type       = "g5.2xlarge"
    }
    ocr_service = {
      name                = "ocr-service"
      container_name      = "ocr-service"
      port                = 8005
      desired_count       = 1
      launch_type         = "FARGATE"
      requires_lb         = false
      health_check_path   = "/health"
      cpu                 = "2048"
      memory              = "8192"
    }
    data_ingestion = {
      name                = "data-ingestion"
      container_name      = "data-ingestion"
      port                = 8006
      desired_count       = 1
      launch_type         = "FARGATE"
      requires_lb         = false
      health_check_path   = "/health"
      cpu                 = "2048"
      memory              = "4096"
    }
    model_training = {
      name                = "model-training"
      container_name      = "model-training"
      port                = 8007
      desired_count       = 0
      launch_type         = "EC2"
      requires_lb         = false
      health_check_path   = "/health"
      instance_type       = "g5.2xlarge"
    }
    chat_widget = {
      name                = "chat-widget"
      container_name      = "chat-widget"
      port                = 80
      desired_count       = 2
      launch_type         = "FARGATE"
      requires_lb         = true
      health_check_path   = "/health"
      cpu                 = "512"
      memory              = "1024"
      path_pattern        = ["/widget/*"]
    }
    search_page = {
      name                = "search-page"
      container_name      = "search-page"
      port                = 80
      desired_count       = 2
      launch_type         = "FARGATE"
      requires_lb         = true
      health_check_path   = "/health"
      cpu                 = "512"
      memory              = "1024"
      path_pattern        = ["/search/*"]
    }
    admin_dashboard = {
      name                = "admin-dashboard"
      container_name      = "admin-dashboard"
      port                = 80
      desired_count       = 2
      launch_type         = "FARGATE"
      requires_lb         = true
      health_check_path   = "/health"
      cpu                 = "512"
      memory              = "1024"
      path_pattern        = ["/admin/*"]
    }
    milvus = {
      name                = "milvus"
      container_name      = "milvus"
      port                = 19530
      desired_count       = 1
      launch_type         = "FARGATE"
      requires_lb         = false
      health_check_path   = "/healthz"
      cpu                 = "4096"
      memory              = "16384"
    }
    langfuse = {
      name                = "langfuse"
      container_name      = "langfuse"
      port                = 3001
      desired_count       = 1
      launch_type         = "FARGATE"
      requires_lb         = true
      health_check_path   = "/health"
      cpu                 = "1024"
      memory              = "2048"
      path_pattern        = ["/langfuse/*"]
    }
    grafana = {
      name                = "grafana"
      container_name      = "grafana"
      port                = 3000
      desired_count       = 1
      launch_type         = "FARGATE"
      requires_lb         = true
      health_check_path   = "/api/health"
      cpu                 = "512"
      memory              = "1024"
      path_pattern        = ["/grafana/*"]
    }
    prometheus = {
      name                = "prometheus"
      container_name      = "prometheus"
      port                = 9090
      desired_count       = 1
      launch_type         = "FARGATE"
      requires_lb         = true
      health_check_path   = "/-/healthy"
      cpu                 = "512"
      memory              = "1024"
      path_pattern        = ["/prometheus/*"]
    }
  }
}

# API Gateway Service
resource "aws_ecs_service" "api_gateway" {
  name            = "ragqa-api-gateway"
  cluster         = aws_ecs_cluster.main.id
  task_definition = aws_ecs_task_definition.api_gateway.arn
  desired_count   = local.service_configs.api_gateway.desired_count
  launch_type     = local.service_configs.api_gateway.launch_type

  network_configuration {
    subnets          = var.private_subnets
    security_groups  = [aws_security_group.ecs_tasks.id]
    assign_public_ip = false
  }

  load_balancer {
    target_group_arn = aws_lb_target_group.api_gateway.arn
    container_name   = local.service_configs.api_gateway.container_name
    container_port   = local.service_configs.api_gateway.port
  }

  service_registries {
    registry_arn = aws_service_discovery_service.api_gateway.arn
  }

  depends_on = [
    aws_lb_listener.http,
    aws_iam_role_policy.ecs_task_execution_role_policy,
    aws_iam_role_policy.ecs_task_role_policy
  ]

  tags = {
    Service = local.service_configs.api_gateway.name
  }
}

# RAG Service
resource "aws_ecs_service" "rag_service" {
  name            = "ragqa-rag-service"
  cluster         = aws_ecs_cluster.main.id
  task_definition = aws_ecs_task_definition.rag_service.arn
  desired_count   = local.service_configs.rag_service.desired_count
  launch_type     = local.service_configs.rag_service.launch_type

  network_configuration {
    subnets          = var.private_subnets
    security_groups  = [aws_security_group.ecs_tasks.id]
    assign_public_ip = false
  }

  service_registries {
    registry_arn = aws_service_discovery_service.rag_service.arn
  }

  depends_on = [
    aws_iam_role_policy.ecs_task_execution_role_policy,
    aws_iam_role_policy.ecs_task_role_policy
  ]

  tags = {
    Service = local.service_configs.rag_service.name
  }
}

# LLM Service (EC2)
resource "aws_ecs_service" "llm_service" {
  name            = "ragqa-llm-service"
  cluster         = aws_ecs_cluster.main.id
  task_definition = aws_ecs_task_definition.llm_service.arn
  desired_count   = local.service_configs.llm_service.desired_count
  launch_type     = local.service_configs.llm_service.launch_type

  network_configuration {
    subnets          = var.private_subnets
    security_groups  = [aws_security_group.ecs_tasks.id]
    assign_public_ip = false
  }

  service_registries {
    registry_arn = aws_service_discovery_service.llm_service.arn
  }

  depends_on = [
    aws_iam_role_policy.ecs_task_execution_role_policy,
    aws_iam_role_policy.ecs_task_role_policy
  ]

  tags = {
    Service = local.service_configs.llm_service.name
  }
}

# Speech Service (EC2)
resource "aws_ecs_service" "speech_service" {
  name            = "ragqa-speech-service"
  cluster         = aws_ecs_cluster.main.id
  task_definition = aws_ecs_task_definition.speech_service.arn
  desired_count   = local.service_configs.speech_service.desired_count
  launch_type     = local.service_configs.speech_service.launch_type

  network_configuration {
    subnets          = var.private_subnets
    security_groups  = [aws_security_group.ecs_tasks.id]
    assign_public_ip = false
  }

  service_registries {
    registry_arn = aws_service_discovery_service.speech_service.arn
  }

  depends_on = [
    aws_iam_role_policy.ecs_task_execution_role_policy,
    aws_iam_role_policy.ecs_task_role_policy
  ]

  tags = {
    Service = local.service_configs.speech_service.name
  }
}

# Translation Service (EC2)
resource "aws_ecs_service" "translation_service" {
  name            = "ragqa-translation-service"
  cluster         = aws_ecs_cluster.main.id
  task_definition = aws_ecs_task_definition.translation_service.arn
  desired_count   = local.service_configs.translation_service.desired_count
  launch_type     = local.service_configs.translation_service.launch_type

  network_configuration {
    subnets          = var.private_subnets
    security_groups  = [aws_security_group.ecs_tasks.id]
    assign_public_ip = false
  }

  service_registries {
    registry_arn = aws_service_discovery_service.translation_service.arn
  }

  depends_on = [
    aws_iam_role_policy.ecs_task_execution_role_policy,
    aws_iam_role_policy.ecs_task_role_policy
  ]

  tags = {
    Service = local.service_configs.translation_service.name
  }
}

# OCR Service
resource "aws_ecs_service" "ocr_service" {
  name            = "ragqa-ocr-service"
  cluster         = aws_ecs_cluster.main.id
  task_definition = aws_ecs_task_definition.ocr_service.arn
  desired_count   = local.service_configs.ocr_service.desired_count
  launch_type     = local.service_configs.ocr_service.launch_type

  network_configuration {
    subnets          = var.private_subnets
    security_groups  = [aws_security_group.ecs_tasks.id]
    assign_public_ip = false
  }

  service_registries {
    registry_arn = aws_service_discovery_service.ocr_service.arn
  }

  depends_on = [
    aws_iam_role_policy.ecs_task_execution_role_policy,
    aws_iam_role_policy.ecs_task_role_policy
  ]

  tags = {
    Service = local.service_configs.ocr_service.name
  }
}

# Data Ingestion Service
resource "aws_ecs_service" "data_ingestion" {
  name            = "ragqa-data-ingestion"
  cluster         = aws_ecs_cluster.main.id
  task_definition = aws_ecs_task_definition.data_ingestion.arn
  desired_count   = local.service_configs.data_ingestion.desired_count
  launch_type     = local.service_configs.data_ingestion.launch_type

  network_configuration {
    subnets          = var.private_subnets
    security_groups  = [aws_security_group.ecs_tasks.id]
    assign_public_ip = false
  }

  service_registries {
    registry_arn = aws_service_discovery_service.data_ingestion.arn
  }

  depends_on = [
    aws_iam_role_policy.ecs_task_execution_role_policy,
    aws_iam_role_policy.ecs_task_role_policy
  ]

  tags = {
    Service = local.service_configs.data_ingestion.name
  }
}

# Model Training Service
resource "aws_ecs_service" "model_training" {
  name            = "ragqa-model-training"
  cluster         = aws_ecs_cluster.main.id
  task_definition = aws_ecs_task_definition.model_training.arn
  desired_count   = local.service_configs.model_training.desired_count
  launch_type     = local.service_configs.model_training.launch_type

  network_configuration {
    subnets          = var.private_subnets
    security_groups  = [aws_security_group.ecs_tasks.id]
    assign_public_ip = false
  }

  service_registries {
    registry_arn = aws_service_discovery_service.model_training.arn
  }

  depends_on = [
    aws_iam_role_policy.ecs_task_execution_role_policy,
    aws_iam_role_policy.ecs_task_role_policy
  ]

  tags = {
    Service = local.service_configs.model_training.name
  }
}

# Chat Widget Service
resource "aws_ecs_service" "chat_widget" {
  name            = "ragqa-chat-widget"
  cluster         = aws_ecs_cluster.main.id
  task_definition = aws_ecs_task_definition.chat_widget.arn
  desired_count   = local.service_configs.chat_widget.desired_count
  launch_type     = local.service_configs.chat_widget.launch_type

  network_configuration {
    subnets          = var.private_subnets
    security_groups  = [aws_security_group.ecs_tasks.id]
    assign_public_ip = false
  }

  load_balancer {
    target_group_arn = aws_lb_target_group.chat_widget.arn
    container_name   = local.service_configs.chat_widget.container_name
    container_port   = local.service_configs.chat_widget.port
  }

  service_registries {
    registry_arn = aws_service_discovery_service.chat_widget.arn
  }

  depends_on = [
    aws_lb_listener.http,
    aws_iam_role_policy.ecs_task_execution_role_policy
  ]

  tags = {
    Service = local.service_configs.chat_widget.name
  }
}

# Search Page Service
resource "aws_ecs_service" "search_page" {
  name            = "ragqa-search-page"
  cluster         = aws_ecs_cluster.main.id
  task_definition = aws_ecs_task_definition.search_page.arn
  desired_count   = local.service_configs.search_page.desired_count
  launch_type     = local.service_configs.search_page.launch_type

  network_configuration {
    subnets          = var.private_subnets
    security_groups  = [aws_security_group.ecs_tasks.id]
    assign_public_ip = false
  }

  load_balancer {
    target_group_arn = aws_lb_target_group.search_page.arn
    container_name   = local.service_configs.search_page.container_name
    container_port   = local.service_configs.search_page.port
  }

  service_registries {
    registry_arn = aws_service_discovery_service.search_page.arn
  }

  depends_on = [
    aws_lb_listener.http,
    aws_iam_role_policy.ecs_task_execution_role_policy
  ]

  tags = {
    Service = local.service_configs.search_page.name
  }
}

# Admin Dashboard Service
resource "aws_ecs_service" "admin_dashboard" {
  name            = "ragqa-admin-dashboard"
  cluster         = aws_ecs_cluster.main.id
  task_definition = aws_ecs_task_definition.admin_dashboard.arn
  desired_count   = local.service_configs.admin_dashboard.desired_count
  launch_type     = local.service_configs.admin_dashboard.launch_type

  network_configuration {
    subnets          = var.private_subnets
    security_groups  = [aws_security_group.ecs_tasks.id]
    assign_public_ip = false
  }

  load_balancer {
    target_group_arn = aws_lb_target_group.admin_dashboard.arn
    container_name   = local.service_configs.admin_dashboard.container_name
    container_port   = local.service_configs.admin_dashboard.port
  }

  service_registries {
    registry_arn = aws_service_discovery_service.admin_dashboard.arn
  }

  depends_on = [
    aws_lb_listener.http,
    aws_iam_role_policy.ecs_task_execution_role_policy
  ]

  tags = {
    Service = local.service_configs.admin_dashboard.name
  }
}

# Milvus Service
resource "aws_ecs_service" "milvus" {
  name            = "ragqa-milvus"
  cluster         = aws_ecs_cluster.main.id
  task_definition = aws_ecs_task_definition.milvus.arn
  desired_count   = local.service_configs.milvus.desired_count
  launch_type     = local.service_configs.milvus.launch_type

  network_configuration {
    subnets          = var.private_subnets
    security_groups  = [aws_security_group.ecs_tasks.id]
    assign_public_ip = false
  }

  service_registries {
    registry_arn = aws_service_discovery_service.milvus.arn
  }

  depends_on = [
    aws_iam_role_policy.ecs_task_execution_role_policy
  ]

  tags = {
    Service = local.service_configs.milvus.name
  }
}

# Langfuse Service
resource "aws_ecs_service" "langfuse" {
  name            = "ragqa-langfuse"
  cluster         = aws_ecs_cluster.main.id
  task_definition = aws_ecs_task_definition.langfuse.arn
  desired_count   = local.service_configs.langfuse.desired_count
  launch_type     = local.service_configs.langfuse.launch_type

  network_configuration {
    subnets          = var.private_subnets
    security_groups  = [aws_security_group.ecs_tasks.id]
    assign_public_ip = false
  }

  load_balancer {
    target_group_arn = aws_lb_target_group.langfuse.arn
    container_name   = local.service_configs.langfuse.container_name
    container_port   = local.service_configs.langfuse.port
  }

  service_registries {
    registry_arn = aws_service_discovery_service.langfuse.arn
  }

  depends_on = [
    aws_lb_listener.http,
    aws_iam_role_policy.ecs_task_execution_role_policy
  ]

  tags = {
    Service = local.service_configs.langfuse.name
  }
}

# Grafana Service
resource "aws_ecs_service" "grafana" {
  name            = "ragqa-grafana"
  cluster         = aws_ecs_cluster.main.id
  task_definition = aws_ecs_task_definition.grafana.arn
  desired_count   = local.service_configs.grafana.desired_count
  launch_type     = local.service_configs.grafana.launch_type

  network_configuration {
    subnets          = var.private_subnets
    security_groups  = [aws_security_group.ecs_tasks.id]
    assign_public_ip = false
  }

  load_balancer {
    target_group_arn = aws_lb_target_group.grafana.arn
    container_name   = local.service_configs.grafana.container_name
    container_port   = local.service_configs.grafana.port
  }

  service_registries {
    registry_arn = aws_service_discovery_service.grafana.arn
  }

  depends_on = [
    aws_lb_listener.http,
    aws_iam_role_policy.ecs_task_execution_role_policy
  ]

  tags = {
    Service = local.service_configs.grafana.name
  }
}

# Prometheus Service
resource "aws_ecs_service" "prometheus" {
  name            = "ragqa-prometheus"
  cluster         = aws_ecs_cluster.main.id
  task_definition = aws_ecs_task_definition.prometheus.arn
  desired_count   = local.service_configs.prometheus.desired_count
  launch_type     = local.service_configs.prometheus.launch_type

  network_configuration {
    subnets          = var.private_subnets
    security_groups  = [aws_security_group.ecs_tasks.id]
    assign_public_ip = false
  }

  load_balancer {
    target_group_arn = aws_lb_target_group.prometheus.arn
    container_name   = local.service_configs.prometheus.container_name
    container_port   = local.service_configs.prometheus.port
  }

  service_registries {
    registry_arn = aws_service_discovery_service.prometheus.arn
  }

  depends_on = [
    aws_lb_listener.http,
    aws_iam_role_policy.ecs_task_execution_role_policy
  ]

  tags = {
    Service = local.service_configs.prometheus.name
  }
}

# Auto Scaling for Fargate Services
resource "aws_appautoscaling_target" "api_gateway_target" {
  max_capacity       = 4
  min_capacity       = 2
  resource_id        = "service/${aws_ecs_cluster.main.name}/${aws_ecs_service.api_gateway.name}"
  scalable_dimension = "ecs:service:DesiredCount"
  service_namespace  = "ecs"
}

resource "aws_appautoscaling_policy" "api_gateway_cpu" {
  policy_name            = "api-gateway-cpu-autoscaling"
  policy_type            = "TargetTrackingScaling"
  resource_id            = aws_appautoscaling_target.api_gateway_target.resource_id
  scalable_dimension     = aws_appautoscaling_target.api_gateway_target.scalable_dimension
  service_namespace      = aws_appautoscaling_target.api_gateway_target.service_namespace
  target_tracking_scaling_policy_configuration {
    predefined_metric_specification {
      predefined_metric_type = "ECSServiceAverageCPUUtilization"
    }
    target_value = 70.0
  }
}

resource "aws_appautoscaling_policy" "api_gateway_memory" {
  policy_name            = "api-gateway-memory-autoscaling"
  policy_type            = "TargetTrackingScaling"
  resource_id            = aws_appautoscaling_target.api_gateway_target.resource_id
  scalable_dimension     = aws_appautoscaling_target.api_gateway_target.scalable_dimension
  service_namespace      = aws_appautoscaling_target.api_gateway_target.service_namespace
  target_tracking_scaling_policy_configuration {
    predefined_metric_specification {
      predefined_metric_type = "ECSServiceAverageMemoryUtilization"
    }
    target_value = 80.0
  }
}
