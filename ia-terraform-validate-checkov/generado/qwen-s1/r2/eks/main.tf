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
    namespace               = "default"
    public_access_cidrs     = []
    endpoint_private_access = true
    endpoint_public_access  = false
  }

  logging {
    cluster_log_enabled = true
    node_log_enabled    = true
    pod_log_enabled     = true
  }

  enable_aws_logs = true

  tags = {
    Name = "example-cluster"
  }
}

resource "aws_iam_role" "example" {
  name = "example-role"

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

resource "aws_iam_role_policy_attachment" "example" {
  policy_arn = "arn:aws:iam::aws:policy/AmazonEKSClusterPolicy"
  role       = aws_iam_role.example.name
}

resource "aws_eks_node_group" "example" {
  cluster_name = aws_eks_cluster.example.name
  node_group_name = "example-node-group"
  node_role_arn = aws_iam_role.example.arn

  subnet_ids = [aws_subnet.example.id]

  scaling_config {
    desired_size = 2
    min_size     = 2
    max_size     = 2
  }
}

resource "aws_subnet" "example" {
  vpc_id            = aws_vpc.example.id
  cidr_block        = "10.0.1.0/24"
  availability_zone = "us-east-1a"

  tags = {
    Name = "example-subnet"
  }
}

resource "aws_vpc" "example" {
  cidr_block = "10.0.0.0/16"

  default_security_group {
    ingress {
      from_port   = -1
      to_port     = -1
      protocol    = "-1"
      cidr_blocks = ["0.0.0.0/0"]
    }
    egress {
      from_port   = -1
      to_port     = -1
      protocol    = "-1"
      cidr_blocks = ["0.0.0.0/0"]
    }
  }

  tags = {
    Name = "example-vpc"
  }
}

resource "aws_flow_log" "example" {
  vpc_id            = aws_vpc.example.id
  traffic_type      = "ALL"
  deliver_logs_to_cloudwatch_logs = true
}
