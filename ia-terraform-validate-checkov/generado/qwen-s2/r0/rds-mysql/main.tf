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

resource "aws_rds_instance" "mysql_wordpress" {
  engine                 = "mysql"
  engine_version         = "5.7"
  instance_class         = "db.t2.micro"
  name                   = "wordpress-db"
  username               = "admin"
  password               = "StrongPassword123!"
  allocated_storage      = 20
  storage_encrypted      = true
  vpc_security_group_ids = [aws_security_group.db_sg.id]
  parameter_group_name   = "default.mysql5.7"
}

resource "aws_security_group" "db_sg" {
  name        = "db-sg"
  description = "Security group for the database"

  ingress {
    from_port   = 3306
    to_port     = 3306
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
