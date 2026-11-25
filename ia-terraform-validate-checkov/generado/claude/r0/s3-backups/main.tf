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
      Project   = "app-backups"
      ManagedBy = "terraform"
    }
  }
}

variable "bucket_name" {
  description = "Nombre globalmente único del bucket de backups"
  type        = string
  default     = "mi-app-backups-us-east-1"
}

variable "backup_retention_days" {
  description = "Días que se conservan las versiones no actuales de los backups"
  type        = number
  default     = 90
}

# Bucket de backups
resource "aws_s3_bucket" "backups" {
  bucket = var.bucket_name

  # Evita borrar el bucket por accidente con terraform destroy
  lifecycle {
    prevent_destroy = true
  }
}

# Propiedad de objetos: desactiva ACLs
resource "aws_s3_bucket_ownership_controls" "backups" {
  bucket = aws_s3_bucket.backups.id

  rule {
    object_ownership = "BucketOwnerEnforced"
  }
}

# Bloqueo total de acceso público
resource "aws_s3_bucket_public_access_block" "backups" {
  bucket = aws_s3_bucket.backups.id

  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

# Versionado para proteger contra sobrescrituras y borrados
resource "aws_s3_bucket_versioning" "backups" {
  bucket = aws_s3_bucket.backups.id

  versioning_configuration {
    status = "Enabled"
  }
}

# Cifrado en reposo por defecto
resource "aws_s3_bucket_server_side_encryption_configuration" "backups" {
  bucket = aws_s3_bucket.backups.id

  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
    bucket_key_enabled = true
  }
}

# Ciclo de vida: mover a clases más baratas y limpiar versiones antiguas
resource "aws_s3_bucket_lifecycle_configuration" "backups" {
  bucket = aws_s3_bucket.backups.id

  rule {
    id     = "backups-tiering"
    status = "Enabled"

    filter {}

    transition {
      days          = 30
      storage_class = "STANDARD_IA"
    }

    transition {
      days          = 90
      storage_class = "GLACIER"
    }

    noncurrent_version_transition {
      noncurrent_days = 30
      storage_class   = "GLACIER"
    }

    noncurrent_version_expiration {
      noncurrent_days = var.backup_retention_days
    }

    abort_incomplete_multipart_upload {
      days_after_initiation = 7
    }
  }

  depends_on = [aws_s3_bucket_versioning.backups]
}

# Política: solo permitir conexiones HTTPS
data "aws_iam_policy_document" "backups" {
  statement {
    sid     = "DenyInsecureTransport"
    effect  = "Deny"
    actions = ["s3:*"]

    principals {
      type        = "*"
      identifiers = ["*"]
    }

    resources = [
      aws_s3_bucket.backups.arn,
      "${aws_s3_bucket.backups.arn}/*",
    ]

    condition {
      test     = "Bool"
      variable = "aws:SecureTransport"
      values   = ["false"]
    }
  }
}

resource "aws_s3_bucket_policy" "backups" {
  bucket = aws_s3_bucket.backups.id
  policy = data.aws_iam_policy_document.backups.json

  depends_on = [aws_s3_bucket_public_access_block.backups]
}

output "bucket_name" {
  description = "Nombre del bucket de backups"
  value       = aws_s3_bucket.backups.id
}

output "bucket_arn" {
  description = "ARN del bucket de backups"
  value       = aws_s3_bucket.backups.arn
}
