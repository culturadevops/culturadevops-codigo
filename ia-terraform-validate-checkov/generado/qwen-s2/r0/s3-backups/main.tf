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

resource "aws_s3_bucket" "app_backups" {
  bucket = "app-backups-${var.env}"
  acl    = "private"
}

resource "aws_s3_bucket_policy" "app_backups" {
  bucket = aws_s3_bucket.app_backups.id
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Sid          = "AllowPublicRead"
        Effect       = "Allow"
        Principal    = "*"
        Action       = "s3:GetObject"
        Resource     = "${aws_s3_bucket.app_backups.bucket}/{*}"
      }
    ]
  })
}
