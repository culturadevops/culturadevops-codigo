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

resource "aws_instance" "web" {
  count = 2

  ami           = "ami-0c55b159cbfafe1f0" # Use the latest Amazon Linux 2 AMI
  instance_type = "t2.micro"

  tags = {
    Name = "web-instance-${count.index}"
  }
}

resource "aws_alb" "example" {
  name               = "example-alb"
  internal           = false
  load_balancer_type = "application"
  security_groups    = [aws_security_group.example.id]
  subnets            = [for subnet in aws_subnet.example : subnet.id]

  listener {
    port     = 80
    protocol = "HTTP"

    default_action {
      type = "forward"
      value = aws_alb_target_group.example.id
    }
  }
}

resource "aws_alb_target_group" "example" {
  name     = "example-tg"
  port     = 80
  protocol = "HTTP"
  vpc_id   = aws_vpc.example.id
}

resource "aws_security_group" "example" {
  name        = "example-sg"
  description = "Allow HTTP traffic"
  vpc_id      = aws_vpc.example.id

  ingress {
    from_port   = 80
    to_port     = 80
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }
}

resource "aws_vpc" "example" {
  cidr_block = "10.0.0.0/16"

  tags = {
    Name = "example-vpc"
  }
}

resource "aws_subnet" "example" {
  count           = 2
  cidr_block      = "10.0.${count.index}.0/24"
  vpc_id          = aws_vpc.example.id
  availability_zone = "us-east-1a"

  tags = {
    Name = "example-subnet-${count.index}"
  }
}

resource "aws_route_table" "example" {
  vpc_id = aws_vpc.example.id

  route {
    cidr_block = "0.0.0.0/0"
    gateway_id = aws_internet_gateway.example.id
  }

  tags = {
    Name = "example-rt"
  }
}

resource "aws_route_table_association" "example" {
  count           = 2
  subnet_id       = element(aws_subnet.example.*.id, count.index)
  route_table_id  = aws_route_table.example.id
}

resource "aws_internet_gateway" "example" {
  vpc_id = aws_vpc.example.id

  tags = {
    Name = "example-igw"
  }
}
