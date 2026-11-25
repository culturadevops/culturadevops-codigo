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

resource "aws_sns_topic" "alertas" {
  name = "alertas-sns"
}

resource "aws_sns_topic_policy" "alertas_policy" {
  topic_arn = aws_sns_topic.alertas.arn

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Sid         = "EnableSNSKMS"
        Effect      = "Allow"
        Principal   = "*"
        Action      = "sns:GetTopicAttributes"
        Resource    = aws_sns_topic.alertas.arn
        Condition   = {
          StringLike = {
            "aws:SourceArn" = "arn:aws:kms:*:*:*"
          }
        }
      },
      {
        Sid         = "EncryptWithKMS"
        Effect      = "Allow"
        Principal   = "*"
        Action      = "sns:Publish"
        Resource    = aws_sns_topic.alertas.arn
        Condition   = {
          StringEquals = {
            "aws:EncryptionContext:aws:kms" = "true"
          }
        }
      }
    ]
  })
}

resource "aws_kms_key" "sns_key" {
  description = "KMS key for SNS topic encryption"
}

resource "aws_iam_policy" "sns_policy" {
  name        = "sns-policy"
  description = "Policy to allow publishing to SNS topic"

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sns:Publish"
        Effect = "Allow"
        Resource = aws_sns_topic.alertas.arn
      }
    ]
  })
}

resource "aws_iam_role" "sns_role" {
  name = "sns-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "lambda.amazonaws.com"
        }
      }
    ]
  })
}

resource "aws_iam_role_policy_attachment" "sns_policy_attachment" {
  role       = aws_iam_role.sns_role.name
  policy_arn = aws_iam_policy.sns_policy.arn
}
