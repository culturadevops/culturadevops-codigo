# El entorno de pruebas de la lección 6, contra moto (emulador de AWS). Nada de esto cobra.
# `default_tags` marca TODO lo que crea tofu: así se distingue de lo que alguien crea a mano.

variable "endpoint" { default = "http://127.0.0.1:5055" }
variable "ami" {}

provider "aws" {
  region                      = "us-east-1"
  access_key                  = "prueba"
  secret_key                  = "prueba"
  skip_credentials_validation = true
  skip_requesting_account_id  = true
  skip_metadata_api_check     = true
  endpoints {
    ec2 = var.endpoint
    sts = var.endpoint
  }
  default_tags {
    tags = { Gestion = "tofu", Proyecto = "pruebas" }
  }
}

resource "aws_vpc" "red" { cidr_block = "10.0.0.0/16" }

resource "aws_subnet" "pub" {
  vpc_id            = aws_vpc.red.id
  cidr_block        = "10.0.1.0/24"
  availability_zone = "us-east-1a"
}

resource "aws_instance" "app" {
  ami           = var.ami
  instance_type = "t3.micro"
  subnet_id     = aws_subnet.pub.id
}

resource "aws_ebs_volume" "datos" {
  availability_zone = "us-east-1a"
  size              = 50
  type              = "gp3"
}

resource "aws_volume_attachment" "datos" {
  device_name = "/dev/sdf"
  volume_id   = aws_ebs_volume.datos.id
  instance_id = aws_instance.app.id
}

resource "aws_eip" "app" {
  domain   = "vpc"
  instance = aws_instance.app.id
}

resource "aws_eip" "nat" { domain = "vpc" }

resource "aws_nat_gateway" "salida" {
  allocation_id = aws_eip.nat.id
  subnet_id     = aws_subnet.pub.id
}
