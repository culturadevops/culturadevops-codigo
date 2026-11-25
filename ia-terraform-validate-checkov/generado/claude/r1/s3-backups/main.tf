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

# Región secundaria para la réplica de backups
provider "aws" {
  alias  = "replica"
  region = var.replica_region

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

variable "replica_region" {
  description = "Región de destino para la replicación de backups"
  type        = string
  default     = "us-west-2"
}

variable "replica_bucket_name" {
  description = "Nombre globalmente único del bucket réplica de backups"
  type        = string
  default     = "mi-app-backups-us-west-2"
}

variable "logs_bucket_name" {
  description = "Nombre globalmente único del bucket de logs de acceso"
  type        = string
  default     = "mi-app-backups-logs-us-east-1"
}

variable "access_logs_retention_days" {
  description = "Días que se conservan los logs de acceso al bucket de backups"
  type        = number
  default     = 365
}

data "aws_caller_identity" "current" {}

# ---------------------------------------------------------------------------
# KMS
# ---------------------------------------------------------------------------

# Clave KMS para cifrar los backups y el topic SNS de notificaciones
resource "aws_kms_key" "backups" {
  description             = "Cifrado del bucket de backups y sus notificaciones"
  enable_key_rotation     = true
  deletion_window_in_days = 30

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Sid       = "EnableRootAccountPermissions"
        Effect    = "Allow"
        Principal = { AWS = "arn:aws:iam::${data.aws_caller_identity.current.account_id}:root" }
        Action    = "kms:*"
        Resource  = "*"
      },
      {
        Sid       = "AllowS3EventNotificationsToEncryptedSNS"
        Effect    = "Allow"
        Principal = { Service = "s3.amazonaws.com" }
        Action = [
          "kms:GenerateDataKey*",
          "kms:Decrypt",
        ]
        Resource = "*"
        Condition = {
          StringEquals = {
            "aws:SourceAccount" = data.aws_caller_identity.current.account_id
          }
        }
      },
    ]
  })
}

resource "aws_kms_alias" "backups" {
  name          = "alias/app-backups"
  target_key_id = aws_kms_key.backups.key_id
}

# Clave KMS en la región réplica
resource "aws_kms_key" "replica" {
  provider = aws.replica

  description             = "Cifrado del bucket réplica de backups"
  enable_key_rotation     = true
  deletion_window_in_days = 30

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Sid       = "EnableRootAccountPermissions"
        Effect    = "Allow"
        Principal = { AWS = "arn:aws:iam::${data.aws_caller_identity.current.account_id}:root" }
        Action    = "kms:*"
        Resource  = "*"
      },
    ]
  })
}

resource "aws_kms_alias" "replica" {
  provider = aws.replica

  name          = "alias/app-backups-replica"
  target_key_id = aws_kms_key.replica.key_id
}

# ---------------------------------------------------------------------------
# Bucket de logs de acceso
# ---------------------------------------------------------------------------

# Bucket destino de los logs de acceso del bucket de backups
resource "aws_s3_bucket" "logs" {
  #checkov:skip=CKV_AWS_18:Es el bucket destino de los logs de acceso; registrarse a sí mismo genera un bucle de logs
  #checkov:skip=CKV_AWS_144:Los logs de acceso no requieren replicación entre regiones
  #checkov:skip=CKV2_AWS_62:No se requieren notificaciones de eventos para los logs de acceso
  #checkov:skip=CKV_AWS_145:El logging de acceso de S3 solo admite SSE-S3 en el bucket destino, no SSE-KMS
  bucket = var.logs_bucket_name

  lifecycle {
    prevent_destroy = true
  }
}

resource "aws_s3_bucket_ownership_controls" "logs" {
  bucket = aws_s3_bucket.logs.id

  rule {
    object_ownership = "BucketOwnerEnforced"
  }
}

resource "aws_s3_bucket_public_access_block" "logs" {
  bucket = aws_s3_bucket.logs.id

  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

resource "aws_s3_bucket_versioning" "logs" {
  bucket = aws_s3_bucket.logs.id

  versioning_configuration {
    status = "Enabled"
  }
}

# SSE-S3: único cifrado soportado para destinos de logs de acceso
resource "aws_s3_bucket_server_side_encryption_configuration" "logs" {
  bucket = aws_s3_bucket.logs.id

  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
  }
}

resource "aws_s3_bucket_lifecycle_configuration" "logs" {
  bucket = aws_s3_bucket.logs.id

  rule {
    id     = "logs-retention"
    status = "Enabled"

    filter {}

    transition {
      days          = 30
      storage_class = "STANDARD_IA"
    }

    expiration {
      days = var.access_logs_retention_days
    }

    noncurrent_version_expiration {
      noncurrent_days = 30
    }

    abort_incomplete_multipart_upload {
      days_after_initiation = 7
    }
  }

  depends_on = [aws_s3_bucket_versioning.logs]
}

# Política: solo HTTPS y permitir escritura al servicio de logging de S3
data "aws_iam_policy_document" "logs" {
  statement {
    sid     = "DenyInsecureTransport"
    effect  = "Deny"
    actions = ["s3:*"]

    principals {
      type        = "*"
      identifiers = ["*"]
    }

    resources = [
      aws_s3_bucket.logs.arn,
      "${aws_s3_bucket.logs.arn}/*",
    ]

    condition {
      test     = "Bool"
      variable = "aws:SecureTransport"
      values   = ["false"]
    }
  }

  statement {
    sid     = "AllowS3ServerAccessLogs"
    effect  = "Allow"
    actions = ["s3:PutObject"]

    principals {
      type        = "Service"
      identifiers = ["logging.s3.amazonaws.com"]
    }

    resources = ["${aws_s3_bucket.logs.arn}/s3-access/*"]

    condition {
      test     = "ArnLike"
      variable = "aws:SourceArn"
      values   = [aws_s3_bucket.backups.arn]
    }

    condition {
      test     = "StringEquals"
      variable = "aws:SourceAccount"
      values   = [data.aws_caller_identity.current.account_id]
    }
  }
}

resource "aws_s3_bucket_policy" "logs" {
  bucket = aws_s3_bucket.logs.id
  policy = data.aws_iam_policy_document.logs.json

  depends_on = [aws_s3_bucket_public_access_block.logs]
}

# ---------------------------------------------------------------------------
# Bucket réplica (otra región)
# ---------------------------------------------------------------------------

resource "aws_s3_bucket" "replica" {
  #checkov:skip=CKV_AWS_144:Es el bucket destino de la replicación; replicarlo de nuevo no aporta resiliencia adicional
  #checkov:skip=CKV_AWS_18:El bucket de logs debe estar en la misma región; el acceso se audita vía CloudTrail
  #checkov:skip=CKV2_AWS_62:Las notificaciones de eventos se gestionan en el bucket origen
  provider = aws.replica

  bucket = var.replica_bucket_name

  lifecycle {
    prevent_destroy = true
  }
}

resource "aws_s3_bucket_ownership_controls" "replica" {
  provider = aws.replica

  bucket = aws_s3_bucket.replica.id

  rule {
    object_ownership = "BucketOwnerEnforced"
  }
}

resource "aws_s3_bucket_public_access_block" "replica" {
  provider = aws.replica

  bucket = aws_s3_bucket.replica.id

  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

resource "aws_s3_bucket_versioning" "replica" {
  provider = aws.replica

  bucket = aws_s3_bucket.replica.id

  versioning_configuration {
    status = "Enabled"
  }
}

resource "aws_s3_bucket_server_side_encryption_configuration" "replica" {
  provider = aws.replica

  bucket = aws_s3_bucket.replica.id

  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm     = "aws:kms"
      kms_master_key_id = aws_kms_key.replica.arn
    }
    bucket_key_enabled = true
  }
}

resource "aws_s3_bucket_lifecycle_configuration" "replica" {
  provider = aws.replica

  bucket = aws_s3_bucket.replica.id

  rule {
    id     = "replica-tiering"
    status = "Enabled"

    filter {}

    transition {
      days          = 30
      storage_class = "GLACIER"
    }

    noncurrent_version_expiration {
      noncurrent_days = var.backup_retention_days
    }

    abort_incomplete_multipart_upload {
      days_after_initiation = 7
    }
  }

  depends_on = [aws_s3_bucket_versioning.replica]
}

data "aws_iam_policy_document" "replica" {
  statement {
    sid     = "DenyInsecureTransport"
    effect  = "Deny"
    actions = ["s3:*"]

    principals {
      type        = "*"
      identifiers = ["*"]
    }

    resources = [
      aws_s3_bucket.replica.arn,
      "${aws_s3_bucket.replica.arn}/*",
    ]

    condition {
      test     = "Bool"
      variable = "aws:SecureTransport"
      values   = ["false"]
    }
  }
}

resource "aws_s3_bucket_policy" "replica" {
  provider = aws.replica

  bucket = aws_s3_bucket.replica.id
  policy = data.aws_iam_policy_document.replica.json

  depends_on = [aws_s3_bucket_public_access_block.replica]
}

# ---------------------------------------------------------------------------
# Bucket de backups
# ---------------------------------------------------------------------------

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

# Cifrado en reposo por defecto con KMS
resource "aws_s3_bucket_server_side_encryption_configuration" "backups" {
  bucket = aws_s3_bucket.backups.id

  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm     = "aws:kms"
      kms_master_key_id = aws_kms_key.backups.arn
    }
    bucket_key_enabled = true
  }
}

# Logs de acceso al bucket de backups
resource "aws_s3_bucket_logging" "backups" {
  bucket = aws_s3_bucket.backups.id

  target_bucket = aws_s3_bucket.logs.id
  target_prefix = "s3-access/${var.bucket_name}/"

  depends_on = [aws_s3_bucket_policy.logs]
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

# ---------------------------------------------------------------------------
# Replicación entre regiones
# ---------------------------------------------------------------------------

resource "aws_iam_role" "replication" {
  name = "app-backups-s3-replication"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect    = "Allow"
        Principal = { Service = "s3.amazonaws.com" }
        Action    = "sts:AssumeRole"
      },
    ]
  })
}

resource "aws_iam_role_policy" "replication" {
  name = "app-backups-s3-replication"
  role = aws_iam_role.replication.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Sid    = "ReadSourceBucketConfig"
        Effect = "Allow"
        Action = [
          "s3:GetReplicationConfiguration",
          "s3:ListBucket",
        ]
        Resource = [aws_s3_bucket.backups.arn]
      },
      {
        Sid    = "ReadSourceObjects"
        Effect = "Allow"
        Action = [
          "s3:GetObjectVersionForReplication",
          "s3:GetObjectVersionAcl",
          "s3:GetObjectVersionTagging",
        ]
        Resource = ["${aws_s3_bucket.backups.arn}/*"]
      },
      {
        Sid    = "WriteReplicaObjects"
        Effect = "Allow"
        Action = [
          "s3:ReplicateObject",
          "s3:ReplicateDelete",
          "s3:ReplicateTags",
        ]
        Resource = ["${aws_s3_bucket.replica.arn}/*"]
      },
      {
        Sid      = "DecryptSourceObjects"
        Effect   = "Allow"
        Action   = ["kms:Decrypt"]
        Resource = [aws_kms_key.backups.arn]
        Condition = {
          StringLike = {
            "kms:ViaService"                   = "s3.us-east-1.amazonaws.com"
            "kms:EncryptionContext:aws:s3:arn" = ["${aws_s3_bucket.backups.arn}/*"]
          }
        }
      },
      {
        Sid    = "EncryptReplicaObjects"
        Effect = "Allow"
        Action = [
          "kms:Encrypt",
          "kms:GenerateDataKey",
        ]
        Resource = [aws_kms_key.replica.arn]
        Condition = {
          StringLike = {
            "kms:ViaService"                   = "s3.${var.replica_region}.amazonaws.com"
            "kms:EncryptionContext:aws:s3:arn" = ["${aws_s3_bucket.replica.arn}/*"]
          }
        }
      },
    ]
  })
}

resource "aws_s3_bucket_replication_configuration" "backups" {
  bucket = aws_s3_bucket.backups.id
  role   = aws_iam_role.replication.arn

  rule {
    id     = "backups-cross-region"
    status = "Enabled"

    filter {}

    delete_marker_replication {
      status = "Enabled"
    }

    source_selection_criteria {
      sse_kms_encrypted_objects {
        status = "Enabled"
      }
    }

    destination {
      bucket        = aws_s3_bucket.replica.arn
      storage_class = "STANDARD"

      encryption_configuration {
        replica_kms_key_id = aws_kms_key.replica.arn
      }
    }
  }

  depends_on = [
    aws_s3_bucket_versioning.backups,
    aws_s3_bucket_versioning.replica,
  ]
}

# ---------------------------------------------------------------------------
# Notificaciones de eventos
# ---------------------------------------------------------------------------

resource "aws_sns_topic" "backups_events" {
  name              = "app-backups-events"
  kms_master_key_id = aws_kms_key.backups.arn
}

data "aws_iam_policy_document" "backups_events" {
  statement {
    sid     = "AllowS3Publish"
    effect  = "Allow"
    actions = ["sns:Publish"]

    principals {
      type        = "Service"
      identifiers = ["s3.amazonaws.com"]
    }

    resources = [aws_sns_topic.backups_events.arn]

    condition {
      test     = "ArnLike"
      variable = "aws:SourceArn"
      values   = [aws_s3_bucket.backups.arn]
    }

    condition {
      test     = "StringEquals"
      variable = "aws:SourceAccount"
      values   = [data.aws_caller_identity.current.account_id]
    }
  }
}

resource "aws_sns_topic_policy" "backups_events" {
  arn    = aws_sns_topic.backups_events.arn
  policy = data.aws_iam_policy_document.backups_events.json
}

# Notifica creación y borrado de backups
resource "aws_s3_bucket_notification" "backups" {
  bucket = aws_s3_bucket.backups.id

  topic {
    topic_arn = aws_sns_topic.backups_events.arn
    events = [
      "s3:ObjectCreated:*",
      "s3:ObjectRemoved:*",
    ]
  }

  depends_on = [aws_sns_topic_policy.backups_events]
}

output "bucket_name" {
  description = "Nombre del bucket de backups"
  value       = aws_s3_bucket.backups.id
}

output "bucket_arn" {
  description = "ARN del bucket de backups"
  value       = aws_s3_bucket.backups.arn
}

output "replica_bucket_arn" {
  description = "ARN del bucket réplica de backups"
  value       = aws_s3_bucket.replica.arn
}

output "logs_bucket_name" {
  description = "Nombre del bucket de logs de acceso"
  value       = aws_s3_bucket.logs.id
}

output "events_topic_arn" {
  description = "ARN del topic SNS con los eventos del bucket de backups"
  value       = aws_sns_topic.backups_events.arn
}
