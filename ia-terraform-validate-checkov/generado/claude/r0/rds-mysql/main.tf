terraform {
  required_version = ">= 1.5.0"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

provider "aws" {
  region = "us-east-1"
}

# ---------------------------------------------------------------------------
# Variables
# ---------------------------------------------------------------------------

variable "project_name" {
  description = "Prefijo para nombrar los recursos"
  type        = string
  default     = "wordpress"
}

variable "db_name" {
  description = "Nombre de la base de datos inicial de WordPress"
  type        = string
  default     = "wordpress"
}

variable "db_username" {
  description = "Usuario administrador de MySQL"
  type        = string
  default     = "wpadmin"
}

variable "allowed_cidr_blocks" {
  description = "CIDRs autorizados a conectarse a MySQL (por defecto, solo la VPC)"
  type        = list(string)
  default     = []
}

# ---------------------------------------------------------------------------
# Red: VPC y subredes por defecto
# ---------------------------------------------------------------------------

data "aws_vpc" "default" {
  default = true
}

data "aws_subnets" "default" {
  filter {
    name   = "vpc-id"
    values = [data.aws_vpc.default.id]
  }
}

locals {
  mysql_ingress_cidrs = length(var.allowed_cidr_blocks) > 0 ? var.allowed_cidr_blocks : [data.aws_vpc.default.cidr_block]
}

resource "aws_db_subnet_group" "wordpress" {
  name       = "${var.project_name}-db-subnets"
  subnet_ids = data.aws_subnets.default.ids

  tags = {
    Name = "${var.project_name}-db-subnets"
  }
}

resource "aws_security_group" "rds" {
  name        = "${var.project_name}-rds-sg"
  description = "Acceso MySQL para WordPress"
  vpc_id      = data.aws_vpc.default.id

  ingress {
    description = "MySQL desde la red autorizada"
    from_port   = 3306
    to_port     = 3306
    protocol    = "tcp"
    cidr_blocks = local.mysql_ingress_cidrs
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    Name = "${var.project_name}-rds-sg"
  }
}

# ---------------------------------------------------------------------------
# Instancia RDS MySQL
# ---------------------------------------------------------------------------

resource "aws_db_instance" "wordpress" {
  identifier     = "${var.project_name}-mysql"
  engine         = "mysql"
  engine_version = "8.0"
  instance_class = "db.t4g.micro"

  allocated_storage     = 20
  max_allocated_storage = 50
  storage_type          = "gp3"
  storage_encrypted     = true

  db_name  = var.db_name
  username = var.db_username

  # La contraseña la genera y rota AWS en Secrets Manager (no queda en el state)
  manage_master_user_password = true

  db_subnet_group_name   = aws_db_subnet_group.wordpress.name
  vpc_security_group_ids = [aws_security_group.rds.id]
  publicly_accessible    = false
  multi_az               = false

  backup_retention_period    = 7
  backup_window              = "03:00-04:00"
  maintenance_window         = "sun:04:30-sun:05:30"
  auto_minor_version_upgrade = true
  copy_tags_to_snapshot      = true

  deletion_protection       = true
  skip_final_snapshot       = false
  final_snapshot_identifier = "${var.project_name}-mysql-final"

  tags = {
    Name    = "${var.project_name}-mysql"
    Project = var.project_name
  }
}

# ---------------------------------------------------------------------------
# Outputs
# ---------------------------------------------------------------------------

output "db_endpoint" {
  description = "Endpoint de conexión (host:puerto) para WORDPRESS_DB_HOST"
  value       = aws_db_instance.wordpress.endpoint
}

output "db_name" {
  description = "Nombre de la base de datos"
  value       = aws_db_instance.wordpress.db_name
}

output "db_username" {
  description = "Usuario administrador"
  value       = aws_db_instance.wordpress.username
}

output "db_master_secret_arn" {
  description = "ARN del secreto en Secrets Manager con la contraseña"
  value       = aws_db_instance.wordpress.master_user_secret[0].secret_arn
}

output "rds_security_group_id" {
  description = "ID del security group de la base de datos"
  value       = aws_security_group.rds.id
}
