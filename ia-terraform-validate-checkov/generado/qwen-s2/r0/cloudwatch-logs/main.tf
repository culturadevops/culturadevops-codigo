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

resource "aws_cloudwatch_log_group" "app_logs" {
  name                  = "/app/application_logs"
  retention_in_days     = 30
}
