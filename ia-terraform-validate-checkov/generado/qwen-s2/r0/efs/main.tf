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

resource "aws_efs_file_system" "shared_efs" {
  creation_token = "efs-shared"
}

resource "aws_efs_mount_target" "shared_efs" {
  count           = 1
  file_system_id  = aws_efs_file_system.shared_efs.id
  subnet_id       = "subnet-12345678"  # Reemplaza con tu subnet ID
}

resource "aws_iam_policy" "efs_policy" {
  name        = "efs-policy"
  description = "IAM policy for EFS access"

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Principal {
          AWS = "*"
        }
        Action = [
          "elasticfilesystem:ClientMount",
          "elasticfilesystem:ClientWrite",
          "elasticfilesystem:ClientRead"
        ]
        Resource = "${aws_efs_file_system.shared_efs.arn}/*"
      }
    ]
  })
}

resource "aws_iam_role" "efs_role" {
  name = "efs-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "ec2.amazonaws.com"
        }
      }
    ]
  })
}

resource "aws_iam_role_policy_attachment" "efs_attach" {
  role       = aws_iam_role.efs_role.name
  policy_arn = aws_iam_policy.efs_policy.arn
}
