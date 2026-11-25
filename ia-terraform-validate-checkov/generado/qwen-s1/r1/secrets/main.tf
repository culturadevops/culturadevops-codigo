terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 4.0"
    }
  }
}

provider "aws" {
  region = "us-east-1"
}

resource "aws_kms_key" "database_secret_key" {
  description = "KMS key for database secret"
}

resource "aws_secretsmanager_secret" "database_password" {
  name = "database-password"

  kms_key_id = aws_kms_key.database_secret_key.id
}

resource "aws_secretsmanager_secret_version" "database_password_version" {
  secret_id = aws_secretsmanager_secret.database_password.id
  secret_string = jsonencode({
    password = "your-strong-password-here"
  })
}

resource "aws_secretsmanager_secret_rotation" "database_password_rotation" {
  secret_id = aws_secretsmanager_secret.database_password.id
}
