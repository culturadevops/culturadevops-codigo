terraform {
  required_providers {
    docker = { source = "kreuzwerker/docker", version = "~> 3.0" }
  }
}

variable "nombre" { type = string }
variable "puerto" { type = number }

resource "docker_image" "web" {
  name         = "nginx:1.29-alpine"
  keep_locally = true
}

resource "docker_container" "web" {
  name  = var.nombre
  image = docker_image.web.image_id
  ports {
    internal = 80
    external = var.puerto
  }
}

output "url" { value = "http://localhost:${var.puerto}" }
