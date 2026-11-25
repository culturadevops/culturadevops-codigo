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

resource "aws_iam_user" "ci_user" {
  name = "ci-user"
}

resource "aws_iam_user_policy" "s3_upload_policy" {
  name = "s3-upload-policy"
  user = aws_iam_user.ci_user.name

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "s3:PutObject",
          "s3:PutObjectAcl"
        ]
        Resource = "arn:aws:s3:::your-bucket-name/*"
      }
    ]
  })
}

resource "aws_s3_bucket" "example" {
  bucket = "your-bucket-name"
}

resource "aws_s3_bucket_policy" "example" {
  bucket = aws_s3_bucket.example.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Sid          = "AllowPutFromCIUser"
        Effect       = "Allow"
        Principal    = {
          AWS = aws_iam_user.ci_user.arn
        }
        Action       = "s3:PutObject"
        Resource     = "arn:aws:s3:::your-bucket-name/*"
        Condition    = {
          StringLike = {
            s3:x-amz-acl = ["public-read"]
          }
        }
      }
    ]
  })
}
