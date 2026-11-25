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
    cidr_blocks = ["0.0.0.0/0"]
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }
}

resource "aws_instance" "bastion_host" {
  ami           = "ami-0c55b159cbfafe1f0"  # Replace with your AMI ID
  instance_type = "t2.micro"
  key_name      = "your-key-pair"          # Replace with your key pair name
  security_groups = [aws_security_group.bastion_host_sg.id]
  associate_public_ip_address = true

  tags = {
    Name = "BastionHost"
  }
}
