terraform {
  required_version = ">= 1.5.0"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
    random = {
      source  = "hashicorp/random"
      version = "~> 3.6"
    }
  }
}

provider "aws" {
  region = "us-east-1"
}

variable "secret_name" {
  description = "Nombre del secreto en Secrets Manager"
  type        = string
  default     = "prod/app/db-password"
}

variable "db_username" {
  description = "Usuario de la base de datos"
  type        = string
  default     = "app_admin"
}

variable "db_host" {
  description = "Endpoint de la base de datos"
  type        = string
  default     = "mydb.cluster-xxxxxxxx.us-east-1.rds.amazonaws.com"
}

variable "db_port" {
  description = "Puerto de la base de datos"
  type        = number
  default     = 5432
}

variable "db_name" {
  description = "Nombre de la base de datos"
  type        = string
  default     = "appdb"
}

# Contraseña generada aleatoriamente (nunca hardcodeada en el código)
resource "random_password" "db" {
  length           = 32
  special          = true
  override_special = "!#$%&*()-_=+[]{}<>:?"
  min_lower        = 2
  min_upper        = 2
  min_numeric      = 2
  min_special      = 2
}

# Clave KMS gestionada por el cliente para cifrar el secreto
resource "aws_kms_key" "secrets" {
  description             = "CMK para cifrar secretos de base de datos"
  deletion_window_in_days = 30
  enable_key_rotation     = true
}

resource "aws_kms_alias" "secrets" {
  name          = "alias/db-secrets"
  target_key_id = aws_kms_key.secrets.key_id
}

resource "aws_secretsmanager_secret" "db" {
  name                    = var.secret_name
  description             = "Credenciales de la base de datos de la aplicación"
  kms_key_id              = aws_kms_key.secrets.arn
  recovery_window_in_days = 7

  tags = {
    Environment = "prod"
    ManagedBy   = "terraform"
  }
}

resource "aws_secretsmanager_secret_version" "db" {
  secret_id = aws_secretsmanager_secret.db.id
  secret_string = jsonencode({
    username = var.db_username
    password = random_password.db.result
    engine   = "postgres"
    host     = var.db_host
    port     = var.db_port
    dbname   = var.db_name
  })
}

output "db_secret_arn" {
  description = "ARN del secreto con las credenciales de la base de datos"
  value       = aws_secretsmanager_secret.db.arn
}

output "db_secret_name" {
  description = "Nombre del secreto"
  value       = aws_secretsmanager_secret.db.name
}
