terraform {
  required_version = ">= 1.5.0"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = ">= 5.0, < 7.0"
    }
    random = {
      source  = "hashicorp/random"
      version = "~> 3.6"
    }
  }
}

provider "aws" {
  region = "us-east-1"

  default_tags {
    tags = {
      Project   = var.name
      ManagedBy = "terraform"
    }
  }
}

# -----------------------------------------------------------------------------
# Variables
# -----------------------------------------------------------------------------

variable "name" {
  description = "Prefijo para nombrar los recursos"
  type        = string
  default     = "app-cache"
}

variable "vpc_id" {
  description = "ID de la VPC donde se desplegará Redis"
  type        = string
}

variable "subnet_ids" {
  description = "Subnets privadas (al menos 2 en AZs distintas) para el subnet group"
  type        = list(string)
}

variable "allowed_security_group_ids" {
  description = "Security groups de las aplicaciones que pueden conectarse a Redis"
  type        = list(string)
  default     = []
}

variable "allowed_cidr_blocks" {
  description = "Rangos CIDR que pueden conectarse a Redis (opcional)"
  type        = list(string)
  default     = []
}

variable "node_type" {
  description = "Tipo de instancia de los nodos de caché"
  type        = string
  default     = "cache.t4g.small"
}

variable "engine_version" {
  description = "Versión del motor Redis"
  type        = string
  default     = "7.1"
}

variable "num_cache_clusters" {
  description = "Número de nodos (1 primario + réplicas). Mínimo 2 para failover automático"
  type        = number
  default     = 2
}

# -----------------------------------------------------------------------------
# Red y seguridad
# -----------------------------------------------------------------------------

resource "aws_elasticache_subnet_group" "this" {
  name        = "${var.name}-subnets"
  description = "Subnet group para ${var.name}"
  subnet_ids  = var.subnet_ids
}

resource "aws_security_group" "redis" {
  name        = "${var.name}-redis-sg"
  description = "Acceso a ElastiCache Redis"
  vpc_id      = var.vpc_id
}

resource "aws_vpc_security_group_ingress_rule" "from_sg" {
  for_each = toset(var.allowed_security_group_ids)

  security_group_id            = aws_security_group.redis.id
  referenced_security_group_id = each.value
  ip_protocol                  = "tcp"
  from_port                    = 6379
  to_port                      = 6379
  description                  = "Redis desde ${each.value}"
}

resource "aws_vpc_security_group_ingress_rule" "from_cidr" {
  for_each = toset(var.allowed_cidr_blocks)

  security_group_id = aws_security_group.redis.id
  cidr_ipv4         = each.value
  ip_protocol       = "tcp"
  from_port         = 6379
  to_port           = 6379
  description       = "Redis desde ${each.value}"
}

resource "aws_vpc_security_group_egress_rule" "all" {
  security_group_id = aws_security_group.redis.id
  cidr_ipv4         = "0.0.0.0/0"
  ip_protocol       = "-1"
}

# -----------------------------------------------------------------------------
# Parámetros de Redis orientados a caché
# -----------------------------------------------------------------------------

resource "aws_elasticache_parameter_group" "this" {
  name        = "${var.name}-redis7"
  family      = "redis7"
  description = "Parametros de cache para ${var.name}"

  # Expulsa las claves menos usadas cuando se llena la memoria
  parameter {
    name  = "maxmemory-policy"
    value = "allkeys-lru"
  }
}

# -----------------------------------------------------------------------------
# Autenticación
# -----------------------------------------------------------------------------

resource "random_password" "auth_token" {
  length           = 32
  special          = true
  override_special = "!&#$^<>-"
}

# -----------------------------------------------------------------------------
# Clúster Redis (replication group)
# -----------------------------------------------------------------------------

resource "aws_elasticache_replication_group" "this" {
  replication_group_id = var.name
  description          = "Redis cache para ${var.name}"

  engine               = "redis"
  engine_version       = var.engine_version
  node_type            = var.node_type
  port                 = 6379
  parameter_group_name = aws_elasticache_parameter_group.this.name

  num_cache_clusters         = var.num_cache_clusters
  automatic_failover_enabled = var.num_cache_clusters > 1
  multi_az_enabled           = var.num_cache_clusters > 1

  subnet_group_name  = aws_elasticache_subnet_group.this.name
  security_group_ids = [aws_security_group.redis.id]

  at_rest_encryption_enabled = true
  transit_encryption_enabled = true
  auth_token                 = random_password.auth_token.result

  snapshot_retention_limit = 1
  snapshot_window          = "03:00-04:00"
  maintenance_window       = "sun:05:00-sun:06:00"

  auto_minor_version_upgrade = true
  apply_immediately          = false
}

# -----------------------------------------------------------------------------
# Outputs
# -----------------------------------------------------------------------------

output "primary_endpoint" {
  description = "Endpoint de escritura"
  value       = aws_elasticache_replication_group.this.primary_endpoint_address
}

output "reader_endpoint" {
  description = "Endpoint de lectura"
  value       = aws_elasticache_replication_group.this.reader_endpoint_address
}

output "port" {
  value = aws_elasticache_replication_group.this.port
}

output "auth_token" {
  description = "Token AUTH de Redis"
  value       = random_password.auth_token.result
  sensitive   = true
}
