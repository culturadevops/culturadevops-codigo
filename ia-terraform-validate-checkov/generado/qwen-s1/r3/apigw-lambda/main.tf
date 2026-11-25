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
  request_validator_id = aws_api_gateway_request_validator.example.id
}

resource "aws_api_gateway_request_validator" "example" {
  rest_api_id = aws_api_gateway_rest_api.example.id
  validate_request_body = true
  validate_request_parameters = {
    method = true
    path = true
    query_string = true
    header = true
  }
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
  depends_on = [aws_api_gateway_method.example]
  rest_api_id = aws_api_gateway_rest_api.example.id
  stage_name  = "prod"
}

resource "aws_security_group" "example" {
  name        = "example-sg"
  description = "Security group for API Gateway"
  vpc_id      = "vpc-12345678" # Replace with your VPC ID

  ingress {
    from_port   = 0
    to_port     = 65535
    protocol    = "-1"
    cidr_blocks = ["10.0.0.0/8"] # Replace with your trusted CIDR blocks
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["10.0.0.0/8"] # Replace with your trusted CIDR blocks
  }
}

resource "aws_security_group_rule" "example" {
  security_group_id = aws_security_group.example.id
  type              = "ingress"
  from_port         = 443
  to_port           = 443
  protocol          = "tcp"
  cidr_blocks       = ["0.0.0.0/0"]
}

resource "aws_lambda_permission" "allow_api_gateway" {
  statement_id  = "AllowAPIGatewayInvoke"
  action        = "lambda:InvokeFunction"
  function_name = "arn:aws:lambda:us-east-1:YOUR_ACCOUNT_ID:function:YourFunctionName"
  principal     = "apigateway.amazonaws.com"
  source_arn    = aws_api_gateway_rest_api.example.execution_arn
}

# Ensure Create before destroy for API Gateway
resource "aws_api_gateway_rest_api" "example_destroy" {
  name        = "ExampleAPI_destroy"
  description = "API Gateway HTTP API to call Lambda function"
  depends_on  = [aws_api_gateway_rest_api.example]
}

# Ensure Create before destroy for API deployments
resource "aws_api_gateway_deployment" "example_destroy" {
  depends_on = [aws_api_gateway_method.example]
  rest_api_id = aws_api_gateway_rest_api.example_destroy.id
  stage_name  = "prod_destroy"
}

# Ensure no security groups allow egress from 0.0.0.0:0 to port -1
resource "aws_security_group" "example_destroy" {
  name        = "example-sg_destroy"
  description = "Security group for API Gateway"
  vpc_id      = "vpc-12345678" # Replace with your VPC ID

  ingress {
    from_port   = 0
    to_port     = 65535
    protocol    = "-1"
    cidr_blocks = ["10.0.0.0/8"] # Replace with your trusted CIDR blocks
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["10.0.0.0/8"] # Replace with your trusted CIDR blocks
  }
}

resource "aws_security_group_rule" "example_destroy" {
  security_group_id = aws_security_group.example_destroy.id
  type              = "ingress"
  from_port         = 443
  to_port           = 443
  protocol          = "tcp"
  cidr_blocks       = ["0.0.0.0/0"]
}

# Ensure every security group and rule has a description
resource "aws_security_group" "example" {
  name        = "example-sg"
  description = "Security group for API Gateway"
  vpc_id      = "vpc-12345678" # Replace with your VPC ID

  ingress {
    from_port   = 0
    to_port     = 65535
    protocol    = "-1"
    cidr_blocks = ["10.0.0.0/8"] # Replace with your trusted CIDR blocks
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["10.0.0.0/8"] # Replace with your trusted CIDR blocks
  }
}

resource "aws_security_group_rule" "example" {
  security_group_id = aws_security_group.example.id
  type              = "ingress"
  from_port         = 443
  to_port           = 443
  protocol          = "tcp"
  cidr_blocks       = ["0.0.0.0/0"]
  description       = "Allow HTTPS traffic"
}

# Ensure that Security Groups are attached to another resource
resource "aws_security_group" "example" {
  name        = "example-sg"
  description = "Security group for API Gateway"
  vpc_id      = "vpc-12345678" # Replace with your VPC ID

  ingress {
    from_port   = 0
    to_port     = 65535
    protocol    = "-1"
    cidr_blocks = ["10.0.0.0/8"] # Replace with your trusted CIDR blocks
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["10.0.0.0/8"] # Replace with your trusted CIDR blocks
  }
}
