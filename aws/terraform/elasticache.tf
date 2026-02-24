# ElastiCache Subnet Group
resource "aws_elasticache_subnet_group" "main" {
  name       = "${var.project_name}-cache-subnet-group"
  subnet_ids = [aws_subnet.private_1.id, aws_subnet.private_2.id]

  tags = {
    Name   = "${var.project_name}-cache-subnet-group"
    Stream = "Cache"
  }
}

# ElastiCache Parameter Group for Redis
resource "aws_elasticache_parameter_group" "main" {
  family      = "redis7"
  name        = "${var.project_name}-redis-params"
  description = "Parameter group for Redis cluster"

  # Performance and memory optimization
  parameter {
    name  = "maxmemory-policy"
    value = "allkeys-lru"
  }

  parameter {
    name  = "timeout"
    value = "300"
  }

  parameter {
    name  = "tcp-keepalive"
    value = "300"
  }

  parameter {
    name  = "databases"
    value = "16"
  }

  # Replication configuration
  parameter {
    name  = "repl-diskless-sync"
    value = "yes"
  }

  parameter {
    name  = "repl-diskless-sync-delay"
    value = "5"
  }

  tags = {
    Name   = "${var.project_name}-redis-params"
    Stream = "Cache"
  }
}

# ElastiCache Redis Cluster (primary cache for application)
resource "aws_elasticache_cluster" "main" {
  cluster_id           = "${var.project_name}-redis-main"
  engine               = "redis"
  engine_version       = "7.2"
  node_type            = var.cache_instance_type
  num_cache_nodes      = 2 # Primary + replica
  parameter_group_name = aws_elasticache_parameter_group.main.name
  port                 = 6379

  automatic_failover_enabled = true
  multi_az_enabled           = true

  security_group_ids = [aws_security_group.elasticache.id]
  subnet_group_name  = aws_elasticache_subnet_group.main.name

  # Encryption
  at_rest_encryption_enabled = true
  transit_encryption_enabled = true
  auth_token                 = random_password.redis_auth_token.result
  transit_encryption_mode    = "preferred"

  # Backup and maintenance
  snapshot_retention_limit = var.redis_snapshot_retention_days
  snapshot_window          = "03:00-04:00"
  maintenance_window       = "sun:04:30-sun:05:30"

  # Logging
  log_delivery_configuration {
    destination      = aws_cloudwatch_log_group.redis_slow_log.name
    destination_type = "cloudwatch-logs"
    log_format       = "json"
    log_type         = "slow-log"
    enabled          = true
  }

  log_delivery_configuration {
    destination      = aws_cloudwatch_log_group.redis_engine_log.name
    destination_type = "cloudwatch-logs"
    log_format       = "json"
    log_type         = "engine-log"
    enabled          = true
  }

  auto_minor_version_upgrade = true
  notification_topic_arn     = aws_sns_topic.alerts.arn

  tags = {
    Name   = "${var.project_name}-redis-main"
    Stream = "Cache"
  }

  depends_on = [aws_cloudwatch_log_group.redis_slow_log, aws_cloudwatch_log_group.redis_engine_log]
}

# Random password for Redis AUTH
resource "random_password" "redis_auth_token" {
  length  = 32
  special = false # Redis AUTH tokens cannot contain special characters
}

# Store Redis password in Secrets Manager
resource "aws_secretsmanager_secret" "redis_auth_token" {
  name                    = "${var.project_name}/redis/auth-token"
  recovery_window_in_days = 7

  tags = {
    Name   = "${var.project_name}-redis-auth-token"
    Stream = "Secrets"
  }
}

resource "aws_secretsmanager_secret_version" "redis_auth_token" {
  secret_id = aws_secretsmanager_secret.redis_auth_token.id
  secret_string = jsonencode({
    auth_token = random_password.redis_auth_token.result
    host       = aws_elasticache_cluster.main.cache_nodes[0].address
    port       = aws_elasticache_cluster.main.port
    engine     = "redis"
    databases  = "4" # We use 0-3
  })
}

# CloudWatch Log Groups for Redis
resource "aws_cloudwatch_log_group" "redis_slow_log" {
  name              = "/aws/elasticache/${var.project_name}/redis/slow-log"
  retention_in_days = var.cloudwatch_log_retention_days

  tags = {
    Name   = "${var.project_name}-redis-slow-log"
    Stream = "Monitoring"
  }
}

resource "aws_cloudwatch_log_group" "redis_engine_log" {
  name              = "/aws/elasticache/${var.project_name}/redis/engine-log"
  retention_in_days = var.cloudwatch_log_retention_days

  tags = {
    Name   = "${var.project_name}-redis-engine-log"
    Stream = "Monitoring"
  }
}

# CloudWatch Alarms for Redis
resource "aws_cloudwatch_metric_alarm" "redis_cpu" {
  alarm_name          = "${var.project_name}-redis-cpu-high"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = 2
  metric_name         = "CPUUtilization"
  namespace           = "AWS/ElastiCache"
  period              = 300
  statistic           = "Average"
  threshold           = 80
  alarm_description   = "Redis CPU utilization is high"
  alarm_actions       = [aws_sns_topic.alerts.arn]

  dimensions = {
    CacheClusterId = aws_elasticache_cluster.main.cluster_id
  }

  tags = {
    Name   = "${var.project_name}-redis-cpu-alarm"
    Stream = "Monitoring"
  }
}

resource "aws_cloudwatch_metric_alarm" "redis_memory" {
  alarm_name          = "${var.project_name}-redis-memory-high"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = 2
  metric_name         = "DatabaseMemoryUsagePercentage"
  namespace           = "AWS/ElastiCache"
  period              = 300
  statistic           = "Average"
  threshold           = 80
  alarm_description   = "Redis memory utilization is high"
  alarm_actions       = [aws_sns_topic.alerts.arn]

  dimensions = {
    CacheClusterId = aws_elasticache_cluster.main.cluster_id
  }

  tags = {
    Name   = "${var.project_name}-redis-memory-alarm"
    Stream = "Monitoring"
  }
}

resource "aws_cloudwatch_metric_alarm" "redis_evictions" {
  alarm_name          = "${var.project_name}-redis-evictions"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = 1
  metric_name         = "Evictions"
  namespace           = "AWS/ElastiCache"
  period              = 300
  statistic           = "Sum"
  threshold           = 100
  alarm_description   = "Redis evictions detected - memory pressure"
  alarm_actions       = [aws_sns_topic.alerts.arn]

  dimensions = {
    CacheClusterId = aws_elasticache_cluster.main.cluster_id
  }

  tags = {
    Name   = "${var.project_name}-redis-evictions-alarm"
    Stream = "Monitoring"
  }
}

resource "aws_cloudwatch_metric_alarm" "redis_replication_lag" {
  alarm_name          = "${var.project_name}-redis-replication-lag"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = 2
  metric_name         = "ReplicationLag"
  namespace           = "AWS/ElastiCache"
  period              = 60
  statistic           = "Maximum"
  threshold           = 10 # seconds
  alarm_description   = "Redis replication lag is high"
  alarm_actions       = [aws_sns_topic.alerts.arn]

  dimensions = {
    CacheClusterId = aws_elasticache_cluster.main.cluster_id
  }

  tags = {
    Name   = "${var.project_name}-redis-replication-lag-alarm"
    Stream = "Monitoring"
  }
}

# Note: Database allocation details
# Database 0: Cache (query results, embeddings cache)
# Database 1: Rate limiting
# Database 2: Session storage
# Database 3: Translation cache
