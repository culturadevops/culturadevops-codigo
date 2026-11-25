# Azure Fundamentals 2: arquitectura y servicios, funcionando (AZ-900) — lo que sale en pantalla

Comandos y salidas **tal y como salen en las terminales del vídeo**, en el mismo orden.
Se sacaron automáticamente del guion del vídeo; no se escribió nada de memoria.
Las líneas con `$` son lo que tecleas; el resto es la salida que se midió al grabarlo
(tus hashes, tiempos e IDs van a ser otros).

## 1. en mi máquina · lista pública de precios

```console
Este de EE. UU.     30,37 USD/mes
Europa Occidental   35,04 USD/mes
Brasil Sur          49,06 USD/mes
```

## 2. de la documentación oficial

```console
"id": "/subscriptions/xxxxxxxx-...
          /resourceGroups/myVMResourceGroup
          /providers/Microsoft.Compute
          /virtualMachines/myVM"
```

## 3. de la documentación oficial

```console
$ az vm create -n MyVm \
$   -g MyResourceGroup \
$   --image Ubuntu2204
```

## 4. de la documentación oficial · la respuesta

```console
{
  "location": "eastus",
  "powerState": "VM running",
  "privateIpAddress": "10.0.0.4",
  "publicIpAddress": "52.147.208.85",
  "resourceGroup": "myVMResourceGroup"
}
```

## 5. en mi máquina · lista pública de precios

```console
disco E6 / P6   0,61 USD al mes
disco E10 / P10 1,18 USD al mes

# se pagan esté encendida o apagada
```

## 6. en mi máquina

```console
$ docker run mcr.microsoft.com/azure-storage/azurite

responde tras 12 s
memoria en reposo   83,5 MiB
imagen             532 MB
```

## 7. en mi máquina · el fallo

```console
$ az storage container create --name demo

ErrorCode: InvalidHeaderValue
The API version 2026-04-06 is not
supported by Azurite.
```

## 8. en mi máquina · el arreglo

```console
$ azurite --skipApiVersionCheck

$ az storage container create --name demo
true
```

## 9. en mi máquina

```console
$ az storage blob upload --name prueba.txt
$ az storage blob list --container-name demo

Nombre        Bytes
prueba.txt       26
```

## 10. en mi máquina

```console
$ sqlcmd -Q "SELECT @@VERSION"

Microsoft Azure SQL Edge Developer
(RTM) - 16.0.5100.7245 (X64)
```

## 11. en mi máquina

```console
$ CREATE DATABASE tienda
$ CREATE TABLE pedidos (id INT, importe DECIMAL)
$ SELECT COUNT(*), SUM(importe) FROM pedidos

pedidos     total
      2     65.49
```

## 12. en mi máquina · lista pública de precios

```console
Azure App Service Free Plan
  SKU F1     0.0 USD / 1 Hour
```
