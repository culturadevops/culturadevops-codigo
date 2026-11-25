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

variable "vpc_id" {
  description = "ID de la VPC donde se creará el security group (vacío = VPC por defecto)"
  type        = string
  default     = ""
}

variable "subnet_id" {
  description = "ID de la subred donde se creará la interfaz de red del servidor web (vacío = primera subred de la VPC)"
  type        = string
  default     = ""
}

variable "ssh_allowed_cidr" {
  description = "CIDR autorizado para SSH (restringir a tu IP, p. ej. 203.0.113.10/32)"
  type        = string

  validation {
    condition     = can(cidrhost(var.ssh_allowed_cidr, 0)) && var.ssh_allowed_cidr != "0.0.0.0/0"
    error_message = "Debe ser un CIDR válido y no se permite 0.0.0.0/0 para SSH."
  }
}

data "aws_vpc" "default" {
  default = true
}

locals {
  vpc_id = var.vpc_id != "" ? var.vpc_id : data.aws_vpc.default.id
}

data "aws_subnets" "selected" {
  filter {
    name   = "vpc-id"
    values = [local.vpc_id]
  }
}

locals {
  subnet_id = var.subnet_id != "" ? var.subnet_id : sort(data.aws_subnets.selected.ids)[0]
}

resource "aws_security_group" "web" {
  name        = "web-server-sg"
  description = "Permite HTTPS y SSH al servidor web"
  vpc_id      = local.vpc_id

  tags = {
    Name = "web-server-sg"
  }
}

# HTTPS desde cualquier origen (HTTP en texto plano deshabilitado)
resource "aws_vpc_security_group_ingress_rule" "https_ipv4" {
  security_group_id = aws_security_group.web.id
  description       = "HTTPS"
  cidr_ipv4         = "0.0.0.0/0"
  ip_protocol       = "tcp"
  from_port         = 443
  to_port           = 443
}

resource "aws_vpc_security_group_ingress_rule" "https_ipv6" {
  security_group_id = aws_security_group.web.id
  description       = "HTTPS IPv6"
  cidr_ipv6         = "::/0"
  ip_protocol       = "tcp"
  from_port         = 443
  to_port           = 443
}

# SSH solo desde el CIDR autorizado
resource "aws_vpc_security_group_ingress_rule" "ssh" {
  security_group_id = aws_security_group.web.id
  description       = "SSH restringido"
  cidr_ipv4         = var.ssh_allowed_cidr
  ip_protocol       = "tcp"
  from_port         = 22
  to_port           = 22
}

# Todo el tráfico saliente
resource "aws_vpc_security_group_egress_rule" "all_ipv4" {
  security_group_id = aws_security_group.web.id
  description       = "Salida IPv4"
  cidr_ipv4         = "0.0.0.0/0"
  ip_protocol       = "-1"
}

resource "aws_vpc_security_group_egress_rule" "all_ipv6" {
  security_group_id = aws_security_group.web.id
  description       = "Salida IPv6"
  cidr_ipv6         = "::/0"
  ip_protocol       = "-1"
}

# Interfaz de red del servidor web asociada al security group
resource "aws_network_interface" "web" {
  subnet_id       = local.subnet_id
  security_groups = [aws_security_group.web.id]
  description     = "Interfaz de red del servidor web"

  tags = {
    Name = "web-server-eni"
  }
}

output "security_group_id" {
  description = "ID del security group del servidor web"
  value       = aws_security_group.web.id
}

output "network_interface_id" {
  description = "ID de la interfaz de red del servidor web (asociar a la instancia EC2)"
  value       = aws_network_interface.web.id
}
