terraform {
  required_providers {
    docker = { source = "kreuzwerker/docker", version = "~> 3.0" }
  }
}
provider "docker" { host = "npipe:////./pipe/docker_engine" }

module "tienda" {
  source = "./modulos/web"
  nombre = "tienda"
  puerto = 8101
}

module "blog" {
  source = "./modulos/web"
  nombre = "blog"
  puerto = 8102
}

output "urls" { value = [module.tienda.url, module.blog.url] }
