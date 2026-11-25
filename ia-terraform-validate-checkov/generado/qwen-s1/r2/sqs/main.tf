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

resource "aws_sqs_queue" "main_queue" {
  name        = "main-queue"
  message_retention_seconds = 86400
  visibility_timeout_seconds = 30
  encryption_enabled = true
}

resource "aws_sqs_queue" "dead_letter_queue" {
  name        = "dead-letter-queue"
  message_retention_seconds = 86400
  visibility_timeout_seconds = 30
  encryption_enabled = true
}

resource "aws_sqs_queue_policy" "dead_letter_queue_policy" {
  queue_url = aws_sqs_queue.dead_letter_queue.url

  policy = jsonencode({
    Statement = [
      {
        Sid         = "AllowSendToDeadLetterQueue"
        Effect     = "Allow"
        Principal  = "*"
        Action    = "sqs:SendMessage"
        Resource  = aws_sqs_queue.main_queue.arn
        Condition = {
          StringLike = {
            "sqs:MessageAttributes.http.error.type" = "String"
          }
        }
      }
    ]
  })
}

resource "aws_sqs_queue_policy" "main_queue_policy" {
  queue_url = aws_sqs_queue.main_queue.url

  policy = jsonencode({
    Statement = [
      {
        Sid         = "AllowSendMessageToDeadLetterQueue"
        Effect     = "Deny"
        Principal  = "*"
        Action    = "sqs:SendMessage"
        Resource  = aws_sqs_queue.dead_letter_queue.arn
        Condition = {
          Bool = {
            "sqs:ErrorMessage" = "true"
          }
        }
      }
    ]
  })
}

resource "aws_sqs_queue" "dead_letter_target" {
  name        = "dead-letter-target-queue"
  message_retention_seconds = 86400
  visibility_timeout_seconds = 30
  encryption_enabled = true
}

resource "aws_sqs_queue_policy" "dead_letter_target_policy" {
  queue_url = aws_sqs_queue.dead_letter_target.url

  policy = jsonencode({
    Statement = [
      {
        Sid         = "AllowReceiveMessageFromDeadLetterQueue"
        Effect     = "Allow"
        Principal  = "*"
        Action    = "sqs:ReceiveMessage"
        Resource  = aws_sqs_queue.dead_letter_queue.arn
      }
    ]
  })
}

resource "aws_sqs_queue" "main_queue_with_dead_letter" {
  name        = "main-queue-with-dead-letter"
  message_retention_seconds = 86400
  visibility_timeout_seconds = 30
  dead_letter_target_arn = aws_sqs_queue.dead_letter_target.arn
  encryption_enabled = true
}
