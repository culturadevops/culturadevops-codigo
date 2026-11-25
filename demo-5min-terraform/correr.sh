#!/bin/sh
# Corre DENTRO de hashicorp/terraform:1.16.6 (lo lanza ejecutar.sh). Salida literal → SALIDA.md.
set -u
rm -rf /w && mkdir -p /w && cp /trabajo/main.tf /w/ && cd /w
export TF_IN_AUTOMATION=1 NO_COLOR=1
echo "\$ terraform version"
terraform version | head -1
echo
echo "\$ terraform init"
terraform init -no-color 2>&1 | grep -E "Installing|Installed|initialized"
echo
echo "\$ terraform plan"
terraform plan -no-color 2>&1 | grep -E "will be created|filename|Plan:"
echo
echo "\$ terraform apply -auto-approve"
terraform apply -auto-approve -no-color 2>&1 | grep -E "Creating|Creation complete|Apply complete|archivo ="
echo "\$ cat salida/app-pruebas.conf"
cat salida/app-pruebas.conf
echo
echo "\$ terraform plan   # sin cambiar nada"
terraform plan -no-color 2>&1 | grep -E "No changes|Plan:"
echo
echo "\$ terraform plan -var entorno=produccion"
terraform plan -no-color -var entorno=produccion 2>&1 | grep -E "must be replaced|forces replacement|Plan:"
echo
echo "\$ terraform destroy -auto-approve"
terraform destroy -auto-approve -no-color 2>&1 | grep -E "Destroying|Destruction complete|Destroy complete"
echo "\$ ls salida/"
ls salida/ 2>&1
