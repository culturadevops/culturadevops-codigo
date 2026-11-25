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
  name = "docker-images-repo"
}

resource "aws_ecr_image_tag_mutability" "docker_images" {
  repository_name = aws_ecr_repository.docker_images.name
  image_tag_mutability = "MUTABLE"
}

resource "aws_kms_key" "ecr" {
  description = "KMS key for ECR"
  deletion_window_in_days = 30
}

resource "aws_ecr_repository" "docker_images" {
  name = "docker-images-repo"

  encryption_configuration {
    encryption_type = "KMS"
    kms_key_id      = aws_kms_key.ecr.arn
  }

  image_scanning_configuration {
    scan_on_push = true
  }
}
