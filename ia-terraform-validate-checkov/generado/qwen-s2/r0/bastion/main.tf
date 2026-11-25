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

resource "aws_vpc" "bastion_vpc" {
  cidr_block = "10.0.0.0/16"
}

resource "aws_subnet" "bastion_subnet" {
  vpc_id            = aws_vpc.bastion_vpc.id
  cidr_block        = "10.0.1.0/24"
  availability_zone = "us-east-1a"
}

resource "aws_security_group" "bastion_sg" {
  name        = "bastion-sg"
  description = "Security group for the bastion host"
  vpc_id      = aws_vpc.bastion_vpc.id

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
  ami           = "ami-0c55b11fc3EXAMPLE" # Use the appropriate AMI for your environment
  instance_type = "t2.micro"
  vpc_security_group_ids = [aws_security_group.bastion_sg.id]
  subnet_id      = aws_subnet.bastion_subnet.id

  lifecycle {
    create_before_destroy = true
  }
}
