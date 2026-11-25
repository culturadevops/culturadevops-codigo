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

variable "bucket_name" {
  description = "Nombre del bucket de S3 al que el CI sube archivos"
  type        = string
}

variable "ci_user_name" {
  description = "Nombre del usuario de IAM para el CI"
  type        = string
  default     = "ci-s3-uploader"
}

variable "upload_prefix" {
  description = "Prefijo (carpeta) dentro del bucket donde el CI puede escribir. Vacío = todo el bucket"
  type        = string
  default     = ""
}

data "aws_s3_bucket" "target" {
  bucket = var.bucket_name
}

resource "aws_iam_user" "ci" {
  name = var.ci_user_name
  path = "/ci/"

  tags = {
    Purpose   = "CI uploads to S3"
    ManagedBy = "terraform"
  }
}

data "aws_iam_policy_document" "ci_s3_upload" {
  statement {
    sid     = "ListBucket"
    effect  = "Allow"
    actions = ["s3:ListBucket", "s3:GetBucketLocation"]

    resources = [data.aws_s3_bucket.target.arn]

    dynamic "condition" {
      for_each = var.upload_prefix == "" ? [] : [1]
      content {
        test     = "StringLike"
        variable = "s3:prefix"
        values   = ["${var.upload_prefix}*"]
      }
    }
  }

  statement {
    sid    = "UploadObjects"
    effect = "Allow"
    actions = [
      "s3:PutObject",
      "s3:GetObject",
      "s3:AbortMultipartUpload",
      "s3:ListMultipartUploadParts",
    ]

    resources = ["${data.aws_s3_bucket.target.arn}/${var.upload_prefix}*"]
  }

  statement {
    sid       = "DenyInsecureTransport"
    effect    = "Deny"
    actions   = ["s3:*"]
    resources = [
      data.aws_s3_bucket.target.arn,
      "${data.aws_s3_bucket.target.arn}/*",
    ]

    condition {
      test     = "Bool"
      variable = "aws:SecureTransport"
      values   = ["false"]
    }
  }
}

resource "aws_iam_policy" "ci_s3_upload" {
  name        = "${var.ci_user_name}-s3-upload"
  path        = "/ci/"
  description = "Permite al usuario de CI subir archivos a s3://${var.bucket_name}/${var.upload_prefix}"
  policy      = data.aws_iam_policy_document.ci_s3_upload.json
}

resource "aws_iam_user_policy_attachment" "ci_s3_upload" {
  user       = aws_iam_user.ci.name
  policy_arn = aws_iam_policy.ci_s3_upload.arn
}

# Nota: el secret queda guardado en el state de Terraform. Protege el backend
# (S3 cifrado + acceso restringido) o crea la access key fuera de Terraform.
# Si tu CI soporta OIDC (GitHub Actions, GitLab), es preferible un rol IAM
# asumible vía OIDC en lugar de un usuario con claves de larga duración.
resource "aws_iam_access_key" "ci" {
  user = aws_iam_user.ci.name
}

output "ci_user_arn" {
  value = aws_iam_user.ci.arn
}

output "ci_access_key_id" {
  value = aws_iam_access_key.ci.id
}

output "ci_secret_access_key" {
  value     = aws_iam_access_key.ci.secret
  sensitive = true
}
