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

resource "aws_secretsmanager_secret" "database_password" {
  name     = "database-password"
  description = "Password for the database"
}

resource "aws_secretsmanager_secret_version" "database_password_version" {
  secret_id = aws_secretsmanager_secret.database_password.id
  secret_string = jsonencode({
    username = "dbuser"
    password = "P@ssw0rd123"
  })
}
