terraform {
  required_providers {
    docker = { source = "kreuzwerker/docker", version = "~> 3.0" }
  }
}
provider "docker" { host = "npipe:////./pipe/docker_engine" }

resource "docker_image" "web" {
  name         = "nginx:1.29-alpine"
  keep_locally = true
}

resource "docker_container" "tienda" {
  name  = "refactor-web"
  image = docker_image.web.image_id
}

moved {
  from = docker_container.web
  to   = docker_container.tienda
}
