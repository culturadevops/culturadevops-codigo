# Infraestructura como código de cero con OpenTofu (curso completo, sin cuenta en ninguna nube) — lo que sale en pantalla

Comandos y salidas **tal y como salen en las terminales del vídeo**, en el mismo orden.
Se sacaron automáticamente del guion del vídeo; no se escribió nada de memoria.
Las líneas con `$` son lo que tecleas; el resto es la salida que se midió al grabarlo
(tus hashes, tiempos e IDs van a ser otros).

## 1. main.tf

```console
resource "docker_image" "nginx" {
  name = "nginx:1.27-alpine"
}

resource "docker_container" "web" {
  name  = "iac-web"
  image = docker_image.nginx.image_id
  ports { internal = 80
          external = 8099 }
}
```

## 2. solo en Windows

```console
provider "docker" {
  host = "npipe:////./pipe/docker_engine"
}

# sin esto busca /var/run/docker.sock
```

## 3. en mi máquina

```console
$ tofu init

OpenTofu has been successfully initialized!
```

## 4. en mi máquina · 5 pasadas, en ms

```console
plan  sin cambios    601 581 575 583 596   ->  587
apply sin cambios    593 591 570 577 589   ->  584
apply creando       1145 1095 1120 1114    -> 1116
```

## 5. en mi máquina · después del primer apply

```console
$ ls

main.tf
terraform.tfstate      <- este no lo escribí yo
.terraform.lock.hcl
.terraform/
```

## 6. variables.tf

```console
variable "sitios" {
  type    = list(string)
  default = ["alfa", "beta", "gamma"]
}
```

## 7. salidas

```console
output "direccion" {
  value = docker_container.web.ip_address
}

$ tofu output direccion
```

## 8. la línea que crea la dependencia

```console
image = docker_image.nginx.image_id

#        ^^^^^^^^^^^^^^^^^^
#        esto es una referencia, no un texto
```

## 9. las dos declaraciones

```console
count    = length(var.sitios)
name     = "iac-${var.sitios[count.index]}"

for_each = toset(var.sitios)
name     = "iac-${each.key}"
```

## 10. quito beta de la lista

```console
- default = ["alfa", "beta", "gamma"]
+ default = ["alfa", "gamma"]
```

## 11. en mi máquina · for_each

```console
# docker_container.web["beta"] will be destroyed

Plan: 0 to add, 0 to change, 1 to destroy.
```

## 12. en mi máquina · count

```console
# docker_container.web[1] must be replaced
# docker_container.web[2] will be destroyed

Plan: 1 to add, 0 to change, 2 to destroy.
```

## 13. llamar a un módulo

```console
module "web" {
  source = "./modulos/servidor"
  nombre = "alfa"
  puerto = 8090
}
```

## 14. en mi máquina · lo creo a mano, sin OpenTofu

```console
$ docker run -d --name iac-a-mano -p 8098:80 nginx:1.27-alpine

iac-a-mano   Up Less than a second
```

## 15. en mi máquina · primer intento

```console
$ tofu import docker_container.adoptado 873541debd97

Error: ... use "tofu apply" to create a
new remote object for this resource.
```

## 16. en mi máquina · con el identificador largo

```console
$ docker inspect iac-a-mano --format '{{.Id}}'
873541debd977ded9bc7d32212d3fa6e3f...

Import successful!
```

## 17. en mi máquina · el plan tras importar

```console
$ tofu plan

# docker_container.adoptado must be replaced

Plan: 1 to add, 0 to change, 1 to destroy.
```

## 18. añado lo que faltaba

```console
ports {
  internal = 80
  external = 8098
  ip       = "::"      # esto lo puso Docker
}
```

## 19. en mi máquina · lo que faltaba de verdad

```console
~ ip = "0.0.0.0" -> "::"    # forces replacement

# el real tiene DOS enlaces, no uno
```

## 20. en mi máquina · el final

```console
Apply complete! Resources: 0 added, 1 changed, 0 destroyed.

$ tofu plan
No changes. Your infrastructure matches the configuration.
```

## 21. .terraform.lock.hcl

```console
provider "registry.opentofu.org/kreuzwerker/docker" {
  version     = "3.6.2"
  constraints = "~> 3.0"
  hashes = [
    "h1:...",
  ]
}
```

## 22. en mi máquina · el apply

```console
Outputs:

aviso = <sensitive>
```

## 23. en mi máquina · dentro del estado

```console
"result": "{BFFs*L1)AN>+=>)znmZ<BQg"

# en claro, tal cual
```

## 24. el estado se marca a sí mismo

```console
"sensitive_attributes": [
  [{"type":"get_attr","value":"result"}]
]
```

## 25. el cifrado, declarado

```console
encryption {
  key_provider "pbkdf2" "clave" {
    passphrase = var.frase
  }
  method "aes_gcm" "cifrador" {
    keys = key_provider.pbkdf2.clave
  }
}
```

## 26. en mi máquina · el error

```console
Error: Error acquiring the state lock

failed to write backup file: encountered
unencrypted payload without unencrypted
method configured
```

## 27. en mi máquina · después de cifrar

```console
$ buscar el secreto en el estado
apariciones en claro: 0

"key_provider.pbkdf2.clave": "eyJzYWx0Ijoi...
# 600.000 iteraciones para derivar la clave
```
