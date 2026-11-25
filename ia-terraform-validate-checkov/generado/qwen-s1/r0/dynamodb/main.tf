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

  provisioner "local-exec" {
    command = "echo 'Table UserSessions created successfully.'"
  }
}
