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

resource "aws_vpc" "example" {
  cidr_block = "10.0.0.0/16"
}

resource "aws_subnet" "example" {
  vpc_id     = aws_vpc.example.id
  cidr_block = "10.0.1.0/24"
  availability_zone = "us-east-1a"
}

resource "aws_security_group" "example" {
  name        = "example-sg"
  description = "Allow HTTP traffic"
  vpc_id      = aws_vpc.example.id

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

resource "aws_ecs_cluster" "example" {
  name = "example-cluster"
}

resource "aws_ecs_task_definition" "example" {
  family                   = "example-task"
  network_configuration {
    awsvpc_configuration {
      subnets = [aws_subnet.example.id]
      security_groups = [aws_security_group.example.id]
      assign_public_ip = "ENABLED"
    }
  }

  requires_compatibilities = ["FARGATE"]
  cpu                      = "256"
  memory                   = "512"

  container_definitions = jsonencode([
    {
      name          = "example-container"
      image         = "nginx:latest"
      portMappings  = [
        {
          containerPort = 80
          hostPort      = 80
        }
      ]
      readonly_root_filesystem = true
    }
  ])
}

resource "aws_ecs_service" "example" {
  name            = "example-service"
  cluster         = aws_ecs_cluster.example.id
  task_definition = aws_ecs_task_definition.example.arn
  desired_count   = 1

  load_balancer {
    target_group_arn = aws_lb_target_group.example.arn
    container_name   = "example-container"
    container_port   = 80
  }
}

resource "aws_lb_target_group" "example" {
  name     = "example-target-group"
  port     = 80
  protocol = "HTTP"
  vpc_id   = aws_vpc.example.id

  health_check {
    path = "/"
  }
}

resource "aws_lb" "example" {
  name               = "example-lb"
  internal           = false
  load_balancer_type = "application"
  security_groups    = [aws_security_group.example.id]
  subnets            = [aws_subnet.example.id]

  listener {
    port               = 80
    protocol           = "HTTP"
    default_actions {
      type             = "forward"
      target_group_arn = aws_lb_target_group.example.arn
    }
  }
}

resource "aws_default_security_group" "example" {
  vpc_id = aws_vpc.example.id
}

resource "aws_vpc_flow_log" "example" {
  depends_on = [aws_vpc.example]
  vpc_id     = aws_vpc.example.id
  destination_bucket_name = "example-logs"
  log_group_name          = "/aws/vpc/example"
}

# Add deletion protection to the load balancer
resource "aws_lb" "example" {
  name               = "example-lb"
  internal           = false
  load_balancer_type = "application"
  security_groups    = [aws_security_group.example.id]
  subnets            = [aws_subnet.example.id]
  deletion_protection = true

  listener {
    port               = 80
    protocol           = "HTTP"
    default_actions {
      type             = "forward"
      target_group_arn = aws_lb_target_group.example.arn
    }
  }
}
