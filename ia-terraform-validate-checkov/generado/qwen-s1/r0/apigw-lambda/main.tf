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

resource "aws_api_gateway_rest_api" "example" {
  name        = "ExampleAPI"
  description = "API Gateway HTTP API to call Lambda function"
}

resource "aws_api_gateway_resource" "example" {
  rest_api_id = aws_api_gateway_rest_api.example.id
  parent_id   = aws_api_gateway_rest_api.example.root_resource_id
  path_part   = "{proxy+}"
}

resource "aws_api_gateway_method" "example" {
  rest_api_id   = aws_api_gateway_rest_api.example.id
  resource_id   = aws_api_gateway_resource.example.id
  http_method   = "ANY"
  authorization = "NONE"
}

resource "aws_api_gateway_integration" "example" {
  rest_api_id         = aws_api_gateway_rest_api.example.id
  resource_id         = aws_api_gateway_resource.example.id
  http_method         = aws_api_gateway_method.example.http_method
  type               = "AWS_PROXY"
  integration_http_method = "POST"
  uri                = "arn:aws:apigateway:us-east-1:lambda:path/2015-03-31/functions/arn:aws:lambda:us-east-1:YOUR_ACCOUNT_ID:function:YourFunctionName/invocations"
}

resource "aws_api_gateway_deployment" "example" {
  rest_api_id = aws_api_gateway_rest_api.example.id
  stage_name  = "prod"
}
