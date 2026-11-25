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

resource "aws_ecr_repository" "docker_images" {
  name = "docker-images-repo"
}

resource "aws_ecr_image_tag_mutability" "docker_images" {
  repository_name = aws_ecr_repository.docker_images.name
  image_tag_mutability = "IMMUTABLE"
}

resource "aws_kms_key" "ecr" {
  description = "KMS key for ECR"
  deletion_window_in_days = 30
}

resource "aws_kms_key" "ecr_key_for_images" {
  description = "KMS key for ECR images"
  deletion_window_in_days = 30
}

resource "aws_ecr_repository" "docker_images" {
  name = "docker-images-repo"

  encryption_configuration {
    encryption_type = "KMS"
    kms_key_id      = aws_kms_key.ecr.arn
  }

  image_scanning_configuration {
    scan_on_push = true
  }
}

resource "aws_iam_policy" "ecr_kms_policy" {
  name        = "ecr_kms_policy"
  description = "Policy for ECR to use KMS"

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Sid          = "AllowECRToUseKMS"
        Effect       = "Allow"
        Action       = [
          "kms:GetKeyMetadata",
          "kms:DescribeKey",
          "kms:Encrypt",
          "kms:Decrypt",
          "kms:ReEncrypt*",
          "kms:GenerateDataKey*",
          "kms:List*",
        ]
        Resource = "*"
      }
    ]
  })
}

resource "aws_kms_key_policy" "ecr_key_policy" {
  key_id = aws_kms_key.ecr.arn
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Sid          = "AllowECRToUseKMS"
        Effect       = "Allow"
        Action       = [
          "kms:GetKeyMetadata",
          "kms:DescribeKey",
          "kms:Encrypt",
          "kms:Decrypt",
          "kms:ReEncrypt*",
          "kms:GenerateDataKey*",
          "kms:List*",
        ]
        Principal = {
          AWS = aws_iam_role.ecr_repo.arn
        }
      }
    ]
  })
}

resource "aws_iam_role" "ecr_repo" {
  name = "ecr_repo_role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "ecr.amazonaws.com"
        }
      }
    ]
  })
}

resource "aws_iam_role_policy_attachment" "ecr_repo_policy" {
  role       = aws_iam_role.ecr_repo.name
  policy_arn = aws_iam_policy.ecr_kms_policy.arn
}
