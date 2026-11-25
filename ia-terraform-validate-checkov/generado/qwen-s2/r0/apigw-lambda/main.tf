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

resource "aws_lambda_function" "example" {
  filename             = "lambda_function.zip"
  function_name        = "example_lambda"
  handler              = "app.handler"
  runtime              = "python3.8"
  role                 = aws_iam_role.example.arn

  environment {
    variables = {
      key = "value"
    }
  }
}

resource "aws_iam_role" "example" {
  name = "example_role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = ["lambda.amazonaws.com"]
        }
      }
    ]
  })
}

resource "aws_api_gateway_rest_api" "example" {
  name        = "example_api"
  description = "Example API Gateway"
}

resource "aws_api_gateway_resource" "example" {
  rest_api_id = aws_api_gateway_rest_api.example.id
  parent_id   = aws_api_gateway_rest_api.example.root_resource_id
  path_part   = "{proxy+}"
}

resource "aws_api_gateway_method" "example" {
  rest_api_id = aws_api_gateway_rest_api.example.id
  resource_id = aws_api_gateway_resource.example.id
  http_method = "ANY"
  authorization = "NONE"
}

resource "aws_api_gateway_integration" "example" {
  rest_api_id = aws_api_gateway_rest_api.example.id
  resource_id = aws_api_gateway_resource.example.id
  http_method = aws_api_gateway_method.example.http_method
  type        = "AWS_PROXY"
  integration_http_method = "POST"
  uri         = format(
    "arn:aws:apigateway:%s:lambda:path/2015-03-31/functions/arn:aws:lambda:%s:%%s:region-id:%s/%s/invocations",
    region,
    region,
    aws_lambda_function.example.arn
  )
}

resource "aws_api_gateway_deployment" "example" {
  depends_on = [aws_api_gateway_integration.example]
  rest_api_id = aws_api_gateway_rest_api.example.id
  stage_name  = "prod"
}
