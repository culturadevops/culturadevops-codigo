# count o for_each en Terraform: el error que destruye lo que nadie tocó — lo que sale en pantalla

Comandos y salidas **tal y como salen en las terminales del vídeo**, en el mismo orden.
Se sacaron automáticamente del guion del vídeo; no se escribió nada de memoria.
Las líneas con `$` son lo que tecleas; el resto es la salida que se midió al grabarlo
(tus hashes, tiempos e IDs van a ser otros).

## 1. con count

```console
variable "nombres" {
  default = ["alfa", "beta", "gamma"]
}

resource "docker_container" "con_count" {
  count = length(var.nombres)
  name  = "count-${var.nombres[count.index]}"
  image = docker_image.web.image_id
}
```

## 2. con for_each

```console
resource "docker_container" "con_foreach" {
  for_each = toset(var.nombres)
  name     = "foreach-${each.key}"
  image    = docker_image.web.image_id
}
```

## 3. terraform state list · salida real

```console
$ terraform state list
docker_container.con_count[0]
docker_container.con_count[1]
docker_container.con_count[2]
docker_container.con_foreach["alfa"]
docker_container.con_foreach["beta"]
docker_container.con_foreach["gamma"]
```

## 4. con count · salida real

```console
$ terraform plan
  # docker_container.con_count[1] must be replaced
      ~ name = "count-beta" -> "count-gamma" # forces replacement
  # docker_container.con_count[2] will be destroyed
  # (because index [2] is out of range for count)
```

## 5. con for_each · salida real

```console
$ terraform plan
  # docker_container.con_foreach["beta"] will be destroyed
  # (because key ["beta"] is not in for_each map)
```

## 6. for_each sobre un mapa

```console
variable "webs" {
  type    = map(number)
  default = { tienda = 8141, blog = 8142 }
}

resource "docker_container" "web" {
  for_each = var.webs
  name     = each.key
  ports { internal = 80, external = each.value }
}
```

## 7. dos webs con un solo bloque · salida real

```console
$ terraform state list
docker_container.web["blog"]
docker_container.web["tienda"]
$ curl localhost:8141 ; curl localhost:8142
tienda 200
blog 200
```

## 8. cambio solo el puerto de blog · salida real

```console
$ terraform plan -var 'webs={tienda=8141,blog=8143}'
  # docker_container.web["blog"] must be replaced
          ~ external = 8142 -> 8143 # forces replacement
Plan: 1 to add, 0 to change, 1 to destroy.
```

## 9. una expresion for · salida real

```console
output "urls" {
  value = { for nombre, puerto in var.webs :
            nombre => "http://localhost:${puerto}" }
}

urls = { blog = "http://localhost:8142", tienda = "http://localhost:8141" }
```

## 10. la red, escrita como texto

```console
resource "docker_network" "red" {
  name = "red-curso"
}

resource "docker_container" "lento" {
  networks_advanced {
    name = "red-curso"   # texto literal
  }
}
```

## 11. cinco veces crear y cinco destruir · salida real

```console
crear:     bien  bien  bien  bien  bien
destruir:  bien  bien  bien  bien  bien
```

## 12. el destroy, leido linea a linea · salida real

```console
$ terraform destroy
docker_network.red: Destroying...
docker_container.lento: Destroying...
docker_container.lento: Destruction complete after 0s
docker_network.red: Destruction complete after 2s
```

## 13. el destroy con referencia · salida real

```console
$ terraform destroy
docker_container.lento: Destroying...
docker_container.lento: Destruction complete after 1s
docker_network.red: Destroying...
docker_network.red: Destruction complete after 2s
```

## 14. terraform graph con el nombre en texto · salida real

```console
$ terraform graph | grep -- '->'
"docker_container.web" -> "docker_image.web";

(ninguna flecha hacia la red)
```

## 15. terraform graph con referencia · salida real

```console
$ terraform graph | grep -- '->'
"docker_container.web" -> "docker_image.web";
"docker_container.web" -> "docker_network.red";
```

## 16. depends_on tambien dibuja la flecha · salida real

```console
  depends_on = [docker_network.red]
$ terraform graph | grep -- '->'
"docker_container.web" -> "docker_image.web";
"docker_container.web" -> "docker_network.red";
```

## 17. el material del curso

```console
05-repetir/salida-05-count-foreach.txt
05b-paralelo/salida-05-paralelo.txt
05c-dependencias/salida-05-orden-destroy.txt
```
