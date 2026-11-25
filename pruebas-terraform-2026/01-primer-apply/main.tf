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

resource "docker_image" "web" {
  name = "nginx:1.29-alpine"
}

resource "docker_container" "web" {
  name  = "curso-web"
  image = docker_image.web.image_id
  ports {
    internal = 80
    external = 8080
  }
}
