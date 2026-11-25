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

resource "aws_kms_key" "example" {
  description = "KMS Key for CloudTrail"
  enable_key_rotation = true
}

resource "aws_cloudtrail" "example" {
  name     = "example-cloudtrail"
  s3_bucket_name = "example-bucket"
  is_multi_region_trail = true
  enable_logging = true
  kms_key_id = aws_kms_key.example.id
  enable_log_file_validation = true
  sns_topic_name = "example-sns-topic"
}

resource "aws_cloudwatch_log_group" "example" {
  name = "/aws/cloudtrail/example-cloudtrail"
  retention_in_days = 365
}

resource "aws_cloudwatch_log_destination" "example" {
  name = "example-cloudtrail-destination"
  destination_type = "kinesis-firehose"

  kinesis_firehose {
    arn = aws_kinesis_firehose_delivery_stream.example.arn
  }
}

resource "aws_cloudwatch_log_destination_policy" "example" {
  destination_arn = aws_cloudwatch_log_destination.example.arn
  policy_document = jsonencode({
    Statement = [
      {
        Action = "logs:PutLogEvents"
        Effect = "Allow"
        Principal = {
          Service = "cloudtrail.amazonaws.com"
        }
        Resource = "*"
        Sid      = ""
      }
    ]
  })
}

resource "aws_cloudwatch_log_subscription_filter" "example" {
  name   = "example-cloudtrail-filter"
  filter_pattern = "{}"
  log_group_name = aws_cloudwatch_log_group.example.name
  destination_arn = aws_cloudwatch_log_destination.example.arn
}

resource "aws_kinesis_firehose_delivery_stream" "example" {
  name        = "example-cloudtrail-firehose"
  destination = "LambdaFunction"

  kinesis_firehose {
    role_arn = aws_iam_role.example.arn
    cloudwatch_logging_options {
      enabled = true
    }
    encryption_configuration {
      kms_key_arn = aws_kms_key.example.arn
    }
  }
}

resource "aws_lambda_function" "example" {
  filename      = "path/to/your/lambda/code.zip"
  function_name = "example-cloudtrail-lambda"
  handler       = "index.handler"
  role          = aws_iam_role.example.arn
  runtime       = "python3.8"
  dead_letter_config {
    target_arn = aws_sqs_queue.example.arn
  }
}

resource "aws_sqs_queue" "example" {
  name = "example-sqs-queue"
  encryption_enabled = true
}

resource "aws_iam_role" "example" {
  name = "example-cloudtrail-lambda-role"

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

resource "aws_iam_role_policy_attachment" "example" {
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
  role       = aws_iam_role.example.name
}

resource "aws_kms_key" "example_kms" {
  description = "KMS Key for Kinesis Firehose"
  enable_key_rotation = true
}

resource "aws_kinesis_firehose_delivery_stream" "example2" {
  name        = "example-cloudtrail-firehose2"
  destination = "LambdaFunction"

  kinesis_firehose {
    role_arn = aws_iam_role.example.arn
    cloudwatch_logging_options {
      enabled = true
    }
    encryption_configuration {
      kms_key_arn = aws_kms_key.example_kms.arn
    }
  }
}
