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

resource "aws_rds_instance" "wordpress_db" {
  engine             = "mysql"
  engine_version     = "5.7"
  instance_class     = "db.t2.micro"
  name              = "wordpress-db"
  allocated_storage  = 20
  username           = "admin"
  password           = "YourStrongPassword123"
  parameter_group_name = "default.mysql5.7"
  vpc_security_group_ids = [aws_security_group.db_access.id]
  skip_final_snapshot = true
}

resource "aws_security_group" "db_access" {
  name        = "db_access"
  description = "Security group for RDS database access"
  vpc_id      = "vpc-12345678"  # Replace with your VPC ID

  ingress {
    from_port   = 3306
    to_port    = 3306
    protocol   = "tcp"
    cidr_blocks = ["10.0.0.0/16"]  # Replace with a specific IP or range in production
    description = "Allow database access from VPC"
  }

  egress {
    from_port   = 0
    to_port    = 0
    protocol   = "-1"
    cidr_blocks = ["10.0.0.0/16"]
    description = "Allow egress traffic within the VPC"
  }
}

resource "aws_security_group_rule" "allow_db_egress" {
  security_group_id = aws_security_group.db_access.id
  type              = "egress"
  from_port         = 0
  to_port           = 0
  protocol          = "-1"
  cidr_blocks       = ["10.0.0.0/16"]
  description       = "Allow egress traffic within the VPC"
}

resource "aws_security_group_rule" "allow_all_egress" {
  security_group_id = aws_security_group.db_access.id
  type              = "egress"
  from_port         = 0
  to_port           = 0
  protocol          = "-1"
  cidr_blocks       = ["10.0.0.0/16"]
  description       = "Allow egress traffic within the VPC"
}
