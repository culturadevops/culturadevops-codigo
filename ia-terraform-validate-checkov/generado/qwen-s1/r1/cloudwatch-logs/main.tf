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

resource "aws_kms_key" "app_logs_kms" {
  description = "KMS key for encrypting app logs"
}

resource "aws_cloudwatch_log_group" "app_logs" {
  name                = "/app_logs"
  retention_in_days   = 365
  kms_key_id          = aws_kms_key.app_logs_kms.id
}

resource "aws_cloudwatch_log_group" "app_logs_audit" {
  name                = "/app_logs_audit"
  retention_in_days   = 365
  kms_key_id          = aws_kms_key.app_logs_kms.id
}
