# Módulos y versiones en Terraform: el archivo que tienes que subir al repositorio — lo que sale en pantalla

Comandos y salidas **tal y como salen en las terminales del vídeo**, en el mismo orden.
Se sacaron automáticamente del guion del vídeo; no se escribió nada de memoria.
Las líneas con `$` son lo que tecleas; el resto es la salida que se midió al grabarlo
(tus hashes, tiempos e IDs van a ser otros).

## 1. modulos/web/main.tf

```console
variable "nombre" { type = string }
variable "puerto" { type = number }

resource "docker_image" "web"     { ... }
resource "docker_container" "web" {
  name = var.nombre
  ports { internal = 80, external = var.puerto }
}

output "url" { value = "http://localhost:${var.puerto}" }
```

## 2. main.tf de la raiz

```console
module "tienda" {
  source = "./modulos/web"
  nombre = "tienda"
  puerto = 8101
}

module "blog" {
  source = "./modulos/web"
  nombre = "blog"
  puerto = 8102
}
```

## 3. plan sin init · salida real

```console
$ terraform plan
Error: Module not installed
  on main.tf line 8:
   8: module "tienda" {
This module is not yet installed. Run "terraform init" to install
all modules required by this configuration.
```

## 4. init y apply · salida real

```console
$ terraform init
Initializing modules...
- tienda in modulos\web
- blog in modulos\web
$ terraform apply
Apply complete! Resources: 4 added, 0 changed, 0 destroyed.
tienda 200  ·  blog 200
```

## 5. terraform state list · salida real

```console
$ terraform state list
module.blog.docker_container.web
module.blog.docker_image.web
module.tienda.docker_container.web
module.tienda.docker_image.web
```

## 6. usar los outputs de los modulos · salida real

```console
output "urls" { value = [module.tienda.url, module.blog.url] }
$ terraform apply
urls = [
  "http://localhost:8101",
  "http://localhost:8102",
]
```

## 7. destroy solo del modulo blog · salida real

```console
$ terraform destroy -target=module.blog
module.blog.docker_container.web: Destruction complete after 1s
module.blog.docker_image.web: Destroying...
Warning: Applied changes may be incomplete
Error: Unable to remove Docker image: conflict: unable to delete
nginx:1.29-alpine - container 887c6fe9a3b5 is using its referenced image
```

## 8. terraform providers · salida real

```console
$ terraform providers
.
├── provider[registry.terraform.io/kreuzwerker/docker] ~> 3.0
├── module.tienda
│   └── provider[registry.terraform.io/kreuzwerker/docker] ~> 3.0
└── module.blog
    └── provider[registry.terraform.io/kreuzwerker/docker] ~> 3.0
```

## 9. .terraform.lock.hcl · salida real

```console
provider "registry.terraform.io/kreuzwerker/docker" {
  version     = "3.9.0"
  constraints = "~> 3.0"
  hashes = [
    "h1:o/2lXPHpHZr4fuVmCgcJu8Dk3/bnL6qp8fr0JM36bBM=",
    "zh:0ead8281830e9b9496651282235d9a139ba1b1b6ff79e39...",
    ... 13 lineas zh en total
  ]
}
```

## 10. contar las huellas · salida real

```console
$ grep -c 'h1:' .terraform.lock.hcl
1
$ grep -c 'zh:' .terraform.lock.hcl
13
```

## 11. huellas para mas de una plataforma · salida real

```console
$ terraform providers lock -platform=windows_amd64 \
$                           -platform=linux_amd64
lineas h1 despues: 2
>     "h1:EAdNh5KgGPJT5jm848MRIfNfHUVJeTBdKKcFLax5g38=",
```

## 12. init con el archivo de bloqueo presente · salida real

```console
$ terraform init
- Reusing previous version of kreuzwerker/docker from the
  dependency lock file
- Using previously-installed kreuzwerker/docker v3.9.0
```

## 13. el codigo contra el bloqueo · salida real

```console
$ terraform init
Error: Failed to query available provider packages
locked provider registry.terraform.io/kreuzwerker/docker 3.9.0
does not match configured version constraint ~> 2.0; must use
terraform init -upgrade to allow selection of new versions
```

## 14. init -upgrade en las dos direcciones · salida real

```console
$ terraform init -upgrade      # version = "~> 3.6.0"
- Installed kreuzwerker/docker v3.6.2
  version = "3.6.2"
$ terraform init -upgrade      # version = "~> 3.0"
- Installed kreuzwerker/docker v3.9.0
  version = "3.9.0"
```

## 15. el material del curso

```console
06-modulos/salida-06-modulos.txt
06-modulos/salida-06-imagen-compartida.txt
06-modulos/salida-06-lock.txt
06-modulos/salida-06-upgrade.txt
```
