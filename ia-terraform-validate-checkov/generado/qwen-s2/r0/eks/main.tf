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

resource "aws_eks_cluster" "example" {
  name     = "example-cluster"
  role_arn = aws_iam_role.example.arn

  resources_vpc_config {
    namespace              = "default"
    public_access_cidrs    = ["0.0.0.0/0"]
    endpoint_private_access = false
    endpoint_public_access = true
  }

  version = "1.24"
}

resource "aws_iam_role" "example" {
  name = "example-eks-cluster"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "eks.amazonaws.com"
        }
      }
    ]
  })
}

resource "aws_eks_node_group" "example" {
  name     = "example-node-group"
  cluster_name = aws_eks_cluster.example.name
  node_group_name = "example-node-group"
  subnet_ids = [aws_subnet.example.id]
  scaling_config {
    desired_size = 2
    max_size     = 3
    min_size     = 1
  }
  instance_types = ["t2.micro"]
  ami_type       = "AL2_x86_64"

  disk_size = 20

  labels = {
    kubernetes.io/role/node = "true"
    kubernetes.io/instance-type = "t2.micro"
  }

  tags = {
    Name = "example-node-group"
  }
}

resource "aws_subnet" "example" {
  vpc_id            = aws_vpc.example.id
  cidr_block        = "10.0.1.0/24"
  availability_zone = "us-east-1a"
  map_public_ip_on_launch = false
}

resource "aws_vpc" "example" {
  cidr_block = "10.0.0.0/16"

  tags = {
    Name = "example-vpc"
  }
}
