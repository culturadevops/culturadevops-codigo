# Pruebas en Terraform: el test que pasa sin ejecutar nada — lo que sale en pantalla

Comandos y salidas **tal y como salen en las terminales del vídeo**, en el mismo orden.
Se sacaron automáticamente del guion del vídeo; no se escribió nada de memoria.
Las líneas con `$` son lo que tecleas; el resto es la salida que se midió al grabarlo
(tus hashes, tiempos e IDs van a ser otros).

## 1. tests/web.tftest.hcl

```console
run "el_puerto_por_omision_es_8120" {
  command = plan
  assert {
    condition = docker_container.web.ports[0].external == 8120
  }
}
run "crea_el_contenedor_de_verdad" {
  command   = apply
  variables { puerto = 8121 }
  assert { condition = output.url == "http://localhost:8121" }
}
```

## 2. el bloque check en main.tf

```console
check "la_web_responde" {
  data "http" "portada" {
    url = "http://localhost:${var.puerto}"
  }
  assert {
    condition     = data.http.portada.status_code == 200
    error_message = "La web no devuelve 200."
  }
}
```

## 3. check en un plan normal · salida real

```console
$ terraform plan
Plan: 2 to add, 0 to change, 0 to destroy.
Warning: Error making request
  on main.tf line 31, in check "la_web_responde":
GET http://localhost:8120 giving up after 1 attempt(s)
codigo de salida: 0
```

## 4. terraform test, primer intento · salida real

```console
$ terraform test
  run "el_puerto_por_omision_es_8120"... fail
Error: Error making request
  on main.tf line 31, in check "la_web_responde":
  run "crea_el_contenedor_de_verdad"... skip
Failure! 0 passed, 1 failed, 1 skipped.
```

## 5. con expect_failures · salida real

```console
run "el_puerto_por_omision_es_8120" {
  command         = plan
  expect_failures = [check.la_web_responde]
  ...
$ terraform test
Success! 3 passed, 0 failed.
```

## 6. despues de las pruebas · salida real

```console
tests\web.tftest.hcl... tearing down
tests\web.tftest.hcl... pass
$ docker ps -a --filter name=pruebas-web
(vacio: las pruebas destruyeron lo que crearon)
```

## 7. tests/simulado.tftest.hcl

```console
mock_provider "docker" {}
mock_provider "http" {
  mock_data "http" {
    defaults = { status_code = 200 }
  }
}
run "sin_docker_el_nombre_sigue_bien" {
  command = apply
  assert { condition = docker_container.web.name == "pruebas-web" }
}
```

## 8. la primera medicion · salida real

```console
test simulado                  96   91   89   92   89   media 91 ms
test con docker real           93   90   94   93   91   media 92 ms
```

## 9. por que tardaba 91 ms · salida real

```console
$ terraform test -filter=tests/simulado.tftest.hcl
Warning: Unknown test file
The specified test file, tests/simulado.tftest.hcl, could not be found.
$ terraform test -filter=tests\simulado.tftest.hcl
tests\simulado.tftest.hcl... pass
```

## 10. terraform test con un filtro roto · salida real

```console
$ terraform test -filter=tests/no-existe.tftest.hcl
Success! 0 passed, 0 failed.

Warning: Unknown test file
The specified test file, tests/no-existe.tftest.hcl, could not be found.
codigo de salida: 0
```

## 11. una linea que evita la trampa

```console
salida=$(terraform test -no-color)
echo "$salida"
echo "$salida" | grep -q " 0 passed" && exit 1

# si no se ejecuto ninguna prueba, el paso falla
```

## 12. terraform fmt -check · salida real

```console
$ terraform fmt -check
mal.tf
codigo de salida: 3
$ terraform fmt -diff mal.tf
-type=string
-  default    = "a"
+  type    = string
+  default = "a"
```

## 13. lo que caza validate · salida real

```console
$ terraform validate
Error: Reference to undeclared resource
  10:   image = docker_image.wbe.image_id
$ terraform validate
Error: Unsupported argument
  11:   puertos = 8080
An argument named "puertos" is not expected here.
```

## 14. terraform query · salida real

```console
list "docker_container" "todos" {
  provider = docker
}
$ terraform query
Error: Invalid list resource
The provider kreuzwerker/docker does not support list resource
"docker_container".
```

## 15. el material del curso

```console
Terraform v1.16.2 · kreuzwerker/docker v3.9.0 · Docker 29.6.2
MEDIDO.md             · todas las cifras del curso
08-pruebas/           · test, check, mock y el filtro roto
09-query/             · terraform query
```
