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
# Nota de diseño
# ---------------------------------------------------------------------------
# Para cumplir CKV_AWS_88 la instancia ya NO tiene IP pública, por lo que el
# acceso SSH directo desde Internet desaparece. El acceso se hace mediante
# AWS Systems Manager Session Manager (SSH tunelizado por SSM), usando VPC
# Interface Endpoints privados. Requisitos en tu equipo:
#   - AWS CLI v2
#   - Session Manager Plugin
# Las interface endpoints tienen coste (~0,01 USD/h cada una por AZ).
# Sin NAT ni IP pública, la instancia no tiene salida a Internet (apt update
# no funcionará salvo que añadas NAT Gateway o un proxy).

# ---------------------------------------------------------------------------
# Variables
# ---------------------------------------------------------------------------

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

variable "availability_zone" {
  description = "AZ donde se despliegan la instancia y los endpoints (debe soportar t3.micro)"
  type        = string
  default     = "us-east-1a"
}

# ---------------------------------------------------------------------------
# Datos: VPC por defecto, subred y AMI oficial de Ubuntu 24.04 LTS (Canonical)
# ---------------------------------------------------------------------------

data "aws_region" "current" {}

data "aws_vpc" "default" {
  default = true
}

data "aws_subnet" "selected" {
  vpc_id            = data.aws_vpc.default.id
  availability_zone = var.availability_zone
  default_for_az    = true
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
# Par de claves SSH (se usa a través del túnel de Session Manager)
# ---------------------------------------------------------------------------

resource "aws_key_pair" "this" {
  key_name   = "${var.instance_name}-key"
  public_key = file(pathexpand(var.public_key_path))
}

# ---------------------------------------------------------------------------
# IAM: rol de instancia con permisos mínimos para Session Manager
# ---------------------------------------------------------------------------

data "aws_iam_policy_document" "ec2_assume_role" {
  statement {
    sid     = "EC2AssumeRole"
    effect  = "Allow"
    actions = ["sts:AssumeRole"]

    principals {
      type        = "Service"
      identifiers = ["ec2.amazonaws.com"]
    }
  }
}

resource "aws_iam_role" "this" {
  name               = "${var.instance_name}-role"
  assume_role_policy = data.aws_iam_policy_document.ec2_assume_role.json

  tags = {
    Name = "${var.instance_name}-role"
  }
}

resource "aws_iam_role_policy_attachment" "ssm_core" {
  role       = aws_iam_role.this.name
  policy_arn = "arn:aws:iam::aws:policy/AmazonSSMManagedInstanceCore"
}

resource "aws_iam_instance_profile" "this" {
  name = "${var.instance_name}-profile"
  role = aws_iam_role.this.name
}

# ---------------------------------------------------------------------------
# Security Groups
# ---------------------------------------------------------------------------

# Instancia: sin ingress; egress solo HTTPS dentro de la VPC (endpoints SSM)
resource "aws_security_group" "instance" {
  name        = "${var.instance_name}-instance"
  description = "Instancia sin ingress; HTTPS saliente solo hacia la VPC"
  vpc_id      = data.aws_vpc.default.id

  egress {
    description = "HTTPS hacia los VPC endpoints de SSM"
    from_port   = 443
    to_port     = 443
    protocol    = "tcp"
    cidr_blocks = [data.aws_vpc.default.cidr_block]
  }

  tags = {
    Name = "${var.instance_name}-instance"
  }
}

# Endpoints: HTTPS entrante solo desde la instancia
resource "aws_security_group" "endpoints" {
  name        = "${var.instance_name}-ssm-endpoints"
  description = "HTTPS entrante a los VPC endpoints de SSM desde la instancia"
  vpc_id      = data.aws_vpc.default.id

  ingress {
    description     = "HTTPS desde la instancia"
    from_port       = 443
    to_port         = 443
    protocol        = "tcp"
    security_groups = [aws_security_group.instance.id]
  }

  tags = {
    Name = "${var.instance_name}-ssm-endpoints"
  }
}

# ---------------------------------------------------------------------------
# VPC Interface Endpoints para Session Manager
# ---------------------------------------------------------------------------

resource "aws_vpc_endpoint" "ssm" {
  for_each = toset(["ssm", "ssmmessages", "ec2messages"])

  vpc_id              = data.aws_vpc.default.id
  service_name        = "com.amazonaws.${data.aws_region.current.name}.${each.key}"
  vpc_endpoint_type   = "Interface"
  subnet_ids          = [data.aws_subnet.selected.id]
  security_group_ids  = [aws_security_group.endpoints.id]
  private_dns_enabled = true

  tags = {
    Name = "${var.instance_name}-${each.key}"
  }
}

# ---------------------------------------------------------------------------
# Instancia EC2
# ---------------------------------------------------------------------------

resource "aws_instance" "this" {
  ami                         = data.aws_ami.ubuntu.id
  instance_type               = "t3.micro"
  subnet_id                   = data.aws_subnet.selected.id
  key_name                    = aws_key_pair.this.key_name
  vpc_security_group_ids      = [aws_security_group.instance.id]
  iam_instance_profile        = aws_iam_instance_profile.this.name
  associate_public_ip_address = false
  ebs_optimized               = true
  monitoring                  = true

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

  depends_on = [aws_vpc_endpoint.ssm]
}

# ---------------------------------------------------------------------------
# Salidas
# ---------------------------------------------------------------------------

output "instance_id" {
  description = "ID de la instancia"
  value       = aws_instance.this.id
}

output "private_ip" {
  description = "IP privada de la instancia"
  value       = aws_instance.this.private_ip
}

output "ssm_session_command" {
  description = "Abrir una shell mediante Session Manager"
  value       = "aws ssm start-session --region ${data.aws_region.current.name} --target ${aws_instance.this.id}"
}

output "ssh_command" {
  description = "SSH tunelizado a través de Session Manager"
  value       = "ssh -i ${replace(pathexpand(var.public_key_path), ".pub", "")} -o ProxyCommand=\"aws ssm start-session --region ${data.aws_region.current.name} --target %h --document-name AWS-StartSSHSession --parameters portNumber=%p\" ubuntu@${aws_instance.this.id}"
}
