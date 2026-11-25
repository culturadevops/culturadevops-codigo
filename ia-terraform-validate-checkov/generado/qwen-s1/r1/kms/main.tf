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

resource "aws_kms_key" "example" {
  description = "KMS Key for data encryption"

  enable_key_rotation = true

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Sid     = "EnableKeyRotation"
        Effect  = "Allow"
        Principal = "*"
        Action = [
          "kms:DescribeKey",
          "kms:GetKeyRotationStatus",
          "kms:EnableKeyRotation",
          "kms:DisableKeyRotation"
        ]
        Resource = aws_kms_key.example.arn
      }
    ]
  })
}
