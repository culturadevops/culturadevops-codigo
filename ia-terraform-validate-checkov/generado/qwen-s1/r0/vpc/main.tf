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

resource "aws_vpc" "main" {
  cidr_block = "10.0.0.0/16"

  tags = {
    Name = "MainVPC"
  }
}

resource "aws_subnet" "public1" {
  count              = 1
  vpc_id             = aws_vpc.main.id
  cidr_block         = "10.0.1.0/24"
  map_public_ip_on_launch = true

  tags = {
    Name = "PublicSubnet1"
  }
}

resource "aws_subnet" "public2" {
  count              = 1
  vpc_id             = aws_vpc.main.id
  cidr_block         = "10.0.2.0/24"
  map_public_ip_on_launch = true

  tags = {
    Name = "PublicSubnet2"
  }
}

resource "aws_subnet" "private1" {
  count              = 1
  vpc_id             = aws_vpc.main.id
  cidr_block         = "10.0.3.0/24"

  tags = {
    Name = "PrivateSubnet1"
  }
}

resource "aws_subnet" "private2" {
  count              = 1
  vpc_id             = aws_vpc.main.id
  cidr_block         = "10.0.4.0/24"

  tags = {
    Name = "PrivateSubnet2"
  }
}

resource "aws_nat_gateway" "nat" {
  count = 1

  allocation_id = aws_eip.nat_eip[count.index].id
  subnet_id     = aws_subnet.public1[count.index].id

  tags = {
    Name = "NATGateway"
  }
}

resource "aws_eip" "nat_eip" {
  count = 1

  vpc = true

  depends_on = [aws_vpc.main]
}

resource "aws_security_group" "nat_sg" {
  name        = "NatSG"
  description = "Security group for NAT"
  vpc_id      = aws_vpc.main.id

  ingress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }
}

resource "aws_route_table" "public_route_table" {
  vpc_id = aws_vpc.main.id

  route {
    cidr_block = "0.0.0.0/0"
    gateway_id = aws_nat_gateway.nat[count.index].id
  }
}

resource "aws_route_table_association" "public_route_table_association1" {
  count = 1
  subnet_id      = aws_subnet.public1[count.index].id
  route_table_id = aws_route_table.public_route_table.id
}

resource "aws_route_table_association" "public_route_table_association2" {
  count = 1
  subnet_id      = aws_subnet.public2[count.index].id
  route_table_id = aws_route_table.public_route_table.id
}
