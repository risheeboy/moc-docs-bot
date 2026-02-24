# CloudWatch Log Groups for each ECS service
resource "aws_cloudwatch_log_group" "api_gateway" {
  name              = "/ecs/${var.project_name}/api-gateway"
  retention_in_days = var.cloudwatch_log_retention_days

  tags = {
    Name   = "${var.project_name}-api-gateway-logs"
    Stream = "Monitoring"
  }
}

resource "aws_cloudwatch_log_group" "rag_service" {
  name              = "/ecs/${var.project_name}/rag-service"
  retention_in_days = var.cloudwatch_log_retention_days

  tags = {
    Name   = "${var.project_name}-rag-service-logs"
    Stream = "Monitoring"
  }
}

resource "aws_cloudwatch_log_group" "llm_service" {
  name              = "/ecs/${var.project_name}/llm-service"
  retention_in_days = var.cloudwatch_log_retention_days

  tags = {
    Name   = "${var.project_name}-llm-service-logs"
    Stream = "Monitoring"
  }
}

resource "aws_cloudwatch_log_group" "speech_service" {
  name              = "/ecs/${var.project_name}/speech-service"
  retention_in_days = var.cloudwatch_log_retention_days

  tags = {
    Name   = "${var.project_name}-speech-service-logs"
    Stream = "Monitoring"
  }
}

resource "aws_cloudwatch_log_group" "translation_service" {
  name              = "/ecs/${var.project_name}/translation-service"
  retention_in_days = var.cloudwatch_log_retention_days

  tags = {
    Name   = "${var.project_name}-translation-service-logs"
    Stream = "Monitoring"
  }
}

resource "aws_cloudwatch_log_group" "ocr_service" {
  name              = "/ecs/${var.project_name}/ocr-service"
  retention_in_days = var.cloudwatch_log_retention_days

  tags = {
    Name   = "${var.project_name}-ocr-service-logs"
    Stream = "Monitoring"
  }
}

resource "aws_cloudwatch_log_group" "data_ingestion" {
  name              = "/ecs/${var.project_name}/data-ingestion"
  retention_in_days = var.cloudwatch_log_retention_days

  tags = {
    Name   = "${var.project_name}-data-ingestion-logs"
    Stream = "Monitoring"
  }
}

resource "aws_cloudwatch_log_group" "model_training" {
  name              = "/ecs/${var.project_name}/model-training"
  retention_in_days = var.cloudwatch_log_retention_days

  tags = {
    Name   = "${var.project_name}-model-training-logs"
    Stream = "Monitoring"
  }
}

resource "aws_cloudwatch_log_group" "chat_widget" {
  name              = "/ecs/${var.project_name}/chat-widget"
  retention_in_days = var.cloudwatch_log_retention_days

  tags = {
    Name   = "${var.project_name}-chat-widget-logs"
    Stream = "Monitoring"
  }
}

resource "aws_cloudwatch_log_group" "search_page" {
  name              = "/ecs/${var.project_name}/search-page"
  retention_in_days = var.cloudwatch_log_retention_days

  tags = {
    Name   = "${var.project_name}-search-page-logs"
    Stream = "Monitoring"
  }
}

resource "aws_cloudwatch_log_group" "admin_dashboard" {
  name              = "/ecs/${var.project_name}/admin-dashboard"
  retention_in_days = var.cloudwatch_log_retention_days

  tags = {
    Name   = "${var.project_name}-admin-dashboard-logs"
    Stream = "Monitoring"
  }
}

resource "aws_cloudwatch_log_group" "milvus" {
  name              = "/ecs/${var.project_name}/milvus"
  retention_in_days = var.cloudwatch_log_retention_days

  tags = {
    Name   = "${var.project_name}-milvus-logs"
    Stream = "Monitoring"
  }
}

resource "aws_cloudwatch_log_group" "langfuse" {
  name              = "/ecs/${var.project_name}/langfuse"
  retention_in_days = var.cloudwatch_log_retention_days

  tags = {
    Name   = "${var.project_name}-langfuse-logs"
    Stream = "Monitoring"
  }
}

# CloudWatch Alarms for ECS Services
resource "aws_cloudwatch_metric_alarm" "ecs_api_gateway_cpu" {
  alarm_name          = "${var.project_name}-ecs-api-gateway-cpu-high"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = 2
  metric_name         = "CPUUtilization"
  namespace           = "AWS/ECS"
  period              = 300
  statistic           = "Average"
  threshold           = 80
  alarm_description   = "ECS API Gateway CPU utilization is high"
  alarm_actions       = [aws_sns_topic.alerts.arn]

  dimensions = {
    ClusterName = aws_ecs_cluster.main.name
    ServiceName = aws_ecs_service.api_gateway.name
  }

  tags = {
    Name   = "${var.project_name}-ecs-api-gateway-cpu-alarm"
    Stream = "Monitoring"
  }
}

resource "aws_cloudwatch_metric_alarm" "ecs_api_gateway_memory" {
  alarm_name          = "${var.project_name}-ecs-api-gateway-memory-high"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = 2
  metric_name         = "MemoryUtilization"
  namespace           = "AWS/ECS"
  period              = 300
  statistic           = "Average"
  threshold           = 80
  alarm_description   = "ECS API Gateway memory utilization is high"
  alarm_actions       = [aws_sns_topic.alerts.arn]

  dimensions = {
    ClusterName = aws_ecs_cluster.main.name
    ServiceName = aws_ecs_service.api_gateway.name
  }

  tags = {
    Name   = "${var.project_name}-ecs-api-gateway-memory-alarm"
    Stream = "Monitoring"
  }
}

# Dashboard for monitoring
resource "aws_cloudwatch_dashboard" "main" {
  dashboard_name = "${var.project_name}-dashboard"

  dashboard_body = jsonencode({
    widgets = [
      {
        type = "metric"
        properties = {
          metrics = [
            ["AWS/ECS", "CPUUtilization", { stat = "Average" }],
            [".", "MemoryUtilization", { stat = "Average" }],
            ["AWS/RDS", "CPUUtilization"],
            ["AWS/ElastiCache", "CPUUtilization"],
            ["AWS/ApplicationELB", "TargetResponseTime"]
          ]
          period = 300
          stat   = "Average"
          region = var.aws_region
          title  = "Infrastructure Overview"
        }
      },
      {
        type = "metric"
        properties = {
          metrics = [
            ["AWS/ApplicationELB", "HTTPCode_Target_5XX_Count"],
            [".", "HTTPCode_Target_4XX_Count"],
            [".", "HTTPCode_ELB_5XX_Count"]
          ]
          period = 60
          stat   = "Sum"
          region = var.aws_region
          title  = "Load Balancer Errors"
        }
      },
      {
        type = "log"
        properties = {
          query   = "fields @timestamp, @message | stats count() by bin(5m)"
          region  = var.aws_region
          title   = "Error Logs"
        }
      }
    ]
  })
}

# CloudWatch Log Groups Insights
resource "aws_cloudwatch_log_group" "insights" {
  name              = "/insights/${var.project_name}"
  retention_in_days = var.cloudwatch_log_retention_days

  tags = {
    Name   = "${var.project_name}-insights"
    Stream = "Monitoring"
  }
}

# Metric Filter for Error Tracking
resource "aws_cloudwatch_log_group_metric_filter" "errors" {
  name           = "${var.project_name}-error-metric-filter"
  log_group_name = aws_cloudwatch_log_group.ecs.name
  filter_pattern = "[time, request_id, level = ERROR*, ...]"

  metric_transformation {
    name      = "${var.project_name}-error-count"
    namespace = "${var.project_name}/Errors"
    value     = "1"
  }
}

resource "aws_cloudwatch_metric_alarm" "error_log_alarm" {
  alarm_name          = "${var.project_name}-error-logs"
  comparison_operator = "GreaterThanOrEqualToThreshold"
  evaluation_periods  = 1
  metric_name         = "${var.project_name}-error-count"
  namespace           = "${var.project_name}/Errors"
  period              = 300
  statistic           = "Sum"
  threshold           = 10
  alarm_description   = "Error logs detected in application"
  alarm_actions       = [aws_sns_topic.alerts.arn]

  tags = {
    Name   = "${var.project_name}-error-log-alarm"
    Stream = "Monitoring"
  }
}
