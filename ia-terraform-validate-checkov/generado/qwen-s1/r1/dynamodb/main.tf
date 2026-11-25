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
  kms_master_key_id              = aws_kms_key.user_sessions.key_id

  provisioner "local-exec" {
    command = "echo 'Table UserSessions created successfully.'"
  }
}

resource "aws_kms_key" "user_sessions" {
  description = "KMS Key for UserSessions table"
}

output "kms_key_arn" {
  value = aws_kms_key.user_sessions.arn
}
