## main.tf — el MISMO entorno del guion a_mano.sh, escrito como código.
##
## Una red, un volumen, una base de datos, una caché y dos copias de la aplicación.
## Ni una pieza más ni una menos, para que la comparación valga algo.

terraform {
  required_providers {
    docker = {
      source  = "kreuzwerker/docker"
      version = "~> 3.0"
    }
  }
}

provider "docker" {}

variable "entorno" {
  description = "El nombre del entorno. Cambiar esto es levantar uno nuevo entero."
  type        = string
  default     = "pruebas"
}

variable "copias_app" {
  description = "Cuántas copias de la aplicación."
  type        = number
  default     = 2
}

resource "docker_network" "red" {
  name = "${var.entorno}-red"
}

resource "docker_volume" "datos" {
  name = "${var.entorno}-datos"
}

resource "docker_image" "postgres" {
  name = "postgres:17-alpine"
}

resource "docker_image" "redis" {
  name = "redis:7-alpine"
}

resource "docker_image" "app" {
  name = "nginx:alpine"
}

resource "docker_container" "db" {
  name  = "${var.entorno}-db"
  image = docker_image.postgres.image_id
  env   = ["POSTGRES_PASSWORD=secreto"]

  networks_advanced {
    name = docker_network.red.name
  }

  volumes {
    volume_name    = docker_volume.datos.name
    container_path = "/var/lib/postgresql/data"
  }
}

resource "docker_container" "cache" {
  name  = "${var.entorno}-cache"
  image = docker_image.redis.image_id

  networks_advanced {
    name = docker_network.red.name
  }
}

## Y aquí está la diferencia que decide el vídeo: DOS copias o VEINTE es el mismo código.
resource "docker_container" "app" {
  count = var.copias_app
  name  = "${var.entorno}-app-${count.index + 1}"
  image = docker_image.app.image_id
  env   = ["DB=${docker_container.db.name}", "CACHE=${docker_container.cache.name}"]

  networks_advanced {
    name = docker_network.red.name
  }
}
