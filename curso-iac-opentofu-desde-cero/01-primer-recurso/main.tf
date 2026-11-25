# Lección 02 · el primer recurso.
#
# ⚠️ En Windows el demonio de Docker NO escucha en un socket de Unix: escucha en una tubería
# con nombre. Sin `host` explícito el proveedor busca /var/run/docker.sock y no encuentra nada.
terraform {
  required_providers {
    docker = {
      source  = "kreuzwerker/docker"
      version = "~> 3.0"
    }
  }
}

provider "docker" {
  host = "npipe:////./pipe/docker_engine"
}

resource "docker_image" "nginx" {
  name         = "nginx:1.27-alpine"
  keep_locally = true
}

resource "docker_container" "web" {
  name  = "iac-web"
  image = docker_image.nginx.image_id

  ports {
    internal = 80
    external = 8099
  }
}
