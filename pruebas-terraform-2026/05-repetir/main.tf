terraform {
  required_providers {
    docker = { source = "kreuzwerker/docker", version = "~> 3.0" }
  }
}
provider "docker" { host = "npipe:////./pipe/docker_engine" }

variable "nombres" {
  type    = list(string)
  default = ["alfa", "beta", "gamma"]
}

resource "docker_image" "web" {
  name         = "nginx:1.29-alpine"
  keep_locally = true
}

resource "docker_container" "web" {
  for_each = toset(var.nombres)
  name     = "srv-${each.key}"
  image = docker_image.web.image_id
}

moved {
  from = docker_container.web[0]
  to   = docker_container.web["alfa"]
}
moved {
  from = docker_container.web[1]
  to   = docker_container.web["beta"]
}
moved {
  from = docker_container.web[2]
  to   = docker_container.web["gamma"]
}
