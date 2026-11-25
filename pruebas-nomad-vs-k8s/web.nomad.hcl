# web.nomad.hcl — un servidor web con 2 réplicas, en Nomad.
# ⛔ Ni una línea de más: tiene que crear exactamente lo mismo que el YAML de Kubernetes.
job "web" {
  group "web" {
    count = 2
    network {
      port "http" { to = 80 }
    }
    task "servidor" {
      driver = "docker"
      config {
        image = "nginx:alpine"
        ports = ["http"]
      }
      resources {
        cpu    = 100
        memory = 64
      }
    }
  }
}
