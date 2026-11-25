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

resource "aws_kms_key" "efs_key" {
  description = "KMS key for EFS encryption"
}

resource "aws_efs_file_system" "shared_efs" {
  creation_token = "shared-efs"
  encrypted      = true
  kms_key_id     = aws_kms_key.efs_key.id
}

resource "aws_efs_mount_target" "shared_efs" {
  count = 1
  file_system_id = aws_efs_file_system.shared_efs.id
  subnet_id      = "subnet-12345678"  # Reemplaza con tu ID de subred
}

resource "aws_iam_policy" "efs_policy" {
  name        = "efs_policy"
  description = "IAM policy for EFS access"

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = [
          "elasticfilesystem:DescribeFileSystems",
          "elasticfilesystem:DescribeMountTargets",
          "elasticfilesystem:CreateMountTarget",
          "elasticfilesystem:DeleteMountTarget"
        ]
        Effect   = "Allow"
        Resource = aws_efs_file_system.shared_efs.arn
      }
    ]
  })
}

resource "aws_iam_role" "efs_role" {
  name = "efs_role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "ec2.amazonaws.com"
        }
      }
    ]
  })
}

resource "aws_iam_role_policy_attachment" "efs_attach" {
  policy_arn = aws_iam_policy.efs_policy.arn
  role       = aws_iam_role.efs_role.name
}

resource "aws_instance" "example" {
  count = 2

  ami           = "ami-0c55b159cbfafe1f0"  # Reemplaza con el ID de AMI que uses
  instance_type = "t2.micro"
  subnet_id     = "subnet-12345678"        # Reemplaza con tu ID de subred

  tags = {
    Name = "example-instance-${count.index}"
  }

  vpc_security_group_ids = [aws_security_group.efs_sg.id]

  root_block_device {
    volume_type = "gp2"
    volume_size = 8
  }

  ebs_optimized = true
  disable_api Termination = true
  enable_api Termination = false
}

resource "aws_security_group" "efs_sg" {
  name        = "efs-sg"
  description = "Security group for EFS access"

  ingress {
    from_port   = 2049
    to_port     = 2049
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }
}
