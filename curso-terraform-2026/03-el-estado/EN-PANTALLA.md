# El estado de Terraform: el día que un plan borró mi contenedor — lo que sale en pantalla

Comandos y salidas **tal y como salen en las terminales del vídeo**, en el mismo orden.
Se sacaron automáticamente del guion del vídeo; no se escribió nada de memoria.
Las líneas con `$` son lo que tecleas; el resto es la salida que se midió al grabarlo
(tus hashes, tiempos e IDs van a ser otros).

## 1. dentro de terraform.tfstate · salida real

```console
$ wc -c terraform.tfstate
4842 terraform.tfstate

version: 4   terraform_version: 1.16.2   serial: 68
```

## 2. el enlace que guarda el estado · salida real

```console
managed docker_container web
   id:   02a34fa12a5fc64cfd9a2a75...
   name: curso-web

managed docker_image web
   id:   sha256:5616878291a2eed59...
```

## 3. mirar el estado sin abrir el JSON · salida real

```console
$ terraform state list
docker_container.web
docker_image.web
$ terraform state show docker_container.web
resource "docker_container" "web" {
    command = ["nginx", "-g", "daemon off;"]
    ...
```

## 4. borro el estado y hago plan · salida real

```console
$ rm terraform.tfstate
$ terraform plan
  # docker_container.web will be created
  # docker_image.web will be created
Plan: 2 to add, 0 to change, 0 to destroy.
```

## 5. y aplico · salida real

```console
$ terraform apply
docker_image.web: Creation complete after 0s
Error: Unable to create container:
Conflict. The container name "/curso-web" is already in use
```

## 6. devuelvo el estado · salida real

```console
$ mv estado.guardado terraform.tfstate
$ terraform plan
No changes. Your infrastructure matches the configuration.
```

## 7. terraform state rm · salida real

```console
$ terraform state rm docker_container.web
Successfully removed 1 resource instance(s).
$ docker ps --filter name=curso-web
curso-web  Up 3 seconds
$ terraform plan
  # docker_container.web will be created
```

## 8. plan -refresh-only tras un docker rm · salida real

```console
$ docker rm -f curso-web
$ terraform plan -refresh-only
Note: Objects have changed outside of Terraform

  # docker_container.web has been deleted
  - resource "docker_container" "web" {
      - command = ["nginx", "-g", "daemon off;"] -> null
```

## 9. paro el contenedor, no lo borro · salida real

```console
$ docker stop curso-web
$ docker ps -a --filter name=curso-web
curso-web   Exited (0) Less than a second ago
```

## 10. terraform plan · salida real

```console
$ terraform plan
  # docker_container.web will be created
Plan: 1 to add, 0 to change, 0 to destroy.
$ docker ps -a --filter name=curso-web
(nada: el contenedor ya no existe)
```

## 11. tres pruebas desde el mismo punto · salida real

```console
plan -refresh=false | antes: Exited (0) | despues: Exited (0)
plan (normal)       | antes: Exited (0) | despues: <NO EXISTE>
plan -refresh-only  | antes: Exited (0) | despues: <NO EXISTE>
```

## 12. dos operaciones a la vez · salida real

```console
$ ls -la .terraform.tfstate.lock.info
-rw-r--r--  221  .terraform.tfstate.lock.info
$ terraform plan
Error: Error acquiring the state lock
```

## 13. el material del curso

```console
salida-03-plan-borra.txt   · las tres pruebas
salida-03-estado.txt       · estado borrado y state rm
salida-03-lock.txt         · el bloqueo
```
