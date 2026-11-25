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

resource "aws_cloudtrail" "example" {
  name     = "example-cloudtrail"
  s3_bucket_name = "example-bucket"
  is_multi_region_trail = true
  enable_logging = true
}
