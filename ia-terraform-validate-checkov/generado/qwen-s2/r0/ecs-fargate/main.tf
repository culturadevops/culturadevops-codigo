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

resource "aws_ecs_cluster" "ecs_cluster" {
  name = "ecs-cluster-fargate"
}

resource "aws_ecs_task_definition" "web_task" {
  family                = "web-task"
  network_mode          = "awsvpc"
  requires_compatibilities = ["FARGATE"]
  cpu                  = "256"
  memory               = "512"
  execution_role_arn   = aws_iam_role.ecs_execution_role.arn

  container_definitions = jsonencode([{
    name      = "web-container"
    image     = "nginx:latest"
    portMappings = [{
      containerPort = 80
      hostPort      = 80
    }]
  }])
}

resource "aws_iam_role" "ecs_execution_role" {
  name = "ecs-execution-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "ecs-tasks.amazonaws.com"
        }
      }
    ]
  })
}

resource "aws_ecs_service" "web_service" {
  name            = "web-service"
  cluster         = aws_ecs_cluster.ecs_cluster.id
  task_definition = aws_ecs_task_definition.web_task.arn
  desired_count   = 1
  launch_type     = "FARGATE"
  network_configuration {
    subnets = [for subnet in aws_subnet.example : subnet.id]
    security_groups = [aws_security_group.example.id]
    assign_public_ip = "ENABLED"
  }
}

resource "aws_subnet" "example" {
  vpc_id     = aws_vpc.main.id
  cidr_block = "10.0.1.0/24"
}

resource "aws_security_group" "example" {
  name        = "example-sg"
  description = "Allow HTTP traffic"
  vpc_id      = aws_vpc.main.id

  ingress {
    from_port   = 80
    to_port     = 80
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }
}

resource "aws_vpc" "main" {
  cidr_block = "10.0.0.0/16"

  tags = {
    Name = "main-vpc"
  }
}
