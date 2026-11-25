# SALIDA — Terraform en 5 minutos (cultura-devops)

> Corrida del 2026-10-19 17:13 en hashicorp/terraform:1.16.6, proveedor hashicorp/local 2.5.3.

```
$ terraform version
Terraform v1.16.6

$ terraform init
- Installing hashicorp/local v2.5.3...
- Installed hashicorp/local v2.5.3 (signed by HashiCorp)
Terraform has been successfully initialized!

$ terraform plan
  # local_file.config will be created
      + filename             = "./salida/app-pruebas.conf"
Plan: 1 to add, 0 to change, 0 to destroy.

$ terraform apply -auto-approve
  + archivo = "./salida/app-pruebas.conf"
local_file.config: Creating...
local_file.config: Creation complete after 0s [id=06cd303a8c568abc47c1421e835cd871a05deba5]
Apply complete! Resources: 1 added, 0 changed, 0 destroyed.
archivo = "./salida/app-pruebas.conf"
$ cat salida/app-pruebas.conf
entorno = pruebas
replicas = 2

$ terraform plan   # sin cambiar nada
No changes. Your infrastructure matches the configuration.

$ terraform plan -var entorno=produccion
  # local_file.config must be replaced
      ~ content              = <<-EOT # forces replacement
      ~ filename             = "./salida/app-pruebas.conf" -> "./salida/app-produccion.conf" # forces replacement
Plan: 1 to add, 0 to change, 1 to destroy.

$ terraform destroy -auto-approve
local_file.config: Destroying... [id=06cd303a8c568abc47c1421e835cd871a05deba5]
local_file.config: Destruction complete after 0s
Destroy complete! Resources: 1 destroyed.
$ ls salida/
```
