$ cat main.tf   # típico de lo que genera una IA al pedirle «un bucket y un servidor web»
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

$ trivy config --severity MEDIUM,HIGH,CRITICAL .
Tests: 10 (SUCCESSES: 0, FAILURES: 10)
Failures: 10 (MEDIUM: 1, HIGH: 9, CRITICAL: 0)
AVD-AWS-0028 (HIGH): Instance does not require IMDS access to require a token.
AVD-AWS-0086 (HIGH): No public access block so not blocking public acls
AVD-AWS-0087 (HIGH): No public access block so not blocking public policies
AVD-AWS-0088 (HIGH): Bucket does not have encryption enabled
AVD-AWS-0090 (MEDIUM): Bucket does not have versioning enabled
AVD-AWS-0091 (HIGH): No public access block so not blocking public acls
AVD-AWS-0093 (HIGH): No public access block so not restricting public buckets
AVD-AWS-0107 (HIGH): Security group rule allows unrestricted ingress from any IP address.
AVD-AWS-0131 (HIGH): Root block device is not encrypted.
AVD-AWS-0132 (HIGH): Bucket does not encrypt data with a customer managed key.

$ trivy config --severity MEDIUM,HIGH,CRITICAL .   # versión arreglada
│ Target  │   Type    │ Misconfigurations │
│ .       │ terraform │         0         │
│ main.tf │ terraform │         0         │
(código de salida de trivy con --exit-code 1: 0)

$ trivy --version
Version: 0.67.2
