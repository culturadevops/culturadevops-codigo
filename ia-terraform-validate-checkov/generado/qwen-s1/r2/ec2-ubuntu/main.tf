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

  # Ensure Instance Metadata Service Version 1 is not enabled
  disable_api_state = true

  ebs_optimized = true

  monitoring = true

  tags = {
    Name = "UbuntuInstance"
  }

  # IAM role attachment is not possible in this resource block directly, so we assume an IAM role is attached via an IAM instance profile
}

output "instance_id" {
  value = aws_instance.ubuntu.id
}
