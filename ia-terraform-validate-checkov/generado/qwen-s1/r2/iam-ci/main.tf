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

resource "aws_iam_role" "ci_role" {
  name = "ci-role"

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

resource "aws_iam_role_policy" "s3_upload_policy" {
  name = "s3-upload-policy"
  role = aws_iam_role.ci_role.name

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect    = "Allow"
        Action    = ["s3:PutObject", "s3:PutObjectAcl"]
        Resource  = "arn:aws:s3:::your-bucket-name/*"
      }
    ]
  })
}

resource "aws_s3_bucket" "example" {
  bucket = "your-bucket-name"

  server_side_encryption_configuration {
    rule {
      apply_server_side_encryption_by_default {
        sse_algorithm = "AES256"
      }
    }
  }

  public_access_block {
    block_public_acls       = true
    block_public_policy     = true
    ignore_public_acls      = true
    restrict_public_buckets = true
  }

  versioning {
    enabled = true
  }

  lifecycle {
    rules = [
      {
        id      = "DeleteOldObjects"
        status  = "Enabled"
        noncurrent_version_expiration {
          days = 30
        }
      }
    ]
  }

  event_notification_configuration {
    topic_configuration {
      topic_arn = "arn:aws:sns:us-east-1:123456789012:my-sns-topic"
      event = ["s3:ObjectCreated:*"]
    }
  }
}

resource "aws_s3_bucket_policy" "example" {
  bucket = aws_s3_bucket.example.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Sid          = "AllowPutFromCIUser"
        Effect       = "Allow"
        Principal    = { AWS = aws_iam_role.ci_role.arn }
        Action       = "s3:PutObject"
        Resource     = "arn:aws:s3:::your-bucket-name/*"
        Condition    = { StringLike = { "s3:x-amz-acl" = ["public-read"] } }
      }
    ]
  })
}

resource "aws_s3_bucket_public_access_block" "example" {
  bucket = aws_s3_bucket.example.id

  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

resource "aws_s3_bucket_logging" "example" {
  bucket = aws_s3_bucket.example.id
  target_bucket = "your-logging-bucket"
  target_prefix = "logs/"
}
