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

  connect {
    type        = "ssh"
    user        = "ubuntu"
    private_key = file("~/.ssh/id_rsa")
  }
}
