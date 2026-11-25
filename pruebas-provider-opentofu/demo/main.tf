terraform {
  required_providers {
    ficherito = {
      source  = "registry.opentofu.org/lab/ficherito"
      version = "0.1.0"
    }
  }
}

provider "ficherito" {}

resource "ficherito_fichero" "saludo" {
  ruta      = "/lab/salida/hola.txt"
  contenido = "hola desde el proveedor"
}
