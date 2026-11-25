# Variables en Terraform: sensitive no esconde tu secreto — lo que sale en pantalla

Comandos y salidas **tal y como salen en las terminales del vídeo**, en el mismo orden.
Se sacaron automáticamente del guion del vídeo; no se escribió nada de memoria.
Las líneas con `$` son lo que tecleas; el resto es la salida que se midió al grabarlo
(tus hashes, tiempos e IDs van a ser otros).

## 1. una variable con tipo

```console
variable "puerto" {
  type        = number
  description = "Puerto de la maquina donde se publica la web"
  default     = 8090
}

    external = var.puerto
```

## 2. un tipo mal puesto · salida real

```console
$ terraform plan -var 'puerto=ochenta'
Error: Invalid value for input variable

Unsuitable value for var.puerto set using -var="puerto=...":
a number is required.
```

## 3. una validacion con tu mensaje

```console
variable "puerto" {
  type = number
  validation {
    condition     = var.puerto >= 1024 && var.puerto <= 65535
    error_message = "El puerto tiene que estar entre 1024 y 65535..."
  }
}
```

## 4. mi mensaje, no el de Terraform · salida real

```console
$ terraform plan -var puerto=80
Error: Invalid value for variable
    | var.puerto is 80
El puerto tiene que estar entre 1024 y 65535: por debajo hacen
falta permisos de administrador.
This was checked by the validation rule at main.tf:12,3-13.
```

## 5. una lista cerrada · salida real

```console
$ terraform plan -var entorno=prod
Error: Invalid value for variable
    | var.entorno is "prod"
entorno solo puede ser dev, pre o pro.
```

## 6. sin valor y sin nadie delante · salida real

```console
$ terraform plan -input=false
Error: No value for required variable
  on main.tf line 27:
  27: variable "clave_bd" {
```

## 7. locals y outputs

```console
locals {
  nombre = "web-${var.entorno}"
}

output "url" {
  value = "http://localhost:${var.puerto}"
}
```

## 8. terraform console · salida real

```console
$ terraform console -var entorno=pre
> local.nombre
"web-pre"
> "http://localhost:${var.puerto}"
"http://localhost:8090"
> upper(var.entorno)
"PRE"
```

## 9. la precedencia, medida · salida real

```console
solo default                   ->  8090
terraform.tfvars               ->  8091
tfvars + TF_VAR_puerto=8092    ->  8091
```

## 10. la precedencia completa · salida real

```console
solo default                   ->  8090
terraform.tfvars               ->  8091
tfvars + TF_VAR_puerto=8092    ->  8091
+ zz.auto.tfvars (8094)        ->  8094
+ -var puerto=8093             ->  8093
```

## 11. el orden en la linea de ordenes · salida real

```console
$ terraform plan -var-file=pro.tfvars -var puerto=8093
  + url = "http://localhost:8093"
$ terraform plan -var puerto=8093 -var-file=pro.tfvars
  + url = "http://localhost:8095"
```

## 12. una variable sensible

```console
variable "clave_bd" {
  type      = string
  sensitive = true
}

  env = ["CLAVE_BD=${var.clave_bd}"]
```

## 13. el plan y el apply · salida real

```console
$ terraform apply -var clave_bd=Sup3rS3creta-2026
      + env = (sensitive value)
Outputs:
clave = <sensitive>
url = "http://localhost:8090"
```

## 14. un output normal que usa la clave · salida real

```console
$ terraform plan
Error: Output refers to sensitive values
  60: output "cadena_conexion" {
Terraform requires that any root module output containing
sensitive data be explicitly marked as sensitive.
```

## 15. la marca se puede quitar · salida real

```console
$ terraform console
> var.clave_bd
(sensitive value)
> nonsensitive(var.clave_bd)
"Sup3rS3creta-2026"
```

## 16. pedir el output por su nombre · salida real

```console
$ terraform output clave
"Sup3rS3creta-2026"
$ terraform output -raw clave
Sup3rS3creta-2026
```

## 17. buscar la clave en el estado · salida real

```console
$ grep -c Sup3rS3creta-2026 terraform.tfstate
2
$ grep -n Sup3rS3creta-2026 terraform.tfstate
8:      "value": "Sup3rS3creta-2026",
54:              "CLAVE_BD=Sup3rS3creta-2026"
```

## 18. y en el propio contenedor · salida real

```console
$ docker inspect web-dev --format '{{range .Config.Env}}...'
CLAVE_BD=Sup3rS3creta-2026
```

## 19. una variable efimera en env · salida real

```console
$ terraform plan -var clave_bd=Sup3rS3creta-2026
Error: Invalid use of ephemeral value
  with docker_container.web,
  44:   env   = ["CLAVE_BD=${var.clave_bd}"]
Ephemeral values are not valid for "env", because it is not a
write-only attribute and must be persisted to state.
```

## 20. el material del curso

```console
04-variables/salida-04-validaciones.txt
04-variables/salida-04-precedencia.txt
04-variables/salida-04-sensitive.txt
04b-efimera/salida-04-efimera.txt
```
