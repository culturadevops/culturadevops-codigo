# «Producción» del capstone, en el Docker de esta máquina, con OpenTofu.
# No hay nube ni dominio público: el anfitrión es Docker y el certificado es de una CA propia (se dice).
#
#  · el estado va CIFRADO (OpenTofu): sin esto, la clave de la base de datos queda en claro en el
#    terraform.tfstate aunque la variable sea «sensitive» (paso 3)
#  · la clave llega a Postgres como FICHERO (POSTGRES_PASSWORD_FILE), no como variable de entorno:
#    las variables de entorno las enseña `docker inspect` (paso 4)
#  · dos réplicas de la tienda detrás de nginx con TLS, `resolve` y reintento (pasos 5 y 8)
#  · Prometheus con la alerta de errores (paso 6)

variable "frase_estado" {
  sensitive = true
}
variable "clave_db" {
  sensitive = true
}
variable "certs" { description = "carpeta con raiz.pem, tienda.pem y tienda.key" }
variable "imagen_tienda" { default = "capstone-tienda:1" }

terraform {
  required_providers {
    docker = { source = "kreuzwerker/docker", version = "~> 3.9" }
  }
  encryption {
    key_provider "pbkdf2" "frase" {
      passphrase = var.frase_estado
    }
    method "aes_gcm" "cifrado" {
      keys = key_provider.pbkdf2.frase
    }
    state {
      method = method.aes_gcm.cifrado
    }
  }
}

provider "docker" {
  host = "npipe:////./pipe/docker_engine"
}

resource "docker_network" "prod" { name = "capstone-prod" }
resource "docker_volume" "datos_db" { name = "capstone-datos-db" }

resource "docker_container" "db" {
  name    = "capstone-db"
  image   = "postgres:17"
  restart = "unless-stopped"
  env     = ["POSTGRES_USER=admin", "POSTGRES_DB=tienda", "POSTGRES_PASSWORD_FILE=/run/secrets/clave_db"]
  upload {
    file    = "/run/secrets/clave_db"
    content = var.clave_db
  }
  volumes {
    volume_name    = docker_volume.datos_db.name
    container_path = "/var/lib/postgresql/data"
  }
  networks_advanced { name = docker_network.prod.name }
}

resource "docker_container" "tienda" {
  for_each = toset(["a", "b"])
  name     = "capstone-tienda-${each.key}"
  image    = var.imagen_tienda
  restart  = "unless-stopped"
  env      = ["NOMBRE=tienda-${each.key}", "APAGADO=bueno", "AUDITORIA=/datos/auditoria.log", "LOKI=http://127.0.0.1:1/"]
  networks_advanced { name = docker_network.prod.name }
}

resource "docker_container" "proxy" {
  name    = "capstone-proxy"
  image   = "nginx:1.27-alpine"
  restart = "unless-stopped"
  ports {
    internal = 443
    external = 18443
    ip       = "127.0.0.1"
  }
  upload {
    file   = "/etc/nginx/conf.d/default.conf"
    source = "${path.module}/proxy.conf"
  }
  upload {
    file   = "/c/tienda.pem"
    source = "${var.certs}/tienda-cadena.pem"
  }
  upload {
    file   = "/c/tienda.key"
    source = "${var.certs}/tienda.key"
  }
  networks_advanced {
    name    = docker_network.prod.name
    aliases = ["tienda.prod.test"]
  }
  depends_on = [docker_container.tienda]
}

resource "docker_container" "prometheus" {
  name  = "capstone-prometheus"
  image = "prom/prometheus:v3.1.0"
  ports {
    internal = 9090
    external = 19091
    ip       = "127.0.0.1"
  }
  upload {
    file   = "/etc/prometheus/prometheus.yml"
    source = "${path.module}/prometheus.yml"
  }
  upload {
    file   = "/etc/prometheus/alertas.yml"
    source = "${path.module}/alertas.yml"
  }
  networks_advanced { name = docker_network.prod.name }
}
