# Leer un plan de Terraform: el aviso de que va a destruir algo — lo que sale en pantalla

Comandos y salidas **tal y como salen en las terminales del vídeo**, en el mismo orden.
Se sacaron automáticamente del guion del vídeo; no se escribió nada de memoria.
Las líneas con `$` son lo que tecleas; el resto es la salida que se midió al grabarlo
(tus hashes, tiempos e IDs van a ser otros).

## 1. los simbolos de un plan

```console
  +    create
  ~    update in-place
  -    destroy
 -/+   destroy and then create replacement
 +/-   create replacement and then destroy
```

## 2. cambio 1: el puerto · salida real

```console
$ terraform plan
-/+ destroy and then create replacement

  # docker_container.web must be replaced
-/+ resource "docker_container" "web" {
```

## 3. el motivo, dentro del plan · salida real

```console
      ~ ports {
          ~ external = 8080 -> 8081 # forces replacement
        }

Plan: 1 to add, 0 to change, 1 to destroy.
```

## 4. cambio 2: el nombre · salida real

```console
$ terraform plan
  # docker_container.web must be replaced
      ~ name = "curso-web" -> "curso-web2" # forces replacement

Plan: 1 to add, 0 to change, 1 to destroy.
```

## 5. cambio 3: restart · salida real

```console
$ terraform plan
  ~ update in-place

  # docker_container.web will be updated in-place
      ~ restart = "no" -> "always"

Plan: 0 to add, 1 to change, 0 to destroy.
```

## 6. known after apply · salida real

```console
      + id           = (known after apply)
      + hostname     = (known after apply)
      + network_data = (known after apply)
      + must_run     = true
      + name         = "curso-web"
```

## 7. main.tf · crear antes de destruir

```console
resource "docker_container" "web" {
  name = "plan-web"
  ...
  lifecycle {
    create_before_destroy = true
  }
}
```

## 8. el plan con create_before_destroy · salida real

```console
$ terraform plan
+/- create replacement and then destroy
  # docker_container.web must be replaced
          ~ external = 8130 -> 8131 # forces replacement
Plan: 1 to add, 0 to change, 1 to destroy.
```

## 9. terraform apply · salida real

```console
$ terraform apply
docker_container.web: Creating...
Error: Unable to create container:
Conflict. The container name "/plan-web" is already in use
```

## 10. con un nombre que cambia · salida real

```console
$ terraform apply
docker_container.web: Creation complete after 1s
docker_container.web (deposed object 23e8c72b): Destroying...
Apply complete! Resources: 1 added, 0 changed, 1 destroyed.
```

## 11. el aviso al final de cada plan · salida real

```console
Note: You didn't use the -out option to save this plan, so
Terraform can't guarantee to take exactly these actions if you
run "terraform apply" now.
```

## 12. guardar el plan y aplicarlo · salida real

```console
$ terraform plan -out=cambio.plan
Plan: 0 to add, 1 to change, 0 to destroy.
Saved the plan to: cambio.plan
$ terraform show cambio.plan
  # docker_container.web will be updated in-place
      ~ restart = "no" -> "always"
```

## 13. aplicar un plan que ya no vale · salida real

```console
$ terraform apply cambio.plan
Error: Saved plan is stale

The given plan file can no longer be applied because the state
was changed by another operation after the plan was created.
```

## 14. terraform plan -detailed-exitcode · codigos reales

```console
$ terraform plan -detailed-exitcode   # sin cambios
codigo: 0
$ terraform plan -detailed-exitcode   # restart cambiado
codigo: 2
$ terraform plan -detailed-exitcode   # bloque sin cerrar
codigo: 1
```

## 15. el plan en JSON · salida real

```console
$ terraform plan -out=p.bin
$ terraform show -json p.bin > p.json
docker_container.web  ['create', 'delete']
docker_image.web      ['no-op']
borrados: 1
```

## 16. terraform plan -destroy · salida real

```console
$ terraform plan -destroy
  # docker_container.web will be destroyed
  # docker_image.web will be destroyed

Plan: 0 to add, 0 to change, 2 to destroy.
```

## 17. el material del curso

```console
salida-01-cambios.txt
salida-02-plan-guardado.txt
02-plan/salida-02-create-before-destroy.txt
```
