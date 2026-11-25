terraform {
  required_providers {
    docker = { source = "kreuzwerker/docker", version = "~> 3.0" }
  }
}
provider "docker" { host = "npipe:////./pipe/docker_engine" }

resource "docker_network" "red" {
  name = "red-curso"
}

resource "docker_image" "lento" {
  name         = "alpine:3.22"
  keep_locally = true
}

# Un servicio que tarda en pararse: `sleep` como PID 1 ignora SIGTERM,
# así que Docker espera su plazo antes de matarlo.
resource "docker_container" "lento" {
  name    = "dep-lento"
  image   = docker_image.lento.image_id
  command = ["sleep", "3600"]
  networks_advanced {
    name = docker_network.red.name
  }
}
