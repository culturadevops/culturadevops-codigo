# Lección 06 · repetir con `for_each`.
# ⚠️ `for_each` indexa por CLAVE: el recurso se llama web["alfa"], web["beta"]…
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
  for_each = toset(var.sitios)
  name  = "iac-foreach-${each.key}"
  image = docker_image.nginx.image_id
}
