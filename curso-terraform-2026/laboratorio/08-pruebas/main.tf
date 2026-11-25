terraform {
  required_providers {
    docker = { source = "kreuzwerker/docker", version = "~> 3.0" }
    http   = { source = "hashicorp/http", version = "~> 3.0" }
  }
}
provider "docker" { host = "npipe:////./pipe/docker_engine" }

variable "puerto" {
  type    = number
  default = 8120
}

resource "docker_image" "web" {
  name         = "nginx:1.29-alpine"
  keep_locally = true
}

resource "docker_container" "web" {
  name  = "pruebas-web"
  image = docker_image.web.image_id
  ports {
    internal = 80
    external = var.puerto
  }
}

output "url" { value = "http://localhost:${var.puerto}" }

check "la_web_responde" {
  data "http" "portada" {
    url = "http://localhost:${var.puerto}"
  }
  assert {
    condition     = data.http.portada.status_code == 200
    error_message = "La web no devuelve 200."
  }
}
