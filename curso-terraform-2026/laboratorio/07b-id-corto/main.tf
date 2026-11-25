terraform {
  required_providers {
    docker = { source = "kreuzwerker/docker", version = "~> 3.0" }
  }
}
provider "docker" { host = "npipe:////./pipe/docker_engine" }

import {
  to       = docker_container.corto
  id       = "b4715229da4e5191975de54cb50fc99927dff1602dfdeb57dc5d0c7ff2adac64"
  provider = docker
}
