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

resource "aws_security_group" "bastion_host_sg" {
  name        = "bastion_host_sg"
  description = "Security group for the bastion host"
  vpc_id      = "vpc-12345678"  # Replace with your VPC ID

  ingress {
    from_port   = 22
    to_port     = 22
    protocol    = "tcp"
    cidr_blocks = ["10.0.0.0/8"]  # Replace with your internal network CIDR
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["10.0.0.0/8"]  # Replace with your internal network CIDR
  }
}

resource "aws_instance" "bastion_host" {
  ami           = "ami-0c55b159cbfafe1f0"  # Replace with your AMI ID
  instance_type = "t2.micro"
  key_name      = "your-key-pair"          # Replace with your key pair name
  security_groups = [aws_security_group.bastion_host_sg.id]
  associate_public_ip_address = false

  tags = {
    Name = "BastionHost"
  }

  # Ensure Instance Metadata Service Version 1 is not enabled
  disable_api_stop = true
  disable_api_terminate = true

  # Ensure that EC2 is EBS optimized
  ebs_optimized = true

  # Ensure all data stored in the Launch configuration or instance Elastic Blocks Store is securely encrypted
  root_block_device {
    encryption_enabled = true
  }

  # Ensure that detailed monitoring is enabled for EC2 instances
  monitoring = true

  # Ensure an IAM role is attached to EC2 instance
  iam_instance_profile {
    arn = aws_iam_instance_profile.bastion_host.arn
  }
}

resource "aws_iam_instance_profile" "bastion_host" {
  name = "bastion_host_profile"
  roles = [aws_iam_role.bastion_host.arn]
}

resource "aws_iam_role" "bastion_host" {
  name = "bastion_host_role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "ec2.amazonaws.com"
        }
      }
    ]
  })
}
