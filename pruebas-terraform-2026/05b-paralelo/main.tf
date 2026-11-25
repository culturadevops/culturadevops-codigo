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

resource "docker_container" "web" {
  for_each = toset([for i in range(12) : format("n%02d", i)])
  name     = "par-${each.key}"
  image    = docker_image.web.image_id
}
