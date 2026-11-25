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

resource "aws_queue" "main_queue" {
  name = "main-queue"
}

resource "aws_queue" "dead_letter_queue" {
  name           = "dead-letter-queue"
  redrive_policy = jsonencode({
    deadLetterDeliveryDelaySeconds = 0
    redrivePolicy                  = jsonencode({
      maxDeliveryCount              = 5
      deadLetterTargetArn           = aws_queue.main_queue.arn
    })
  })
}

resource "aws_queue_policy" "dead_letter_queue_policy" {
  queue_url = aws_queue.dead_letter_queue.url

  policy = jsonencode({
    Statement = [
      {
        Sid          = "AllowSendToDeadLetterQueue"
        Effect      = "Allow"
        Principal   = "*"
        Action      = "sqs:SendMessage"
        Resource    = aws_queue.main_queue.arn
        Condition   = {
          StringEquals = {
            "aws:SourceArn" = aws_queue.main_queue.arn
          }
        }
      }
    ]
  })
}
