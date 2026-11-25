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

resource "aws_rds_cluster" "postgres" {
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

  enable_iam_database_authentication = true
  deletion_protection                = true
  enable_cloudwatch_logs_exports     = ["query", "error", "slowquery"]
  enable_performance_insights        = true
  enable_performance_insights_retention_period = 30
}

resource "aws_rds_cluster_parameter_group" "postgres" {
  name        = "terraform-postgres-param-group"
  family      = "postgres14"
  description = "Parameter group for Terraform-managed PostgreSQL RDS instance"
}

resource "aws_rds_cluster_parameter" "postgres" {
  for_each = toset(["enable_log_shipping"])

  name         = each.value
  value        = "on"
  apply_method = "pending-reboot"
  cluster_parameter_group_name = aws_rds_cluster_parameter_group.postgres.name
}

resource "aws_backup_plan" "postgres" {
  name        = "terraform-postgres-backup-plan"
  backup_plan {
    rule {
      rule_name      = "Daily-Backup"
      rule_type      = "RecoveryPoint"
      target_backupvault_name = "terraform-postgres-backup-vault"
      schedule_based_rule {
        schedule_expression = "cron(0 7 * * ? *)"
      }
    }
  }
}

resource "aws_backup_vault" "postgres" {
  name = "terraform-postgres-backup-vault"
}

resource "aws_rds_cluster_snapshot" "postgres" {
  name = "terraform-postgres-snapshot"
  cluster_identifier = aws_rds_cluster.postgres.id
  tags = {
    Name = "terraform-postgres-snapshot"
  }
}

resource "aws_rds_cluster_tag" "postgres" {
  for_each = toset(["Name"])

  key   = each.value
  value = "terraform-managed"
}
