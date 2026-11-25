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
  enable_key_rotation = true
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

resource "aws_kms_key_policy" "database_secret_key_policy" {
  key_id = aws_kms_key.database_secret_key.id
  policy = jsonencode({
    Version = "2012-10-17",
    Statement = [
      {
        Sid          = "EnableSecretsManagerAccess",
        Effect       = "Allow",
        Principal    = {
          AWS = "arn:aws:iam::123456789012:root"
        },
        Action       = [
          "kms:Encrypt",
          "kms:Decrypt",
          "kms:ReEncrypt*",
          "kms:GenerateDataKey*",
          "kms:DescribeKey"
        ],
        Resource = "*"
      }
    ]
  })
}

resource "aws_secretsmanager_secret_rotation" "database_password_rotation" {
  secret_id = aws_secretsmanager_secret.database_password.id
  rotate_after_days = 90
  rotation_rules = {
    automatically_after = 90
  }
}
