terraform {
  required_providers {
    docker = { source = "kreuzwerker/docker", version = "~> 3.0" }
  }
}
provider "docker" { host = "npipe:////./pipe/docker_engine" }

variable "webs" {
  type = map(number)
  default = {
    tienda = 8141
    blog   = 8142
  }
}

resource "docker_image" "web" {
  name         = "nginx:1.29-alpine"
  keep_locally = true
}

resource "docker_network" "red" {
  name = "red-mapa"
}

resource "docker_container" "web" {
  for_each = var.webs
  name     = each.key
  image    = docker_image.web.image_id
  ports {
    internal = 80
    external = each.value
  }
  depends_on = [docker_network.red]
}

output "urls" {
  value = { for nombre, puerto in var.webs : nombre => "http://localhost:${puerto}" }
}
