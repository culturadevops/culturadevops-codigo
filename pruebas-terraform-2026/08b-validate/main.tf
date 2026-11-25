terraform {
  required_providers {
    docker = { source = "kreuzwerker/docker", version = "~> 3.0" }
  }
}
provider "docker" { host = "npipe:////./pipe/docker_engine" }

resource "docker_container" "web" {
  name  = "validar-web"
  image = "nginx:1.29-alpine"
  puertos = 8080
}
