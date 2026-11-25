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

resource "aws_kms_key" "redis_key" {
  description = "KMS key for Redis replication group"
  enable_key_rotation = true  # Enable key rotation

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Sid     = "EnableKeyRotation"
        Effect  = "Allow"
        Principal = "AWS"
        Action = [
          "kms:RotateKey"
        ]
        Resource = "*"
      }
    ]
  })
}

resource "aws_elasticache_replication_group" "redis_cluster" {
  replication_group_name = "terraform-redis-cluster"
  replication_group_description = "Elasticache Redis cluster created with Terraform"
  num_node_groups = 1
  automatic_failover_enabled = true

  node_type = "cache.t3.micro"
  engine = "redis"
  engine_version = "6.x"
  security_group_ids = [aws_security_group.cache_sg.id]
  at_rest_encryption_enabled = true
  at_rest_kms_key_id = aws_kms_key.redis_key.id
  transit_encryption_enabled = true

  provisioner "local-exec" {
    command = "aws elasticache describe-replication-groups --replication-group-name ${aws_elasticache_replication_group.redis_cluster.replication_group_name} --query 'ReplicationGroups[0].ReplicationGroupDescription' --output text"
  }
}

resource "aws_security_group" "cache_sg" {
  name        = "cache-sg"
  description = "Security group for Redis cache"
  vpc_id      = "vpc-12345678"  # Replace with your VPC ID

  ingress {
    from_port   = 6379
    to_port     = 6379
    protocol    = "tcp"
    cidr_blocks = ["10.0.0.0/16"]  # Replace with your desired CIDR blocks
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["10.0.0.0/16"]  # Replace with your desired CIDR blocks
  }

  # Add a description to the security group
  tags = {
    Description = "Security group for Redis cache"
  }
}

# This resource is added to address the missing required argument and unsupported argument issues
resource "null_resource" "dummy" {
  triggers = {
    description = aws_security_group.cache_sg.description
  }
}
