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

resource "aws_dynamodb_table" "user_sessions" {
  name           = "UserSessions"
  billing_mode   = "PAY_PER_REQUEST"

  attribute {
    name = "UserId"
    type = "S"
  }

  attribute {
    name = "SessionId"
    type = "S"
  }

  key_schema {
    attribute_name = "UserId"
    key_type       = "HASH"
  }

  point_in_time_recovery_enabled = true

  server_side_encryption_enabled = true
  kms_key_id                      = aws_kms_key.user_sessions.arn

  provisioner "local-exec" {
    command = "echo 'Table UserSessions created successfully.'"
  }
}

resource "aws_kms_key" "user_sessions" {
  description = "KMS Key for UserSessions table"
}

resource "aws_kms_key_rotation_policy" "user_sessions" {
  target_key_id = aws_kms_key.user_sessions.id
}

resource "aws_kms_key_grant" "user_sessions" {
  key_id       = aws_kms_key.user_sessions.id
  constraint {
    principal_id = "*"
    principal_type = "AWS"
  }
  operations = ["Encrypt", "Decrypt", "GenerateDataKey", "DescribeKey"]
}

output "kms_key_arn" {
  value = aws_kms_key.user_sessions.arn
}

# Ensure KMS key Policy is defined
resource "aws_kms_key_policy" "user_sessions" {
  target_key_id = aws_kms_key.user_sessions.id
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Sid          = "EnableKeyRotation"
        Effect       = "Allow"
        Principal    = "*"
        Action       = "kms:GenerateRotationCurrentKey"
        Condition   = {
          StringEquals = {
            "aws:SourceArn" : aws_dynamodb_table.user_sessions.arn
          }
        }
      },
      {
        Sid          = "AllowEncryptionDecryption"
        Effect       = "Allow"
        Principal    = "*"
        Action       = ["kms:Encrypt", "kms:Decrypt", "kms:ReEncrypt*", "kms:GenerateDataKey*", "kms:DescribeKey"]
      }
    ]
  })
}
