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

resource "aws_security_group" "alb_sg" {
  name        = "alb_security_group"
  description = "Security group for ALB"
  vpc_id      = "vpc-12345678"  # Replace with your VPC ID

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

resource "aws_alb" "example" {
  name               = "example-alb"
  subnets             = ["subnet-12345678", "subnet-87654321"]  # Replace with your subnet IDs
  security_groups     = [aws_security_group.alb_sg.id]
  internal            = false
  load_balancer_type  = "application"
  enable_deletion_protection = false

  listener {
    port            = 80
    protocol        = "HTTP"
    default_action {
      type = "forward"
      target_group_arn = aws_lb_target_group.example.arn
    }
  }
}

resource "aws_lb_target_group" "example" {
  name     = "example-tg"
  port     = 80
  protocol = "HTTP"
  vpc_id   = "vpc-12345678"  # Replace with your VPC ID

  health_check {
    enabled  = true
    interval = 30
    timeout  = 5
    unhealthy_threshold = 2
    healthy_threshold = 2
    path = "/"
  }
}

resource "aws_instance" "web" {
  count = 2

  ami           = "ami-0c55b159cbfafe1f0"  # Replace with your AMI ID
  instance_type = "t2.micro"
  vpc_security_group_ids = [aws_security_group.alb_sg.id]
  subnet_id      = "subnet-12345678"  # Replace with your subnet ID
  key_name       = "your-key-pair"   # Replace with your key pair name

  user_data = <<-EOF
              #!/bin/bash
              echo "Hello, World" > index.html
              nohup busy &
              EOF
}

resource "aws_lb_target_group_attachment" "example" {
  target_group_arn = aws_lb_target_group.example.arn
  target_id        = aws_instance.web[count.index].id
}
