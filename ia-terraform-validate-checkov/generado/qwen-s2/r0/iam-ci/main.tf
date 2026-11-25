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

resource "aws_iam_role" "s3_upload_role" {
  name = "s3UploadRole"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "s3.amazonaws.com"
        }
      }
    ]
  })
}

resource "aws_iam_role_policy" "s3_upload_policy" {
  name = "s3UploadPolicy"
  role = aws_iam_role.s3_upload_role.name

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = [
          "s3:PutObject",
          "s3:PutObjectAcl"
        ]
        Effect = "Allow"
        Resource = "arn:aws:s3:::your-bucket-name/*"
      }
    ]
  })
}

resource "aws_s3_bucket" "example_bucket" {
  bucket = "your-bucket-name"
}

resource "aws_s3_bucket_policy" "example_bucket_policy" {
  bucket = aws_s3_bucket.example_bucket.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Sid    = "AllowUploadToBucket"
        Effect = "Allow"
        Principal = "*"
        Action = [
          "s3:PutObject"
        ]
        Resource = "arn:aws:s3:::your-bucket-name/*"
        Condition = {
          StringLike = {
            "aws:SourceArn" = [
              "arn:aws:sts::${data.aws_caller_identity.current.account_id}:assumed-role/${aws_iam_role.s3_upload_role.name}/*"
            ]
          }
        }
      }
    ]
  })
}

data "aws_caller_identity" "current" {}
