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

resource "aws_ecr_repository" "docker_images" {
  name               = "docker-images-repo"
  image_tag_mutability = "MUTABLE"  # Make sure image tags are immutable
  encryption_configuration {
    encryption_type = "KMS"
    kms_key_id      = "alias/aws/ecr"
  }
  image_scanning_configuration {
    scan_on_push = true
  }
}
