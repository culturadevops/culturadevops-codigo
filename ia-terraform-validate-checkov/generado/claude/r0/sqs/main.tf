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

variable "queue_name" {
  description = "Nombre base de la cola SQS"
  type        = string
  default     = "mi-cola"
}

variable "max_receive_count" {
  description = "Número de recepciones antes de mover el mensaje a la DLQ"
  type        = number
  default     = 5
}

# Dead-letter queue
resource "aws_sqs_queue" "dlq" {
  name                      = "${var.queue_name}-dlq"
  message_retention_seconds = 1209600 # 14 días (máximo)
  sqs_managed_sse_enabled   = true

  tags = {
    Name = "${var.queue_name}-dlq"
  }
}

# Cola principal
resource "aws_sqs_queue" "main" {
  name                       = var.queue_name
  visibility_timeout_seconds = 30
  message_retention_seconds  = 345600 # 4 días
  receive_wait_time_seconds  = 20     # long polling
  sqs_managed_sse_enabled    = true

  redrive_policy = jsonencode({
    deadLetterTargetArn = aws_sqs_queue.dlq.arn
    maxReceiveCount     = var.max_receive_count
  })

  tags = {
    Name = var.queue_name
  }
}

# Restringe qué colas pueden usar la DLQ como destino
resource "aws_sqs_queue_redrive_allow_policy" "dlq" {
  queue_url = aws_sqs_queue.dlq.id

  redrive_allow_policy = jsonencode({
    redrivePermission = "byQueue"
    sourceQueueArns   = [aws_sqs_queue.main.arn]
  })
}

output "queue_url" {
  value = aws_sqs_queue.main.id
}

output "queue_arn" {
  value = aws_sqs_queue.main.arn
}

output "dlq_url" {
  value = aws_sqs_queue.dlq.id
}

output "dlq_arn" {
  value = aws_sqs_queue.dlq.arn
}
