# ECS Cluster
resource "aws_ecs_cluster" "main" {
  name = "${var.project_name}-cluster"

  setting {
    name  = "containerInsights"
    value = "enabled"
  }

  tags = {
    Name   = "${var.project_name}-cluster"
    Stream = "Container"
  }
}

# CloudWatch Log Group for ECS
resource "aws_cloudwatch_log_group" "ecs" {
  name              = "/ecs/${var.project_name}"
  retention_in_days = var.cloudwatch_log_retention_days

  tags = {
    Name   = "${var.project_name}-ecs-logs"
    Stream = "Monitoring"
  }
}

# ECS Cluster Capacity Providers
resource "aws_ecs_cluster_capacity_providers" "main" {
  cluster_name = aws_ecs_cluster.main.name

  capacity_providers = ["FARGATE", "FARGATE_SPOT", aws_autoscaling_group.gpu_instances.name]

  default_capacity_provider_strategy {
    base              = 1
    weight            = 100
    capacity_provider = "FARGATE"
  }
}

# EC2 Launch Template for GPU instances
resource "aws_launch_template" "gpu_instances" {
  name_prefix   = "${var.project_name}-gpu-"
  image_id      = data.aws_ami.ecs_gpu_ami.id
  instance_type = var.gpu_instance_type

  iam_instance_profile {
    arn = aws_iam_instance_profile.ec2_gpu.arn
  }

  network_interfaces {
    associate_public_ip_address = false
    security_groups             = [aws_security_group.gpu.id]
    delete_on_termination       = true
  }

  tag_specifications {
    resource_type = "instance"
    tags = {
      Name   = "${var.project_name}-gpu-instance"
      Stream = "Container"
    }
  }

  tag_specifications {
    resource_type = "volume"
    tags = {
      Name   = "${var.project_name}-gpu-volume"
      Stream = "Storage"
    }
  }

  user_data = base64encode(templatefile("${path.module}/user_data.sh", {
    ecs_cluster_name = aws_ecs_cluster.main.name
  }))

  monitoring {
    enabled = true
  }

  lifecycle {
    create_before_destroy = true
  }
}

# Auto Scaling Group for GPU instances
resource "aws_autoscaling_group" "gpu_instances" {
  name                = "${var.project_name}-gpu-asg"
  vpc_zone_identifier = [aws_subnet.private_1.id, aws_subnet.private_2.id]
  min_size            = var.min_gpu_instances
  max_size            = var.max_gpu_instances
  desired_capacity    = var.min_gpu_instances

  launch_template {
    id      = aws_launch_template.gpu_instances.id
    version = "$Latest"
  }

  health_check_type         = "ELB"
  health_check_grace_period = 300

  tag {
    key                 = "Name"
    value               = "${var.project_name}-gpu-instance"
    propagate_at_launch = true
  }

  tag {
    key                 = "Cluster"
    value               = aws_ecs_cluster.main.name
    propagate_at_launch = true
  }

  lifecycle {
    create_before_destroy = true
  }

  depends_on = [aws_iam_instance_profile.ec2_gpu]
}

# CloudWatch Alarm for GPU ASG
resource "aws_cloudwatch_metric_alarm" "gpu_asg_cpu" {
  alarm_name          = "${var.project_name}-gpu-asg-cpu-high"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = 2
  metric_name         = "CPUUtilization"
  namespace           = "AWS/EC2"
  period              = 300
  statistic           = "Average"
  threshold           = 80
  alarm_description   = "GPU ASG CPU utilization is high"
  alarm_actions       = [aws_sns_topic.alerts.arn]

  dimensions = {
    AutoScalingGroupName = aws_autoscaling_group.gpu_instances.name
  }

  tags = {
    Name   = "${var.project_name}-gpu-asg-cpu-alarm"
    Stream = "Monitoring"
  }
}

# API Gateway ECS Task Definition
resource "aws_ecs_task_definition" "api_gateway" {
  family                   = "${var.project_name}-api-gateway"
  network_mode             = "awsvpc"
  requires_compatibilities = ["FARGATE"]
  cpu                      = var.services["api-gateway"].cpu
  memory                   = var.services["api-gateway"].memory

  execution_role_arn = aws_iam_role.ecs_task_execution_role.arn
  task_role_arn      = aws_iam_role.ecs_task_role.arn

  container_definitions = jsonencode([
    {
      name      = "api-gateway"
      image     = "${aws_ecr_repository.api_gateway.repository_url}:latest"
      essential = true
      portMappings = [
        {
          containerPort = var.services["api-gateway"].port
          hostPort      = var.services["api-gateway"].port
          protocol      = "tcp"
        }
      ]

      environment = [
        {
          name  = "REDIS_HOST"
          value = aws_elasticache_cluster.main.cache_nodes[0].address
        },
        {
          name  = "REDIS_PORT"
          value = tostring(aws_elasticache_cluster.main.port)
        },
        {
          name  = "DB_HOST"
          value = aws_db_instance.main.address
        },
        {
          name  = "DB_PORT"
          value = tostring(aws_db_instance.main.port)
        },
        {
          name  = "DB_NAME"
          value = aws_db_instance.main.db_name
        },
        {
          name  = "MILVUS_HOST"
          value = "milvus"
        },
        {
          name  = "MILVUS_PORT"
          value = "19530"
        }
      ]

      secrets = [
        {
          name      = "REDIS_PASSWORD"
          valueFrom = "${aws_secretsmanager_secret.redis_auth_token.arn}:password::"
        },
        {
          name      = "DB_USER"
          valueFrom = "${aws_secretsmanager_secret.rds_password.arn}:username::"
        },
        {
          name      = "DB_PASSWORD"
          valueFrom = "${aws_secretsmanager_secret.rds_password.arn}:password::"
        },
        {
          name      = "JWT_SECRET"
          valueFrom = aws_secretsmanager_secret.jwt_secret.arn
        }
      ]

      logConfiguration = {
        logDriver = "awslogs"
        options = {
          "awslogs-group"         = aws_cloudwatch_log_group.ecs.name
          "awslogs-region"        = var.aws_region
          "awslogs-stream-prefix" = "api-gateway"
        }
      }
    }
  ])

  tags = {
    Name   = "${var.project_name}-api-gateway-task"
    Stream = "Container"
  }
}

# API Gateway ECS Service
resource "aws_ecs_service" "api_gateway" {
  name            = "${var.project_name}-api-gateway"
  cluster         = aws_ecs_cluster.main.id
  task_definition = aws_ecs_task_definition.api_gateway.arn
  desired_count   = var.services["api-gateway"].desired_count
  launch_type     = "FARGATE"

  network_configuration {
    subnets          = [aws_subnet.private_1.id, aws_subnet.private_2.id]
    security_groups  = [aws_security_group.ecs_backend.id]
    assign_public_ip = false
  }

  load_balancer {
    target_group_arn = aws_lb_target_group.api_gateway.arn
    container_name   = "api-gateway"
    container_port   = var.services["api-gateway"].port
  }

  depends_on = [
    aws_lb_listener.https,
    aws_iam_role_policy.ecs_task_execution_ecr_kms
  ]

  tags = {
    Name   = "${var.project_name}-api-gateway-service"
    Stream = "Container"
  }
}

# Auto Scaling for API Gateway
resource "aws_appautoscaling_target" "api_gateway" {
  max_capacity       = 4
  min_capacity       = var.services["api-gateway"].desired_count
  resource_id        = "service/${aws_ecs_cluster.main.name}/${aws_ecs_service.api_gateway.name}"
  scalable_dimension = "ecs:service:DesiredCount"
  service_namespace  = "ecs"
}

resource "aws_appautoscaling_policy" "api_gateway_cpu" {
  name               = "${var.project_name}-api-gateway-cpu-scaling"
  policy_type        = "TargetTrackingScaling"
  resource_id        = aws_appautoscaling_target.api_gateway.resource_id
  scalable_dimension = aws_appautoscaling_target.api_gateway.scalable_dimension
  service_namespace  = aws_appautoscaling_target.api_gateway.service_namespace

  target_tracking_scaling_policy_configuration {
    predefined_metric_specification {
      predefined_metric_type = "ECSServiceAverageCPUUtilization"
    }
    target_value = 70.0
  }
}

resource "aws_appautoscaling_policy" "api_gateway_memory" {
  name               = "${var.project_name}-api-gateway-memory-scaling"
  policy_type        = "TargetTrackingScaling"
  resource_id        = aws_appautoscaling_target.api_gateway.resource_id
  scalable_dimension = aws_appautoscaling_target.api_gateway.scalable_dimension
  service_namespace  = aws_appautoscaling_target.api_gateway.service_namespace

  target_tracking_scaling_policy_configuration {
    predefined_metric_specification {
      predefined_metric_type = "ECSServiceAverageMemoryUtilization"
    }
    target_value = 80.0
  }
}

# Chat Widget ECS Task Definition
resource "aws_ecs_task_definition" "chat_widget" {
  family                   = "${var.project_name}-chat-widget"
  network_mode             = "awsvpc"
  requires_compatibilities = ["FARGATE"]
  cpu                      = var.services["chat-widget"].cpu
  memory                   = var.services["chat-widget"].memory

  execution_role_arn = aws_iam_role.ecs_task_execution_role.arn
  task_role_arn      = aws_iam_role.ecs_task_role.arn

  container_definitions = jsonencode([
    {
      name      = "chat-widget"
      image     = "${aws_ecr_repository.chat_widget.repository_url}:latest"
      essential = true
      portMappings = [
        {
          containerPort = var.services["chat-widget"].port
          hostPort      = var.services["chat-widget"].port
          protocol      = "tcp"
        }
      ]

      environment = [
        {
          name  = "API_GATEWAY_URL"
          value = "http://api-gateway:${var.services["api-gateway"].port}"
        }
      ]

      logConfiguration = {
        logDriver = "awslogs"
        options = {
          "awslogs-group"         = aws_cloudwatch_log_group.ecs.name
          "awslogs-region"        = var.aws_region
          "awslogs-stream-prefix" = "chat-widget"
        }
      }
    }
  ])

  tags = {
    Name   = "${var.project_name}-chat-widget-task"
    Stream = "Container"
  }
}

# Chat Widget ECS Service
resource "aws_ecs_service" "chat_widget" {
  name            = "${var.project_name}-chat-widget"
  cluster         = aws_ecs_cluster.main.id
  task_definition = aws_ecs_task_definition.chat_widget.arn
  desired_count   = var.services["chat-widget"].desired_count
  launch_type     = "FARGATE"

  network_configuration {
    subnets          = [aws_subnet.private_1.id, aws_subnet.private_2.id]
    security_groups  = [aws_security_group.ecs_frontend.id]
    assign_public_ip = false
  }

  load_balancer {
    target_group_arn = aws_lb_target_group.chat_widget.arn
    container_name   = "chat-widget"
    container_port   = var.services["chat-widget"].port
  }

  depends_on = [
    aws_lb_listener.https,
    aws_iam_role_policy.ecs_task_execution_ecr_kms
  ]

  tags = {
    Name   = "${var.project_name}-chat-widget-service"
    Stream = "Container"
  }
}

# Auto Scaling for Chat Widget
resource "aws_appautoscaling_target" "chat_widget" {
  max_capacity       = 4
  min_capacity       = var.services["chat-widget"].desired_count
  resource_id        = "service/${aws_ecs_cluster.main.name}/${aws_ecs_service.chat_widget.name}"
  scalable_dimension = "ecs:service:DesiredCount"
  service_namespace  = "ecs"
}

resource "aws_appautoscaling_policy" "chat_widget_cpu" {
  name               = "${var.project_name}-chat-widget-cpu-scaling"
  policy_type        = "TargetTrackingScaling"
  resource_id        = aws_appautoscaling_target.chat_widget.resource_id
  scalable_dimension = aws_appautoscaling_target.chat_widget.scalable_dimension
  service_namespace  = aws_appautoscaling_target.chat_widget.service_namespace

  target_tracking_scaling_policy_configuration {
    predefined_metric_specification {
      predefined_metric_type = "ECSServiceAverageCPUUtilization"
    }
    target_value = 70.0
  }
}
