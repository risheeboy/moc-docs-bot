# RDS Subnet Group
resource "aws_db_subnet_group" "main" {
  name       = "${var.project_name}-db-subnet-group"
  subnet_ids = [aws_subnet.private_1.id, aws_subnet.private_2.id]

  tags = {
    Name   = "${var.project_name}-db-subnet-group"
    Stream = "Database"
  }
}

# RDS PostgreSQL Parameter Group (Main)
resource "aws_db_parameter_group" "main" {
  name   = "${var.project_name}-postgres-params"
  family = "postgres16"

  # Performance and tuning parameters
  parameter {
    name  = "log_min_duration_statement"
    value = "1000"
  }

  parameter {
    name  = "shared_preload_libraries"
    value = "pg_stat_statements"
  }

  parameter {
    name  = "max_connections"
    value = "256"
  }

  parameter {
    name  = "work_mem"
    value = "16384"
  }

  parameter {
    name  = "maintenance_work_mem"
    value = "65536"
  }

  parameter {
    name  = "effective_cache_size"
    value = "262144"
  }

  parameter {
    name  = "random_page_cost"
    value = "1.1"
  }

  parameter {
    name  = "jit"
    value = "on"
  }

  tags = {
    Name   = "${var.project_name}-postgres-params"
    Stream = "Database"
  }
}

# RDS PostgreSQL Instance (Main - for RAG QA system)
resource "aws_db_instance" "main" {
  identifier     = "${var.project_name}-db-main"
  engine         = "postgres"
  engine_version = "16.3"
  instance_class = var.db_instance_class

  allocated_storage     = var.db_allocated_storage
  storage_type          = "gp3"
  storage_encrypted     = true
  kms_key_id            = aws_kms_key.rds.arn
  iops                  = 3000
  storage_throughput    = 125

  db_name  = "ragqa"
  username = "ragqaadmin"
  password = random_password.rds_password.result

  db_subnet_group_name            = aws_db_subnet_group.main.name
  vpc_security_group_ids          = [aws_security_group.rds.id]
  parameter_group_name            = aws_db_parameter_group.main.name
  publicly_accessible             = false
  skip_final_snapshot             = false
  final_snapshot_identifier       = "${var.project_name}-final-snapshot-${formatdate("YYYY-MM-DD-hhmm", timestamp())}"
  copy_tags_to_snapshot           = true
  auto_minor_version_upgrade      = true
  backup_retention_period         = var.db_backup_retention_days
  backup_window                   = var.rds_backup_window
  maintenance_window              = var.rds_maintenance_window
  multi_az                        = true
  deletion_protection             = var.enable_deletion_protection
  enabled_cloudwatch_logs_exports = ["postgresql"]

  # Performance Insights
  performance_insights_enabled    = true
  performance_insights_kms_key_id = aws_kms_key.rds.arn
  performance_insights_retention_period = 7

  # Enhanced Monitoring
  monitoring_interval             = 60
  monitoring_role_arn             = aws_iam_role.rds_monitoring.arn
  enable_iam_database_authentication = true

  # Restore from backup (if needed)
  # restore_to_point_in_time {
  #   source_db_instance_identifier = "source-db-instance"
  #   restore_time                   = "2023-12-19T23:45:00Z"
  # }

  tags = {
    Name   = "${var.project_name}-db-main"
    Stream = "Database"
  }

  depends_on = [aws_iam_role_policy.rds_monitoring]
}

# RDS PostgreSQL Instance (Langfuse - for LLM observability)
resource "aws_db_instance" "langfuse" {
  identifier     = "${var.project_name}-db-langfuse"
  engine         = "postgres"
  engine_version = "16.3"
  instance_class = "db.t4g.medium"

  allocated_storage  = 20
  storage_type       = "gp3"
  storage_encrypted  = true
  kms_key_id         = aws_kms_key.rds.arn
  iops               = 3000
  storage_throughput = 125

  db_name  = "langfuse"
  username = "langfuseadmin"
  password = random_password.rds_langfuse_password.result

  db_subnet_group_name            = aws_db_subnet_group.main.name
  vpc_security_group_ids          = [aws_security_group.rds.id]
  publicly_accessible             = false
  skip_final_snapshot             = false
  final_snapshot_identifier       = "${var.project_name}-langfuse-final-snapshot-${formatdate("YYYY-MM-DD-hhmm", timestamp())}"
  copy_tags_to_snapshot           = true
  auto_minor_version_upgrade      = true
  backup_retention_period         = 7
  backup_window                   = var.rds_backup_window
  maintenance_window              = var.rds_maintenance_window
  multi_az                        = false
  deletion_protection             = var.enable_deletion_protection
  enabled_cloudwatch_logs_exports = ["postgresql"]

  monitoring_interval = 60
  monitoring_role_arn = aws_iam_role.rds_monitoring.arn

  tags = {
    Name   = "${var.project_name}-db-langfuse"
    Stream = "Database"
  }

  depends_on = [aws_iam_role_policy.rds_monitoring]
}

# Random password for RDS (main)
resource "random_password" "rds_password" {
  length  = 32
  special = true
}

# Random password for RDS (langfuse)
resource "random_password" "rds_langfuse_password" {
  length  = 32
  special = true
}

# Store RDS passwords in Secrets Manager
resource "aws_secretsmanager_secret" "rds_password" {
  name                    = "${var.project_name}/rds/main/password"
  recovery_window_in_days = 7

  tags = {
    Name   = "${var.project_name}-rds-password"
    Stream = "Secrets"
  }
}

resource "aws_secretsmanager_secret_version" "rds_password" {
  secret_id = aws_secretsmanager_secret.rds_password.id
  secret_string = jsonencode({
    username = aws_db_instance.main.username
    password = random_password.rds_password.result
    engine   = "postgres"
    host     = aws_db_instance.main.address
    port     = aws_db_instance.main.port
    dbname   = aws_db_instance.main.db_name
  })
}

resource "aws_secretsmanager_secret" "rds_langfuse_password" {
  name                    = "${var.project_name}/rds/langfuse/password"
  recovery_window_in_days = 7

  tags = {
    Name   = "${var.project_name}-rds-langfuse-password"
    Stream = "Secrets"
  }
}

resource "aws_secretsmanager_secret_version" "rds_langfuse_password" {
  secret_id = aws_secretsmanager_secret.rds_langfuse_password.id
  secret_string = jsonencode({
    username = aws_db_instance.langfuse.username
    password = random_password.rds_langfuse_password.result
    engine   = "postgres"
    host     = aws_db_instance.langfuse.address
    port     = aws_db_instance.langfuse.port
    dbname   = aws_db_instance.langfuse.db_name
  })
}

# IAM Role for RDS Monitoring
resource "aws_iam_role" "rds_monitoring" {
  name = "${var.project_name}-rds-monitoring-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "monitoring.rds.amazonaws.com"
        }
      }
    ]
  })

  tags = {
    Name   = "${var.project_name}-rds-monitoring-role"
    Stream = "IAM"
  }
}

resource "aws_iam_role_policy_attachment" "rds_monitoring" {
  role       = aws_iam_role.rds_monitoring.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AmazonRDSEnhancedMonitoringRole"
}

resource "aws_iam_role_policy" "rds_monitoring" {
  name = "${var.project_name}-rds-monitoring-policy"
  role = aws_iam_role.rds_monitoring.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "logs:CreateLogGroup",
          "logs:CreateLogStream",
          "logs:PutLogEvents",
          "logs:DescribeLogStreams"
        ]
        Resource = "arn:aws:logs:${var.aws_region}:${data.aws_caller_identity.current.account_id}:log-group:/aws/rds/*"
      }
    ]
  })
}

# KMS Key for RDS encryption
resource "aws_kms_key" "rds" {
  description             = "KMS key for RDS encryption"
  deletion_window_in_days = 10
  enable_key_rotation     = true

  tags = {
    Name   = "${var.project_name}-rds-key"
    Stream = "Security"
  }
}

resource "aws_kms_alias" "rds" {
  name          = "alias/${var.project_name}-rds"
  target_key_id = aws_kms_key.rds.key_id
}

# RDS Event Subscription
resource "aws_db_event_subscription" "main" {
  name      = "${var.project_name}-rds-events"
  sns_topic = aws_sns_topic.alerts.arn

  source_type = "db-instance"

  event_categories = [
    "availability",
    "backup",
    "creation",
    "deletion",
    "failover",
    "failure",
    "maintenance",
    "notification",
    "recovery"
  ]

  tags = {
    Name   = "${var.project_name}-rds-events"
    Stream = "Monitoring"
  }
}

# CloudWatch Alarms for RDS
resource "aws_cloudwatch_metric_alarm" "rds_cpu" {
  alarm_name          = "${var.project_name}-rds-cpu-high"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = 2
  metric_name         = "CPUUtilization"
  namespace           = "AWS/RDS"
  period              = 300
  statistic           = "Average"
  threshold           = 80
  alarm_description   = "RDS CPU utilization is high"
  alarm_actions       = [aws_sns_topic.alerts.arn]

  dimensions = {
    DBInstanceIdentifier = aws_db_instance.main.identifier
  }

  tags = {
    Name   = "${var.project_name}-rds-cpu-alarm"
    Stream = "Monitoring"
  }
}

resource "aws_cloudwatch_metric_alarm" "rds_storage" {
  alarm_name          = "${var.project_name}-rds-storage-low"
  comparison_operator = "LessThanThreshold"
  evaluation_periods  = 1
  metric_name         = "FreeStorageSpace"
  namespace           = "AWS/RDS"
  period              = 300
  statistic           = "Average"
  threshold           = 10737418240 # 10 GB in bytes
  alarm_description   = "RDS free storage space is low"
  alarm_actions       = [aws_sns_topic.alerts.arn]

  dimensions = {
    DBInstanceIdentifier = aws_db_instance.main.identifier
  }

  tags = {
    Name   = "${var.project_name}-rds-storage-alarm"
    Stream = "Monitoring"
  }
}

resource "aws_cloudwatch_metric_alarm" "rds_connection_count" {
  alarm_name          = "${var.project_name}-rds-connections-high"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = 2
  metric_name         = "DatabaseConnections"
  namespace           = "AWS/RDS"
  period              = 300
  statistic           = "Average"
  threshold           = 200
  alarm_description   = "RDS connection count is high"
  alarm_actions       = [aws_sns_topic.alerts.arn]

  dimensions = {
    DBInstanceIdentifier = aws_db_instance.main.identifier
  }

  tags = {
    Name   = "${var.project_name}-rds-connections-alarm"
    Stream = "Monitoring"
  }
}
