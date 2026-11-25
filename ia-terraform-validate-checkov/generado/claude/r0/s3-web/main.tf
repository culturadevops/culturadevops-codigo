terraform {
  required_version = ">= 1.5.0"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

provider "aws" {
  region = "us-east-1"
}

variable "bucket_name" {
  description = "Nombre globalmente único del bucket S3 para el sitio web estático"
  type        = string
}

resource "aws_s3_bucket" "sitio" {
  bucket = var.bucket_name

  tags = {
    Name        = var.bucket_name
    Proposito   = "sitio-web-estatico"
    Gestionado  = "terraform"
  }
}

resource "aws_s3_bucket_ownership_controls" "sitio" {
  bucket = aws_s3_bucket.sitio.id

  rule {
    object_ownership = "BucketOwnerEnforced"
  }
}

resource "aws_s3_bucket_public_access_block" "sitio" {
  bucket = aws_s3_bucket.sitio.id

  block_public_acls       = true
  ignore_public_acls      = true
  block_public_policy     = false
  restrict_public_buckets = false
}

resource "aws_s3_bucket_website_configuration" "sitio" {
  bucket = aws_s3_bucket.sitio.id

  index_document {
    suffix = "index.html"
  }

  error_document {
    key = "error.html"
  }
}

resource "aws_s3_bucket_server_side_encryption_configuration" "sitio" {
  bucket = aws_s3_bucket.sitio.id

  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
  }
}

resource "aws_s3_bucket_versioning" "sitio" {
  bucket = aws_s3_bucket.sitio.id

  versioning_configuration {
    status = "Enabled"
  }
}

data "aws_iam_policy_document" "lectura_publica" {
  statement {
    sid     = "PublicReadGetObject"
    effect  = "Allow"
    actions = ["s3:GetObject"]

    principals {
      type        = "*"
      identifiers = ["*"]
    }

    resources = ["${aws_s3_bucket.sitio.arn}/*"]
  }
}

resource "aws_s3_bucket_policy" "lectura_publica" {
  bucket = aws_s3_bucket.sitio.id
  policy = data.aws_iam_policy_document.lectura_publica.json

  depends_on = [aws_s3_bucket_public_access_block.sitio]
}

output "bucket_name" {
  description = "Nombre del bucket S3"
  value       = aws_s3_bucket.sitio.id
}

output "website_endpoint" {
  description = "Endpoint del sitio web estático"
  value       = aws_s3_bucket_website_configuration.sitio.website_endpoint
}

output "website_url" {
  description = "URL HTTP del sitio web estático"
  value       = "http://${aws_s3_bucket_website_configuration.sitio.website_endpoint}"
}
