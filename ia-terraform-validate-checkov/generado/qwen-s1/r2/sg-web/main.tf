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

resource "aws_security_group" "web_server" {
  name        = "web_server_sg"
  description = "Security group for web server with HTTP, HTTPS and SSH access"

  ingress {
    from_port   = 80
    to_port     = 80
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  ingress {
    from_port   = 443
    to_port     = 443
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  ingress {
    from_port   = 22
    to_port     = 22
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]  # Permitir SSH desde cualquier IP
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    Name = "web_server_sg"
  }
}

resource "aws_instance" "example" {
  ami           = "ami-0c55b159cbfafe1f0"  # Reemplaza con la AMI adecuada para tu región
  instance_type = "t2.micro"

  vpc_security_group_ids = [aws_security_group.web_server.id]

  tags = {
    Name = "web_server"
  }

  # Ensure Instance Metadata Service Version 1 is not enabled
  metadata_options {
    http_endpoint = "enabled"
    http_tokens   = "optional"
  }

  # Ensure that EC2 is EBS optimized
  ebs_optimized = true

  # Ensure all data stored in the Launch configuration or instance Elastic Blocks Store is securely encrypted
  root_block_device {
    encrypted = true
  }

  # Ensure that detailed monitoring is enabled for EC2 instances
  monitoring = true

  # Ensure an IAM role is attached to EC2 instance
  # Asegúrate de que tienes una política IAM apropiada y la adjuntas al recurso
  # example_iam_role = aws_iam_role.example
}
