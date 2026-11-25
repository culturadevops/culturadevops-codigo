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
    cidr_blocks = ["10.0.0.0/16"]  # Reemplaza con la subnet de tu red privada
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
}
