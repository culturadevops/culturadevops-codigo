# Terraform 2026 desde cero: tu primera infraestructura sin cuenta en ninguna nube — lo que sale en pantalla

Comandos y salidas **tal y como salen en las terminales del vídeo**, en el mismo orden.
Se sacaron automáticamente del guion del vídeo; no se escribió nada de memoria.
Las líneas con `$` son lo que tecleas; el resto es la salida que se midió al grabarlo
(tus hashes, tiempos e IDs van a ser otros).

## 1. comprobar la version · salida real

```console
$ terraform version
Terraform v1.15.8

Your version of Terraform is out of date! The latest version
is 1.16.2.
```

## 2. la version de todo el curso

```console
$ terraform version
Terraform v1.16.2
on windows_amd64
```

## 3. main.tf · bloque 1: con que hablo

```console
terraform {
  required_providers {
    docker = {
      source  = "kreuzwerker/docker"
      version = "~> 3.0"
    }
  }
}
```

## 4. main.tf · como llego

```console
provider "docker" {
  host = "npipe:////./pipe/docker_engine"
}

# sin esta linea, en Windows busca /var/run/docker.sock
```

## 5. main.tf · bloque 2: que quiero que exista

```console
resource "docker_image" "web" {
  name = "nginx:1.29-alpine"
}

resource "docker_container" "web" {
  name  = "curso-web"
  image = docker_image.web.image_id
  ports {
    internal = 80
    external = 8080
  }
}
```

## 6. terraform init · salida real

```console
$ terraform init
Initializing provider plugins...
- Installing kreuzwerker/docker v3.9.0...

Terraform has created a lock file .terraform.lock.hcl
Terraform has been successfully initialized!
```

## 7. lo que deja init en la carpeta · salida real

```console
$ du -sh .terraform
66M     .terraform
$ ls .terraform/providers/.../3.9.0/windows_amd64/
terraform-provider-docker_v3.9.0.exe   68402688 bytes
```

## 8. terraform plan · salida real

```console
$ terraform plan
  # docker_container.web will be created
  + resource "docker_container" "web" {
      + name     = "curso-web"
      + must_run = true
      ...
  # docker_image.web will be created

Plan: 2 to add, 0 to change, 0 to destroy.
```

## 9. terraform apply · salida real

```console
$ terraform apply
Plan: 2 to add, 0 to change, 0 to destroy.
docker_image.web: Creation complete after 6s
docker_container.web: Creation complete after 1s

Apply complete! Resources: 2 added, 0 changed, 0 destroyed.
```

## 10. comprobarlo sin creerle a Terraform · salida real

```console
$ docker ps --filter name=curso-web
e4adcb6f9a17  Up  0.0.0.0:8080->80/tcp
$ curl -s -o /dev/null -w "HTTP %{http_code}" localhost:8080
HTTP 200
```

## 11. apply por segunda vez · salida real

```console
$ terraform apply
No changes. Your infrastructure matches the configuration.

Terraform has compared your real infrastructure against your
configuration and found no differences, so no changes are needed.
Apply complete! Resources: 0 added, 0 changed, 0 destroyed.
```

## 12. lo que hay en la carpeta despues de apply · salida real

```console
$ ls -a
.terraform/
.terraform.lock.hcl       1260 bytes
main.tf                    402 bytes
terraform.tfstate         4825 bytes
terraform.tfstate.backup  4843 bytes
```

## 13. despues del destroy · salida real

```console
$ terraform destroy
docker_container.web: Destruction complete after 1s
docker_image.web: Destruction complete after 0s
Destroy complete! Resources: 2 destroyed.
$ docker images nginx:1.29-alpine
(nada: la imagen tambien se borro)
```

## 14. el material del curso

```console
Terraform v1.16.2  ·  kreuzwerker/docker v3.9.0
Docker 29.6.2      ·  nginx:1.29-alpine
01-primer-apply/   ·  salidas literales
```
