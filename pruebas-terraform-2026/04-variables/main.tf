terraform {
  required_providers {
    docker = { source = "kreuzwerker/docker", version = "~> 3.0" }
  }
}
provider "docker" { host = "npipe:////./pipe/docker_engine" }

variable "puerto" {
  type        = number
  description = "Puerto de la maquina donde se publica la web"
  default     = 8090
  validation {
    condition     = var.puerto >= 1024 && var.puerto <= 65535
    error_message = "El puerto tiene que estar entre 1024 y 65535: por debajo hacen falta permisos de administrador."
  }
}

variable "entorno" {
  type    = string
  default = "dev"
  validation {
    condition     = contains(["dev", "pre", "pro"], var.entorno)
    error_message = "entorno solo puede ser dev, pre o pro."
  }
}

variable "clave_bd" {
  type      = string
  sensitive = true
}

locals {
  nombre = "web-${var.entorno}"
}

resource "docker_image" "web" {
  name         = "nginx:1.29-alpine"
  keep_locally = true
}

resource "docker_container" "web" {
  name  = local.nombre
  image = docker_image.web.image_id
  env   = ["CLAVE_BD=${var.clave_bd}"]
  ports {
    internal = 80
    external = var.puerto
  }
}

output "url" {
  value = "http://localhost:${var.puerto}"
}

output "clave" {
  value     = var.clave_bd
  sensitive = true
}
