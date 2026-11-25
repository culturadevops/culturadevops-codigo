# Lección 06 · repetir con `count`.
# ⚠️ `count` indexa por POSICIÓN: el recurso se llama web[0], web[1], web[2].
terraform {
  required_providers { docker = { source = "kreuzwerker/docker", version = "~> 3.0" } }
}
provider "docker" { host = "npipe:////./pipe/docker_engine" }

variable "sitios" {
  type    = list(string)
  default = ["alfa", "gamma"]
}

resource "docker_image" "nginx" {
  name         = "nginx:1.27-alpine"
  keep_locally = true
}

resource "docker_container" "web" {
  count = length(var.sitios)
  name  = "iac-count-${var.sitios[count.index]}"
  image = docker_image.nginx.image_id
}
