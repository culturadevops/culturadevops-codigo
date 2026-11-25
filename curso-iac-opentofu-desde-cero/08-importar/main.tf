# Lección 08 · adoptar algo que ya existe.
#
# ⚠️ La declaración se escribe ANTES de importar: `tofu import` no genera código, solo mete el
# recurso en el estado. Si el bloque no existe, se niega.
terraform {
  required_providers { docker = { source = "kreuzwerker/docker", version = "~> 3.0" } }
}
provider "docker" { host = "npipe:////./pipe/docker_engine" }

resource "docker_container" "adoptado" {
  name  = "iac-a-mano"
  image = "nginx:1.27-alpine"
  # ⚠️ `ip` no lo escribió nadie: se lo puso Docker al crear el contenedor a mano. Sin
  # declararlo, el bloque de puertos no coincide con el real y OpenTofu quiere REEMPLAZAR.
  # ⚠️ DOS bloques, no uno. Docker publica el puerto en IPv4 y en IPv6 por defecto, y el
  # estado importado trae las dos. Con uno solo, el plan quiere reemplazar el contenedor para
  # siempre. Esto es lo que de verdad cuesta de importar: no el mandato, sino cuadrar la
  # declaración con lo que ya existe, atributo a atributo.
  ports {
    internal = 80
    external = 8098
    ip       = "0.0.0.0"
  }
  ports {
    internal = 80
    external = 8098
    ip       = "::"
  }
  env = []
}
