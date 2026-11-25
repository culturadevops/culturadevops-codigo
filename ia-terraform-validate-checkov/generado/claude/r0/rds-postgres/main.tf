terraform {
  required_version = ">= 1.5.0"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = ">= 5.0"
    }
  }
}

provider "aws" {
  region = "us-east-1"

  default_tags {
    tags = {
      Project     = var.project_name
      Environment = var.environment
      ManagedBy   = "terraform"
    }
  }
}

# -----------------------------------------------------------------------------
# Variables
# -----------------------------------------------------------------------------

variable "project_name" {
  description = "Nombre del proyecto/aplicación"
  type        = string
  default     = "miapp"
}

variable "environment" {
  description = "Entorno (dev, staging, prod)"
  type        = string
  default     = "prod"
}

variable "vpc_id" {
  description = "ID de la VPC donde se desplegará RDS"
  type        = string
}

variable "private_subnet_ids" {
  description = "Subredes privadas (mínimo 2, en distintas AZ) para el DB subnet group"
  type        = list(string)
}

variable "app_security_group_ids" {
  description = "Security groups de la aplicación autorizados a conectarse a la BD"
  type        = list(string)
  default     = []
}

variable "allowed_cidr_blocks" {
  description = "CIDR adicionales autorizados (opcional, p. ej. una VPN)"
  type        = list(string)
  default     = []
}

variable "db_name" {
  description = "Nombre de la base de datos inicial"
  type        = string
  default     = "appdb"
}

variable "db_username" {
  description = "Usuario maestro de la base de datos"
  type        = string
  default     = "appadmin"
}

variable "engine_version" {
  description = "Versión mayor de PostgreSQL"
  type        = string
  default     = "16"
}

variable "instance_class" {
  description = "Clase de instancia RDS"
  type        = string
  default     = "db.t4g.medium"
}

variable "allocated_storage" {
  description = "Almacenamiento inicial en GB"
  type        = number
  default     = 20
}

variable "max_allocated_storage" {
  description = "Límite de autoescalado de almacenamiento en GB"
  type        = number
  default     = 100
}

variable "multi_az" {
  description = "Habilitar despliegue Multi-AZ"
  type        = bool
  default     = true
}

variable "backup_retention_days" {
  description = "Días de retención de backups automáticos"
  type        = number
  default     = 7
}

# -----------------------------------------------------------------------------
# Locals
# -----------------------------------------------------------------------------

locals {
  name = "${var.project_name}-${var.environment}"
}

# -----------------------------------------------------------------------------
# Red
# -----------------------------------------------------------------------------

resource "aws_db_subnet_group" "this" {
  name        = "${local.name}-db-subnets"
  description = "Subredes privadas para ${local.name} RDS"
  subnet_ids  = var.private_subnet_ids
}

resource "aws_security_group" "rds" {
  name        = "${local.name}-rds-sg"
  description = "Acceso a PostgreSQL para ${local.name}"
  vpc_id      = var.vpc_id

  tags = {
    Name = "${local.name}-rds-sg"
  }
}

resource "aws_vpc_security_group_ingress_rule" "from_app_sg" {
  for_each = toset(var.app_security_group_ids)

  security_group_id            = aws_security_group.rds.id
  referenced_security_group_id = each.value
  ip_protocol                  = "tcp"
  from_port                    = 5432
  to_port                      = 5432
  description                  = "PostgreSQL desde la aplicación"
}

resource "aws_vpc_security_group_ingress_rule" "from_cidr" {
  for_each = toset(var.allowed_cidr_blocks)

  security_group_id = aws_security_group.rds.id
  cidr_ipv4         = each.value
  ip_protocol       = "tcp"
  from_port         = 5432
  to_port           = 5432
  description       = "PostgreSQL desde CIDR autorizado"
}

resource "aws_vpc_security_group_egress_rule" "all" {
  security_group_id = aws_security_group.rds.id
  cidr_ipv4         = "0.0.0.0/0"
  ip_protocol       = "-1"
}

# -----------------------------------------------------------------------------
# Cifrado
# -----------------------------------------------------------------------------

resource "aws_kms_key" "rds" {
  description             = "Clave KMS para ${local.name} RDS"
  deletion_window_in_days = 30
  enable_key_rotation     = true
}

resource "aws_kms_alias" "rds" {
  name          = "alias/${local.name}-rds"
  target_key_id = aws_kms_key.rds.key_id
}

# -----------------------------------------------------------------------------
# Parámetros de PostgreSQL
# -----------------------------------------------------------------------------

resource "aws_db_parameter_group" "this" {
  name        = "${local.name}-pg${var.engine_version}"
  family      = "postgres${var.engine_version}"
  description = "Parámetros PostgreSQL para ${local.name}"

  parameter {
    name  = "rds.force_ssl"
    value = "1"
  }

  parameter {
    name  = "log_min_duration_statement"
    value = "1000"
  }

  parameter {
    name  = "log_connections"
    value = "1"
  }

  lifecycle {
    create_before_destroy = true
  }
}

# -----------------------------------------------------------------------------
# Monitorización mejorada
# -----------------------------------------------------------------------------

data "aws_iam_policy_document" "rds_monitoring_assume" {
  statement {
    actions = ["sts:AssumeRole"]
    principals {
      type        = "Service"
      identifiers = ["monitoring.rds.amazonaws.com"]
    }
  }
}

resource "aws_iam_role" "rds_monitoring" {
  name               = "${local.name}-rds-monitoring"
  assume_role_policy = data.aws_iam_policy_document.rds_monitoring_assume.json
}

resource "aws_iam_role_policy_attachment" "rds_monitoring" {
  role       = aws_iam_role.rds_monitoring.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AmazonRDSEnhancedMonitoringRole"
}

# -----------------------------------------------------------------------------
# Instancia RDS PostgreSQL
# -----------------------------------------------------------------------------

resource "aws_db_instance" "this" {
  identifier     = "${local.name}-postgres"
  engine         = "postgres"
  engine_version = var.engine_version
  instance_class = var.instance_class

  db_name  = var.db_name
  username = var.db_username
  port     = 5432

  # Contraseña gestionada por AWS en Secrets Manager (sin secretos en el state)
  manage_master_user_password   = true
  master_user_secret_kms_key_id = aws_kms_key.rds.arn

  allocated_storage     = var.allocated_storage
  max_allocated_storage = var.max_allocated_storage
  storage_type          = "gp3"
  storage_encrypted     = true
  kms_key_id            = aws_kms_key.rds.arn

  db_subnet_group_name   = aws_db_subnet_group.this.name
  vpc_security_group_ids = [aws_security_group.rds.id]
  publicly_accessible    = false
  multi_az               = var.multi_az

  parameter_group_name = aws_db_parameter_group.this.name

  iam_database_authentication_enabled = true

  backup_retention_period  = var.backup_retention_days
  backup_window            = "03:00-04:00"
  maintenance_window       = "sun:04:30-sun:05:30"
  copy_tags_to_snapshot    = true
  delete_automated_backups = false

  auto_minor_version_upgrade  = true
  allow_major_version_upgrade = false

  performance_insights_enabled          = true
  performance_insights_kms_key_id       = aws_kms_key.rds.arn
  performance_insights_retention_period = 7

  monitoring_interval = 60
  monitoring_role_arn = aws_iam_role.rds_monitoring.arn

  enabled_cloudwatch_logs_exports = ["postgresql", "upgrade"]

  deletion_protection       = true
  skip_final_snapshot       = false
  final_snapshot_identifier = "${local.name}-postgres-final"

  apply_immediately = false

  depends_on = [aws_iam_role_policy_attachment.rds_monitoring]

  tags = {
    Name = "${local.name}-postgres"
  }
}

# -----------------------------------------------------------------------------
# Outputs
# -----------------------------------------------------------------------------

output "db_endpoint" {
  description = "Endpoint de conexión (host:puerto)"
  value       = aws_db_instance.this.endpoint
}

output "db_address" {
  description = "Hostname de la instancia"
  value       = aws_db_instance.this.address
}

output "db_port" {
  description = "Puerto de PostgreSQL"
  value       = aws_db_instance.this.port
}

output "db_name" {
  description = "Nombre de la base de datos"
  value       = aws_db_instance.this.db_name
}

output "db_master_user_secret_arn" {
  description = "ARN del secreto en Secrets Manager con las credenciales maestras"
  value       = aws_db_instance.this.master_user_secret[0].secret_arn
}

output "db_security_group_id" {
  description = "Security group de RDS"
  value       = aws_security_group.rds.id
}
