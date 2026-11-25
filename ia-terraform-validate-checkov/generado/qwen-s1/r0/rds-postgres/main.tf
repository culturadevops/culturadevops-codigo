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

resource "aws_rds_instance" "postgres" {
  identifier             = "terraform-postgres"
  instance_class         = "db.t3.micro"
  engine                 = "postgres"
  engine_version         = "14.2"
  username               = "admin"
  password               = "YourStrongPassword123"
  name                   = "my-postgres-db"
  allocated_storage      = 20
  storage_encrypted      = true
  backup_retention_period = 7
  backup_window           = "07:00-09:00"
  maintenance_window     = "mon:07:00-09:00"
  parameter_group_name   = "default.postgres14"
  vpc_security_group_ids = ["sg-0123456789abcdef0"]  # Replace with your VPC security group ID
  publicly_accessible    = false
}

resource "aws_rds_cluster_parameter_group" "postgres" {
  name        = "terraform-postgres-param-group"
  family      = "postgres14"
  description = "Parameter group for Terraform-managed PostgreSQL RDS instance"
}

resource "aws_rds_cluster_parameter" "postgres" {
  for_each = toset(["enable_log shipping"])

  name         = each.value
  value        = "on"
  parameter_group_name = aws_rds_cluster_parameter_group.postgres.name
}
