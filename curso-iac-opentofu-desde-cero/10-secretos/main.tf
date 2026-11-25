# Lección 10 · los secretos acaban en el estado.
#
# ⛔ El secreto es de mentira y se genera aquí a propósito, para poder enseñar que el estado lo
# guarda en claro. Seguridad defensiva: sirve para mirar TU estado.
terraform {
  required_providers {
    random = { source = "hashicorp/random", version = "~> 3.6" }
  }
}

resource "random_password" "de_la_base" {
  length  = 24
  special = true
}

output "aviso" {
  value     = random_password.de_la_base.result
  sensitive = true
}
