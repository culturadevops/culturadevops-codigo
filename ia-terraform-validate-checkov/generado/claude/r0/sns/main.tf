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

variable "topic_name" {
  description = "Nombre del tema SNS para alertas"
  type        = string
  default     = "alertas-email"
}

variable "alert_emails" {
  description = "Lista de correos que recibirán las alertas (cada uno debe confirmar la suscripción)"
  type        = list(string)
  default     = ["alertas@example.com"]
}

resource "aws_sns_topic" "alerts" {
  name              = var.topic_name
  kms_master_key_id = "alias/aws/sns"

  tags = {
    Name      = var.topic_name
    ManagedBy = "terraform"
  }
}

data "aws_caller_identity" "current" {}

data "aws_iam_policy_document" "alerts" {
  statement {
    sid     = "AllowAccountPublish"
    effect  = "Allow"
    actions = ["SNS:Publish"]

    principals {
      type        = "AWS"
      identifiers = ["arn:aws:iam::${data.aws_caller_identity.current.account_id}:root"]
    }

    resources = [aws_sns_topic.alerts.arn]
  }

  statement {
    sid     = "AllowCloudWatchAlarms"
    effect  = "Allow"
    actions = ["SNS:Publish"]

    principals {
      type        = "Service"
      identifiers = ["cloudwatch.amazonaws.com"]
    }

    resources = [aws_sns_topic.alerts.arn]

    condition {
      test     = "StringEquals"
      variable = "aws:SourceAccount"
      values   = [data.aws_caller_identity.current.account_id]
    }
  }
}

resource "aws_sns_topic_policy" "alerts" {
  arn    = aws_sns_topic.alerts.arn
  policy = data.aws_iam_policy_document.alerts.json
}

resource "aws_sns_topic_subscription" "email" {
  for_each = toset(var.alert_emails)

  topic_arn = aws_sns_topic.alerts.arn
  protocol  = "email"
  endpoint  = each.value
}

output "sns_topic_arn" {
  description = "ARN del tema SNS de alertas"
  value       = aws_sns_topic.alerts.arn
}
