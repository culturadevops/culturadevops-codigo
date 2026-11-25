#!/usr/bin/env bash
# Demo del vídeo 478 «¿Debo aprender cloud computing en la era de la IA?» — se EJECUTA y su salida va a SALIDA.md.
# Un Terraform como el que escribe una IA cuando le pides «un bucket y un servidor web en AWS»: funciona, y deja la puerta
# abierta (SSH a todo internet, bucket sin bloqueo de acceso público, disco sin cifrar). Trivy lo revisa SIN desplegar nada
# (no hace falta cuenta de AWS), se arregla y se vuelve a revisar. Nada se crea en la nube.
set -u
T=$(mktemp -d)
cd "$T"
mkdir ia arreglado

cat > ia/main.tf <<'EOF'
resource "aws_s3_bucket" "fotos" {
  bucket = "mi-app-fotos"
}

resource "aws_security_group" "web" {
  name        = "web"
  description = "web"

  ingress {
    from_port   = 22
    to_port     = 22
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  ingress {
    from_port   = 80
    to_port     = 80
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }
}

resource "aws_instance" "web" {
  ami             = "ami-0abcdef1234567890"
  instance_type   = "t3.micro"
  security_groups = [aws_security_group.web.name]
}
EOF

cat > arreglado/main.tf <<'EOF'
resource "aws_kms_key" "fotos" {
  description         = "Clave propia para el bucket de fotos"
  enable_key_rotation = true
}

resource "aws_s3_bucket" "fotos" {
  bucket = "mi-app-fotos"
}

resource "aws_s3_bucket_public_access_block" "fotos" {
  bucket                  = aws_s3_bucket.fotos.id
  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

resource "aws_s3_bucket_server_side_encryption_configuration" "fotos" {
  bucket = aws_s3_bucket.fotos.id
  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm     = "aws:kms"
      kms_master_key_id = aws_kms_key.fotos.arn
    }
  }
}

resource "aws_s3_bucket_versioning" "fotos" {
  bucket = aws_s3_bucket.fotos.id
  versioning_configuration {
    status = "Enabled"
  }
}

resource "aws_security_group" "web" {
  name        = "web"
  description = "Servidor web: solo HTTPS desde internet"

  ingress {
    description = "HTTPS"
    from_port   = 443
    to_port     = 443
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }
}

resource "aws_instance" "web" {
  ami                    = "ami-0abcdef1234567890"
  instance_type          = "t3.micro"
  vpc_security_group_ids = [aws_security_group.web.id]

  metadata_options {
    http_tokens = "required"
  }

  root_block_device {
    encrypted = true
  }
}
EOF

TRIVY="docker run --rm -v $(cygpath -w "$T"):/src aquasec/trivy:0.67.2 config --quiet"
echo '$ cat main.tf   # típico de lo que genera una IA al pedirle «un bucket y un servidor web»'; cat ia/main.tf
echo
echo '$ trivy config --severity MEDIUM,HIGH,CRITICAL .'
MSYS_NO_PATHCONV=1 $TRIVY --severity MEDIUM,HIGH,CRITICAL /src/ia 2>&1 | grep -E "^Tests:|^Failures:|^AVD-" | head -40
echo
echo '$ trivy config --severity MEDIUM,HIGH,CRITICAL .   # versión arreglada'
MSYS_NO_PATHCONV=1 $TRIVY --severity MEDIUM,HIGH,CRITICAL /src/arreglado 2>&1 | grep -E "^Tests:|^Failures:|^AVD-|Misconfig|terraform" | head -12
echo "(código de salida de trivy con --exit-code 1: $(MSYS_NO_PATHCONV=1 $TRIVY --severity HIGH,CRITICAL --exit-code 1 /src/arreglado >/dev/null 2>&1; echo $?))"
echo
echo '$ trivy --version'
MSYS_NO_PATHCONV=1 docker run --rm aquasec/trivy:0.67.2 --version 2>&1 | head -1
cd / && rm -rf "$T"
