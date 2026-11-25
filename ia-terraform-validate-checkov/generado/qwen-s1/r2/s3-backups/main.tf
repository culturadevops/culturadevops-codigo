terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 4.0"
    }
  }
}

provider "aws" {
  region = "us-east-1"
}

resource "aws_s3_bucket" "backup_bucket" {
  bucket = "my-backup-bucket"
  acl    = "private"

  # Enable public access block
  public_access_block {
    block_public_acls = true
    block_public_policy = true
    ignore_public_acls = true
    restrict_public_buckets = true
  }

  # Enable server-side encryption with KMS
  server_side_encryption_configuration {
    rule {
      apply_server_side_encryption_by_default {
        sse_algorithm = "aws:kms"
      }
    }
  }

  # Enable event notifications
  event_notification {
    event        = "s3:ObjectCreated:*"
    bucket       = aws_s3_bucket.backup_bucket.id
    topic_arn    = aws_sns_topic.notification_topic.arn
  }

  # Enable versioning
  versioning {
    enabled = true
  }

  # Enable access logging
  logging {
    target_bucket = aws_s3_bucket.access_logs_bucket.id
    target_prefix = "logs/"
  }

  # Enable lifecycle configuration
  lifecycle_rule {
    id      = "versioning"
    enabled = true

    transition {
      days      = 30
      storage_class = "STANDARD_IA"
    }

    noncurrent_version_transition {
      days      = 30
      storage_class = "GLACIER"
    }
  }

  # Enable cross-region replication
  cross_region_replication {
    destination {
      bucket_arn = aws_s3_bucket.replication_bucket.arn
    }
  }
}

resource "aws_sns_topic" "notification_topic" {
  name = "backup-notification-topic"
}

resource "aws_s3_bucket" "access_logs_bucket" {
  bucket = "my-access-logs-bucket"
  acl    = "private"

  # Enable server-side encryption with KMS
  server_side_encryption_configuration {
    rule {
      apply_server_side_encryption_by_default {
        sse_algorithm = "aws:kms"
      }
    }
  }

  # Enable event notifications
  event_notification {
    event        = "s3:ObjectCreated:*"
    bucket       = aws_s3_bucket.access_logs_bucket.id
    topic_arn    = aws_sns_topic.notification_topic.arn
  }

  # Enable versioning
  versioning {
    enabled = true
  }

  # Enable access logging
  logging {
    target_bucket = aws_s3_bucket.backup_bucket.id
    target_prefix = "logs/"
  }

  # Enable lifecycle configuration
  lifecycle_rule {
    id      = "versioning"
    enabled = true

    transition {
      days      = 30
      storage_class = "STANDARD_IA"
    }

    noncurrent_version_transition {
      days      = 30
      storage_class = "GLACIER"
    }
  }

  # Enable cross-region replication
  cross_region_replication {
    destination {
      bucket_arn = aws_s3_bucket.replication_bucket.arn
    }
  }
}

resource "aws_s3_bucket" "replication_bucket" {
  bucket = "my-replication-bucket"
  acl    = "private"

  # Enable server-side encryption with KMS
  server_side_encryption_configuration {
    rule {
      apply_server_side_encryption_by_default {
        sse_algorithm = "aws:kms"
      }
    }
  }

  # Enable event notifications
  event_notification {
    event        = "s3:ObjectCreated:*"
    bucket       = aws_s3_bucket.replication_bucket.id
    topic_arn    = aws_sns_topic.notification_topic.arn
  }

  # Enable versioning
  versioning {
    enabled = true
  }

  # Enable access logging
  logging {
    target_bucket = aws_s3_bucket.backup_bucket.id
    target_prefix = "logs/"
  }

  # Enable lifecycle configuration
  lifecycle_rule {
    id      = "versioning"
    enabled = true

    transition {
      days      = 30
      storage_class = "STANDARD_IA"
    }

    noncurrent_version_transition {
      days      = 30
      storage_class = "GLACIER"
    }
  }

  # Enable cross-region replication
  cross_region_replication {
    destination {
      bucket_arn = aws_s3_bucket.backup_bucket.arn
    }
  }
}
