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

variable "allowed_ssh_cidr" {
  description = "CIDR autorizado para SSH (tu IP pública, ej. 203.0.113.10/32)"
  type        = string

  validation {
    condition     = can(cidrhost(var.allowed_ssh_cidr, 0)) && var.allowed_ssh_cidr != "0.0.0.0/0"
    error_message = "Debe ser un CIDR válido y distinto de 0.0.0.0/0 (usa tu IP/32)."
  }
}

variable "public_key_path" {
  description = "Ruta a la clave pública SSH que se registrará en AWS"
  type        = string
  default     = "~/.ssh/id_ed25519.pub"
}

variable "instance_name" {
  description = "Nombre de la instancia"
  type        = string
  default     = "ubuntu-t3-micro"
}

# ---------------------------------------------------------------------------
# Datos: VPC por defecto y AMI oficial de Ubuntu 24.04 LTS (Canonical)
# ---------------------------------------------------------------------------

data "aws_vpc" "default" {
  default = true
}

data "aws_ami" "ubuntu" {
  most_recent = true
  owners      = ["099720109477"] # Canonical

  filter {
    name   = "name"
    values = ["ubuntu/images/hvm-ssd-gp3/ubuntu-noble-24.04-amd64-server-*"]
  }

  filter {
    name   = "virtualization-type"
    values = ["hvm"]
  }

  filter {
    name   = "architecture"
    values = ["x86_64"]
  }
}

# ---------------------------------------------------------------------------
# Par de claves SSH
# ---------------------------------------------------------------------------

resource "aws_key_pair" "this" {
  key_name   = "${var.instance_name}-key"
  public_key = file(pathexpand(var.public_key_path))
}

# ---------------------------------------------------------------------------
# Security Group: SSH solo desde tu IP
# ---------------------------------------------------------------------------

resource "aws_security_group" "ssh" {
  name        = "${var.instance_name}-ssh"
  description = "Permite SSH desde una IP autorizada"
  vpc_id      = data.aws_vpc.default.id

  ingress {
    description = "SSH"
    from_port   = 22
    to_port     = 22
    protocol    = "tcp"
    cidr_blocks = [var.allowed_ssh_cidr]
  }

  egress {
    description = "Salida a Internet"
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    Name = "${var.instance_name}-ssh"
  }
}

# ---------------------------------------------------------------------------
# Instancia EC2
# ---------------------------------------------------------------------------

resource "aws_instance" "this" {
  ami                         = data.aws_ami.ubuntu.id
  instance_type               = "t3.micro"
  key_name                    = aws_key_pair.this.key_name
  vpc_security_group_ids      = [aws_security_group.ssh.id]
  associate_public_ip_address = true

  metadata_options {
    http_tokens   = "required" # IMDSv2 obligatorio
    http_endpoint = "enabled"
  }

  root_block_device {
    volume_type           = "gp3"
    volume_size           = 8
    encrypted             = true
    delete_on_termination = true
  }

  tags = {
    Name = var.instance_name
  }
}

# ---------------------------------------------------------------------------
# Salidas
# ---------------------------------------------------------------------------

output "public_ip" {
  description = "IP pública de la instancia"
  value       = aws_instance.this.public_ip
}

output "ssh_command" {
  description = "Comando para conectarse por SSH"
  value       = "ssh -i ${replace(pathexpand(var.public_key_path), ".pub", "")} ubuntu@${aws_instance.this.public_ip}"
}
