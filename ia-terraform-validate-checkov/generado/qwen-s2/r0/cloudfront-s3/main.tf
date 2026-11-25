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

resource "aws_s3_bucket" "example" {
  bucket = "example-bucket"
}

resource "aws_cloudfront_distribution" "example" {
  origin {
    domain_name = aws_s3_bucket.example.bucket
    origin_id   = "S3BucketOrigin"

    custom_headers {
      name  = "X-Custom-Header"
      value = "MyCustomValue"
    }

    origin_path = "/path/to/object"
  }

  default_root_object = "index.html"

  default_cache_behavior {
    allowed_methods              = ["GET", "HEAD", "OPTIONS"]
    cached_methods               = ["GET", "HEAD"]
    target_origin_id             = "S3BucketOrigin"
    viewer_protocol_policy       = "redirect-to-https"
    min_ttl                      = 0
    default_ttl                  = 3600
    max_ttl                      = 86400
    forwarded_values {
      query_string = false
      cookies {
        forward = "none"
      }
    }
  }

  enabled = true

  restrictions {
    geo_restriction {
      restriction_type = "none"
    }
  }

  price_class = "PriceClass_100"

  viewer_certificate {
    acm_certificate_arn = aws_acm_certificate.example.arn
    ssl_support_method  = "sni-only"
  }

  alias_icp_record_id = "ICP_RECORD_ID"
  caller_reference    = "unique-ref"
}
