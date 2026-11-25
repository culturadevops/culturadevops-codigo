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

resource "aws_elasticache_cluster" "redis_cluster" {
  cluster_id = "my-redis-cluster"
  engine     = "redis"
  engine_version = "6.x"
  num_cache_nodes = 1
  port        = 6379
  replication_group_id = null
  parameter_group_name = "default.redis6.x"
  security_group_ids = [aws_security_group.redis_sg.id]
  preferred_availability_zone = "us-east-1a"

  tags = {
    Name = "my-redis-cluster"
  }
}

resource "aws_security_group" "redis_sg" {
  name        = "redis-sg"
  description = "Security group for Redis access"

  ingress {
    from_port   = 6379
    to_port     = 6379
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    Name = "redis-sg"
  }
}
