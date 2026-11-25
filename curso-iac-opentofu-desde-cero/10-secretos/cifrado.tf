# El cifrado de estado que trae OpenTofu y Terraform no tiene.
# ⚠️ La frase de paso va por variable de entorno, NUNCA escrita aquí.
terraform {
  encryption {
    key_provider "pbkdf2" "clave" {
      passphrase = var.frase
    }
    method "aes_gcm" "cifrador" {
      keys = key_provider.pbkdf2.clave
    }
    # ⚠️ `fallback` es el puente para MIGRAR un estado que ya existe sin cifrar. Sin él,
    # OpenTofu se niega hasta a respaldarlo: «encountered unencrypted payload without
    # unencrypted method configured». Se quita en cuanto el estado ya está cifrado.
    method "unencrypted" "en_claro" {}
    state {
      method = method.aes_gcm.cifrador
      fallback {
        method = method.unencrypted.en_claro
      }
    }
  }
}
variable "frase" {
  type      = string
  sensitive = true
}
