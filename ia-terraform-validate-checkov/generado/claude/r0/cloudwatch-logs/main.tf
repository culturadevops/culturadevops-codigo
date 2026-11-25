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

variable "app_name" {
  description = "Nombre de la aplicación"
  type        = string
  default     = "mi-aplicacion"
}

variable "environment" {
  description = "Entorno de despliegue (dev, staging, prod)"
  type        = string
  default     = "dev"
}

variable "retention_in_days" {
  description = "Días de retención de los logs"
  type        = number
  default     = 30
}

resource "aws_cloudwatch_log_group" "app" {
  name              = "/aplicacion/${var.app_name}/${var.environment}"
  retention_in_days = var.retention_in_days

  tags = {
    Application = var.app_name
    Environment = var.environment
    ManagedBy   = "terraform"
  }
}

output "log_group_name" {
  description = "Nombre del grupo de logs"
  value       = aws_cloudwatch_log_group.app.name
}

output "log_group_arn" {
  description = "ARN del grupo de logs"
  value       = aws_cloudwatch_log_group.app.arn
}
