# Cambiar Terraform sin destruir nada: moved, import y removed — lo que sale en pantalla

Comandos y salidas **tal y como salen en las terminales del vídeo**, en el mismo orden.
Se sacaron automáticamente del guion del vídeo; no se escribió nada de memoria.
Las líneas con `$` son lo que tecleas; el resto es la salida que se midió al grabarlo
(tus hashes, tiempos e IDs van a ser otros).

## 1. renombrar el recurso en el codigo

```console
- resource "docker_container" "web" {
+ resource "docker_container" "tienda" {
    name  = "refactor-web"
    image = docker_image.web.image_id
  }
```

## 2. el plan sin moved · salida real

```console
$ terraform plan
  # docker_container.tienda will be created
  # docker_container.web will be destroyed
  # (because docker_container.web is not in configuration)
Plan: 1 to add, 0 to change, 1 to destroy.
```

## 3. el bloque moved

```console
moved {
  from = docker_container.web
  to   = docker_container.tienda
}
```

## 4. el plan con moved · salida real

```console
$ terraform plan
  # docker_container.web has moved to docker_container.tienda
Plan: 0 to add, 0 to change, 0 to destroy.
$ terraform apply
contenedor antes: 253975feae06   despues: 253975feae06
```

## 5. de count a for_each sin moved · salida real

```console
$ terraform plan
  # docker_container.web[0] will be destroyed
  # docker_container.web[1] will be destroyed
  # docker_container.web[2] will be destroyed
  # docker_container.web["alfa"] will be created
Plan: 3 to add, 0 to change, 3 to destroy.
```

## 6. con tres bloques moved · salida real

```console
moved { from = docker_container.web[0]  to = docker_container.web["alfa"]  }
moved { from = docker_container.web[1]  to = docker_container.web["beta"]  }
moved { from = docker_container.web[2]  to = docker_container.web["gamma"] }
$ terraform plan
Plan: 0 to add, 0 to change, 0 to destroy.
```

## 7. los identificadores, antes y despues · salida real

```console
antes:   srv-alfa:1c4c90aa1e05  srv-beta:c852265da867  srv-gamma:64dac876c52d
despues: srv-alfa:1c4c90aa1e05  srv-beta:c852265da867  srv-gamma:64dac876c52d
```

## 8. el contenedor hecho a mano

```console
$ docker run -d --name a-mano -p 8110:80 \
$        -e MODO=produccion nginx:1.29-alpine
d34135838117...
```

## 9. el bloque import

```console
import {
  to = docker_container.a_mano
  id = "d34135838117c66dcc0f5628738..."
}

$ terraform plan -generate-config-out=generado.tf
```

## 10. importar con el identificador corto · salida real

```console
$ docker ps --filter name=corto --format '{{.ID}}'
b4715229da4e
  id = "b4715229da4e"
$ terraform plan -generate-config-out=g.tf
Error: Cannot import non-existent remote object
```

## 11. primer intento · salida real

```console
$ terraform plan -generate-config-out=generado.tf
Error: failed to read provider configuration schema for
registry.terraform.io/hashicorp/docker ... unavailable provider
```

## 12. segundo intento · salida real

```console
import {
  to       = docker_container.a_mano
  id       = "d34135838117..."
  provider = docker
}
$ wc -l generado.tf
73 generado.tf
```

## 13. el plan del import · salida real

```console
  # docker_container.a_mano must be replaced
  # (imported from "d34135838117c66dcc0f562873860bc...")
  # Warning: this will destroy the imported resource

Plan: 1 to import, 1 to add, 0 to change, 1 to destroy.
```

## 14. el motivo · salida real

```console
$ terraform plan | grep 'forces replacement'
      + env = (known after apply) # forces replacement
$ grep -c env generado.tf
0
```

## 15. el mismo import sin ninguna variable mia · salida real

```console
  # (imported from "b4715229da4e5191975de54cb50fc99927dff...")
  # Warning: this will destroy the imported resource
Plan: 1 to import, 1 to add, 0 to change, 1 to destroy.
```

## 16. tercer tropiezo · salida real

```console
$ terraform plan
Invalid import provider argument; The provider argument can only
be specified in import blocks that will generate configuration.
```

## 17. con env escrito a mano · salida real

```console
  env = ["MODO=produccion"]
$ terraform plan
      + env = [ # forces replacement
Plan: 1 to import, 1 to add, 0 to change, 1 to destroy.
```

## 18. con ignore_changes · salida real

```console
  lifecycle {
    ignore_changes = [env]
  }
$ terraform plan
  # docker_container.a_mano will be updated in-place
Plan: 1 to import, 0 to add, 1 to change, 0 to destroy.
```

## 19. el apply del import · salida real

```console
$ terraform apply
docker_container.a_mano: Import complete
Apply complete! Resources: 1 imported, 0 added, 1 changed, 0 destroyed.
contenedor tras apply: d34135838117 (antes d34135838117)
MODO=produccion
$ terraform plan
No changes. Your infrastructure matches the configuration.
```

## 20. borrar el bloque sin mas · salida real

```console
$ terraform plan
  # docker_container.a_mano will be destroyed
  # (because docker_container.a_mano is not in configuration)
Plan: 0 to add, 0 to change, 1 to destroy.
```

## 21. el bloque removed

```console
removed {
  from = docker_container.a_mano
  lifecycle {
    destroy = false
  }
}
```

## 22. el plan y el apply con removed · salida real

```console
$ terraform plan
 # docker_container.a_mano will no longer be managed by Terraform,
 # but will not be destroyed
Plan: 0 to add, 0 to change, 0 to destroy.
$ terraform state list
docker_container.tienda
docker_image.web
$ docker ps --filter name=a-mano
a-mano   Up About a minute
```

## 23. el material del curso

```console
07-refactor/salida-07-moved.txt
07-refactor/salida-07-import.txt
07-refactor/salida-07-import-plan.txt
07-refactor/salida-07-removed.txt
```
