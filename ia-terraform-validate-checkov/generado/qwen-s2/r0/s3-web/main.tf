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

resource "aws_s3_bucket" "static_website" {
  bucket = "my-static-website-bucket"
}

resource "aws_s3_bucket_website" "static_website" {
  bucket = aws_s3_bucket.static_website.bucket

  index_document {
    suffix = "index.html"
  }
}

resource "aws_s3_object" "index_html" {
  bucket = aws_s3_bucket.static_website.bucket
  key    = "index.html"
  content = "<h1>Welcome to My Static Website!</h1>"
}
