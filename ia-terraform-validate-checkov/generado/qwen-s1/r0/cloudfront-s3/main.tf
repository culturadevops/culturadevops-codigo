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
}

resource "aws_acm_certificate" "example_certificate" {
  domain_name = "example.com"
  validation_method = "email"
  subject_alternative_names = ["www.example.com"]
}
