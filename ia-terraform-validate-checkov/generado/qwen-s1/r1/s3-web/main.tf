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

resource "aws_s3_bucket" "static_website" {
  bucket = "my-static-website-bucket"
}

resource "aws_s3_bucket_website" "static_website" {
  bucket = aws_s3_bucket.static_website.bucket

  index_document {
    suffix = "index.html"
  }

  error_document {
    key = "error.html"
  }
}

resource "aws_s3_bucket_policy" "static_website" {
  bucket = aws_s3_bucket.static_website.bucket

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Sid = "PublicReadForGetObject"
        Effect = "Allow"
        Principal = "*"
        Action = "s3:GetObject"
        Resource = "arn:aws:s3:::${aws_s3_bucket.static_website.bucket}/*"
      }
    ]
  })
}

resource "aws_s3_bucket_public_access_block" "static_website" {
  bucket = aws_s3_bucket.static_website.bucket

  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

resource "aws_kms_key" "static_website" {
  description = "KMS key for S3 bucket"
}

resource "aws_s3_bucket_server_side_encryption_configuration" "static_website" {
  bucket = aws_s3_bucket.static_website.bucket

  rule {
    apply_server_side_encryption_by_default {
      kms_master_key_id = aws_kms_key.static_website.id
      sse_algorithm     = "aws:kms"
    }
  }
}

resource "aws_s3_bucket_lifecycle_configuration" "static_website" {
  bucket = aws_s3_bucket.static_website.bucket

  rule {
    id      = "Versioning"
    status  = "Enabled"
    enabled = true

    transition {
      storage_class = "STANDARD_IA"
      transition    = "30 days"
    }

    expiration {
      days = 365
    }
  }
}

resource "aws_s3_bucket_versioning" "static_website" {
  bucket = aws_s3_bucket.static_website.bucket

  versioning_configuration {
    status = "Enabled"
  }
}

resource "aws_s3_bucket_logging" "static_website" {
  bucket = aws_s3_bucket.static_website.bucket

  target_bucket = aws_s3_bucket.static_website.bucket
  target_prefix = "log/"
}
