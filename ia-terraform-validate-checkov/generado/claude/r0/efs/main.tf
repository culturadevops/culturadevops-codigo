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

  default_tags {
    tags = {
      Project   = var.project_name
      ManagedBy = "terraform"
    }
  }
}

# -----------------------------------------------------------------------------
# Variables
# -----------------------------------------------------------------------------

variable "project_name" {
  description = "Prefijo para nombrar los recursos"
  type        = string
  default     = "efs-compartido"
}

variable "instance_count" {
  description = "Número de instancias EC2 que montarán el EFS"
  type        = number
  default     = 2
}

variable "instance_type" {
  description = "Tipo de instancia EC2"
  type        = string
  default     = "t3.micro"
}

variable "availability_zones" {
  description = "AZs donde se crearán mount targets e instancias"
  type        = list(string)
  default     = ["us-east-1a", "us-east-1b", "us-east-1c"]
}

variable "mount_point" {
  description = "Ruta de montaje del EFS en las instancias"
  type        = string
  default     = "/mnt/efs"
}

# -----------------------------------------------------------------------------
# Red (VPC por defecto)
# -----------------------------------------------------------------------------

data "aws_vpc" "default" {
  default = true
}

data "aws_subnets" "selected" {
  filter {
    name   = "vpc-id"
    values = [data.aws_vpc.default.id]
  }

  filter {
    name   = "availability-zone"
    values = var.availability_zones
  }

  filter {
    name   = "default-for-az"
    values = ["true"]
  }
}

locals {
  subnet_ids = sort(data.aws_subnets.selected.ids)
}

# -----------------------------------------------------------------------------
# Security Groups
# -----------------------------------------------------------------------------

resource "aws_security_group" "instances" {
  name        = "${var.project_name}-instances"
  description = "Instancias que montan el EFS"
  vpc_id      = data.aws_vpc.default.id

  egress {
    description = "Todo el trafico saliente"
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    Name = "${var.project_name}-instances"
  }
}

resource "aws_security_group" "efs" {
  name        = "${var.project_name}-efs"
  description = "Acceso NFS al EFS solo desde las instancias"
  vpc_id      = data.aws_vpc.default.id

  ingress {
    description     = "NFS desde las instancias"
    from_port       = 2049
    to_port         = 2049
    protocol        = "tcp"
    security_groups = [aws_security_group.instances.id]
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    Name = "${var.project_name}-efs"
  }
}

# -----------------------------------------------------------------------------
# EFS
# -----------------------------------------------------------------------------

resource "aws_efs_file_system" "this" {
  creation_token   = "${var.project_name}-fs"
  encrypted        = true
  performance_mode = "generalPurpose"
  throughput_mode  = "elastic"

  lifecycle_policy {
    transition_to_ia = "AFTER_30_DAYS"
  }

  lifecycle_policy {
    transition_to_primary_storage_class = "AFTER_1_ACCESS"
  }

  tags = {
    Name = "${var.project_name}-fs"
  }
}

resource "aws_efs_backup_policy" "this" {
  file_system_id = aws_efs_file_system.this.id

  backup_policy {
    status = "ENABLED"
  }
}

resource "aws_efs_mount_target" "this" {
  for_each = toset(local.subnet_ids)

  file_system_id  = aws_efs_file_system.this.id
  subnet_id       = each.value
  security_groups = [aws_security_group.efs.id]
}

resource "aws_efs_access_point" "shared" {
  file_system_id = aws_efs_file_system.this.id

  posix_user {
    uid = 1000
    gid = 1000
  }

  root_directory {
    path = "/shared"

    creation_info {
      owner_uid   = 1000
      owner_gid   = 1000
      permissions = "0775"
    }
  }

  tags = {
    Name = "${var.project_name}-ap-shared"
  }
}

resource "aws_efs_file_system_policy" "this" {
  file_system_id = aws_efs_file_system.this.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Sid       = "AllowMountViaMountTargets"
        Effect    = "Allow"
        Principal = { AWS = "*" }
        Action = [
          "elasticfilesystem:ClientMount",
          "elasticfilesystem:ClientWrite"
        ]
        Resource = aws_efs_file_system.this.arn
        Condition = {
          Bool = {
            "elasticfilesystem:AccessedViaMountTarget" = "true"
          }
        }
      },
      {
        Sid       = "DenyInsecureTransport"
        Effect    = "Deny"
        Principal = { AWS = "*" }
        Action    = "*"
        Resource  = aws_efs_file_system.this.arn
        Condition = {
          Bool = {
            "aws:SecureTransport" = "false"
          }
        }
      }
    ]
  })
}

# -----------------------------------------------------------------------------
# IAM (acceso por SSM Session Manager, sin SSH)
# -----------------------------------------------------------------------------

resource "aws_iam_role" "instance" {
  name = "${var.project_name}-instance-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect    = "Allow"
      Principal = { Service = "ec2.amazonaws.com" }
      Action    = "sts:AssumeRole"
    }]
  })
}

resource "aws_iam_role_policy_attachment" "ssm" {
  role       = aws_iam_role.instance.name
  policy_arn = "arn:aws:iam::aws:policy/AmazonSSMManagedInstanceCore"
}

resource "aws_iam_instance_profile" "instance" {
  name = "${var.project_name}-instance-profile"
  role = aws_iam_role.instance.name
}

# -----------------------------------------------------------------------------
# Instancias EC2 que comparten el EFS
# -----------------------------------------------------------------------------

data "aws_ssm_parameter" "al2023" {
  name = "/aws/service/ami-amazon-linux-latest/al2023-ami-kernel-default-x86_64"
}

resource "aws_instance" "app" {
  count = var.instance_count

  ami                         = data.aws_ssm_parameter.al2023.value
  instance_type               = var.instance_type
  subnet_id                   = local.subnet_ids[count.index % length(local.subnet_ids)]
  vpc_security_group_ids      = [aws_security_group.instances.id]
  iam_instance_profile        = aws_iam_instance_profile.instance.name
  associate_public_ip_address = true

  metadata_options {
    http_tokens = "required"
  }

  root_block_device {
    encrypted   = true
    volume_type = "gp3"
  }

  user_data_replace_on_change = true
  user_data                   = <<-EOF
    #!/bin/bash
    set -euxo pipefail

    dnf install -y amazon-efs-utils

    mkdir -p ${var.mount_point}

    echo "${aws_efs_file_system.this.id}:/ ${var.mount_point} efs _netdev,noresvport,tls,accesspoint=${aws_efs_access_point.shared.id} 0 0" >> /etc/fstab

    for i in $(seq 1 30); do
      mount -a -t efs && break
      sleep 10
    done

    echo "Hola desde $(hostname) - $(date -Is)" >> ${var.mount_point}/instancias.log
  EOF

  tags = {
    Name = "${var.project_name}-app-${count.index + 1}"
  }

  depends_on = [
    aws_efs_mount_target.this,
    aws_efs_file_system_policy.this
  ]
}

# -----------------------------------------------------------------------------
# Outputs
# -----------------------------------------------------------------------------

output "efs_id" {
  description = "ID del sistema de archivos EFS"
  value       = aws_efs_file_system.this.id
}

output "efs_dns_name" {
  description = "DNS del EFS"
  value       = aws_efs_file_system.this.dns_name
}

output "efs_access_point_id" {
  description = "ID del access point compartido"
  value       = aws_efs_access_point.shared.id
}

output "instance_ids" {
  description = "IDs de las instancias que montan el EFS"
  value       = aws_instance.app[*].id
}

output "mount_command" {
  description = "Comando para montar el EFS manualmente"
  value       = "sudo mount -t efs -o tls,accesspoint=${aws_efs_access_point.shared.id} ${aws_efs_file_system.this.id}:/ ${var.mount_point}"
}
