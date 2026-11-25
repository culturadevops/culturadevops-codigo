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

resource "aws_s3_bucket" "example_bucket" {
  bucket = "example-bucket"
  server_side_encryption_configuration {
    rule {
      apply_server_side_encryption_by_default {
        sse_algorithm = "AES256"
      }
    }
  }
  versioning {
    enabled = true
  }
  public_access_block {
    block_public_acls       = true
    block_public_policy     = true
    ignore_public_acls      = true
    restrict_public_buckets = true
  }
  lifecycle {
    enabled = true
    rule {
      id      = "Enable-Access-Logging"
      status  = "Enabled"
      noncurrent_version_transition {
        days         = 30
        storage_class = "GLACIER"
      }
      noncurrent_version_expiration {
        days = 30
      }
    }
    rule {
      id      = "Enable-Logging"
      status  = "Enabled"
      noncurrent_version_transition {
        days         = 30
        storage_class = "GLACIER"
      }
      noncurrent_version_expiration {
        days = 30
      }
    }
  }
}

resource "aws_cloudfront_distribution" "example_distribution" {
  origin {
    domain_name = aws_s3_bucket.example_bucket.bucket
    origin_id   = "S3BucketOrigin"
  }

  default_root_object = "index.html"

  default_cache_behavior {
    allowed_methods        = ["GET", "HEAD", "OPTIONS"]
    cached_methods         = ["GET", "HEAD", "OPTIONS"]
    target_origin_id       = "S3BucketOrigin"
    forwarded_values       = {
      query_string = false
    }
    viewer_protocol_policy = "redirect-to-https"
    min_ttl         = 0
    default_ttl     = 3600
    max_ttl         = 86400
  }

  commented_cache_behavior = []

  enabled             = true
  is_ipv6_enabled     = true
  default_root_object = "index.html"

  restrictions {
    geo_restriction {
      restriction_type = "none"
    }
  }

  viewer_certificate {
    acm_certificate_arn = aws_acm_certificate.example_certificate.arn
    ssl_support_method  = "sni-only"
  }

  logging_config {
    bucket = aws_s3_bucket.example_bucket.bucket
    prefix = "cloudfront-logs/"
  }

  waf_failover_config {
    cloudfront_failover_behavior = "forward"
    waf_failover_behavior        = "forward"
  }

  waf_reference_mutation {
    field_to_parse = "uri_path"
    mutate_field   = "uri_path"
  }

  wafv2_web_acl_id = aws_wafv2_web_acl.example_web_acl.id
}

resource "aws_acm_certificate" "example_certificate" {
  domain_name = "example.com"
  validation_method = "email"
  subject_alternative_names = ["www.example.com"]
}

resource "aws_wafv2_web_acl" "example_web_acl" {
  name            = "example-web-acl"
  scope           = "Regional"
  default_action {
    allow = true
  }
  rules {
    statement {
      geo_match_statement {
        country_codes = ["US", "CA"]
      }
      action {
        allow = true
      }
    }
  }
}

resource "aws_s3_bucket_object" "example_object" {
  bucket = aws_s3_bucket.example_bucket.bucket
  key    = "index.html"
  content = "Welcome to the example bucket."
}
