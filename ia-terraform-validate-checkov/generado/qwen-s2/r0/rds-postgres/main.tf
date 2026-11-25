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

resource "aws_rds_instance" "postgresql" {
  identifier      = "my-postgresql-db"
  instance_class  = "db.t3.micro"
  engine          = "postgres"
  username        = "myuser"
  password        = "mypassword"
  allocated_storage = 20
  name            = "my-postgresql-db"
  parameter_group_name = "default.postgres11"
  vpc_security_group_ids = [aws_security_group.my_sg.id]
  publicly_accessible = false
}

resource "aws_security_group" "my_sg" {
  name        = "my-sg"
  description = "Allow access to PostgreSQL"
  vpc_id      = "vpc-12345678"

  ingress {
    from_port   = 5432
    to_port    = 5432
    protocol   = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }
}
