# JWT Secret
resource "aws_secretsmanager_secret" "jwt_secret" {
  name                    = "${var.project_name}/jwt-secret"
  recovery_window_in_days = 7

  tags = {
    Name   = "${var.project_name}-jwt-secret"
    Stream = "Secrets"
  }
}

resource "aws_secretsmanager_secret_version" "jwt_secret" {
  secret_id = aws_secretsmanager_secret.jwt_secret.id
  secret_string = random_password.jwt_secret.result
}

resource "random_password" "jwt_secret" {
  length  = 64
  special = true
}

# App Secret Key
resource "aws_secretsmanager_secret" "app_secret" {
  name                    = "${var.project_name}/app-secret"
  recovery_window_in_days = 7

  tags = {
    Name   = "${var.project_name}-app-secret"
    Stream = "Secrets"
  }
}

resource "aws_secretsmanager_secret_version" "app_secret" {
  secret_id = aws_secretsmanager_secret.app_secret.id
  secret_string = random_password.app_secret.result
}

resource "random_password" "app_secret" {
  length  = 64
  special = true
}

# Langfuse API Keys
resource "aws_secretsmanager_secret" "langfuse_keys" {
  name                    = "${var.project_name}/langfuse-keys"
  recovery_window_in_days = 7

  tags = {
    Name   = "${var.project_name}-langfuse-keys"
    Stream = "Secrets"
  }
}

resource "aws_secretsmanager_secret_version" "langfuse_keys" {
  secret_id = aws_secretsmanager_secret.langfuse_keys.id
  secret_string = jsonencode({
    public_key  = random_password.langfuse_public_key.result
    secret_key  = random_password.langfuse_secret_key.result
    host        = "https://${var.domain_name}/langfuse"
    sdk_version = "1.0.0"
  })
}

resource "random_password" "langfuse_public_key" {
  length  = 32
  special = false
}

resource "random_password" "langfuse_secret_key" {
  length  = 64
  special = true
}

# AWS Secrets Manager Secrets Rotation
# Note: You'll need to create a Lambda function to rotate secrets if needed
# This is a placeholder for the rotation configuration

resource "aws_secretsmanager_secret_rotation" "rds_rotation" {
  secret_id           = aws_secretsmanager_secret.rds_password.id
  rotation_enabled    = false # Set to true and configure Lambda for automatic rotation
  rotation_rules {
    automatically_after_days = 30
  }
}
