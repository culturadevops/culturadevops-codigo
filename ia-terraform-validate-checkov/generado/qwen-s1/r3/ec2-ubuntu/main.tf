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

resource "aws_instance" "ubuntu" {
  ami           = "ami-0c55b159cbfafe1f0"  # Example AMI ID, use the appropriate one for the latest Ubuntu version
  instance_type = "t3.micro"

  user_data = <<-EOF
              #!/bin/bash
              apt-get update
              apt-get install -y openssh-server
              EOF

  metadata_options {
    http_api_enabled = false
    http_endpoint_enabled = true
  }

  ebs_optimized = true

  monitoring = true

  tags = {
    Name = "UbuntuInstance"
  }

  # Assuming an IAM role is attached via an IAM instance profile
  # If you need to specify the IAM role directly, you can use the `iam_instance_profile` argument
  # iam_instance_profile = "your_iam_profile_name"
}

output "instance_id" {
  value = aws_instance.ubuntu.id
}
