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

data "aws_caller_identity" "current" {}

data "aws_iam_policy_document" "kms" {
  statement {
    sid    = "EnableRootAccountPermissions"
    effect = "Allow"

    principals {
      type        = "AWS"
      identifiers = ["arn:aws:iam::${data.aws_caller_identity.current.account_id}:root"]
    }

    actions   = ["kms:*"]
    resources = ["*"]
  }
}

resource "aws_kms_key" "data" {
  description             = "Clave KMS para cifrar datos"
  key_usage               = "ENCRYPT_DECRYPT"
  customer_master_key_spec = "SYMMETRIC_DEFAULT"
  enable_key_rotation     = true
  rotation_period_in_days = 365
  deletion_window_in_days = 30
  multi_region            = false
  policy                  = data.aws_iam_policy_document.kms.json

  tags = {
    Name      = "data-encryption-key"
    ManagedBy = "terraform"
  }
}

resource "aws_kms_alias" "data" {
  name          = "alias/data-encryption-key"
  target_key_id = aws_kms_key.data.key_id
}

output "kms_key_arn" {
  description = "ARN de la clave KMS"
  value       = aws_kms_key.data.arn
}

output "kms_key_id" {
  description = "ID de la clave KMS"
  value       = aws_kms_key.data.key_id
}

output "kms_alias_name" {
  description = "Alias de la clave KMS"
  value       = aws_kms_alias.data.name
}
