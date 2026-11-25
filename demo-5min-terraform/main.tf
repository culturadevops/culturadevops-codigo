# Demo de «Terraform en 5 minutos» (cultura-devops, 2026-10-19). Sin nube: el proveedor «local» crea archivos en disco,
# para ver el ciclo completo (init → plan → apply → cambiar → destroy) sin cuenta ni factura.
terraform {
  required_providers {
    local = {
      source  = "hashicorp/local"
      version = "2.5.3"
    }
  }
}

variable "entorno" {
  type    = string
  default = "pruebas"
}

resource "local_file" "config" {
  filename = "${path.module}/salida/app-${var.entorno}.conf"
  content  = "entorno = ${var.entorno}\nreplicas = 2\n"
}

output "archivo" {
  value = local_file.config.filename
}
