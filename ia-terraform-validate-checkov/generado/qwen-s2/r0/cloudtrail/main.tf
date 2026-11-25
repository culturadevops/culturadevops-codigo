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
  s3_bucket_name = "example-bucket-for-cloudtrail"
  is_multi_region Trail = true
}

resource "aws_s3_bucket" "example" {
  bucket = "example-bucket-for-cloudtrail"
}
