# SALIDA — Azure en local (vídeo 409)

Generado 2026-10-13 20:40 UTC con `python correr.py`. Sin cuenta de Azure: CLI oficial, Bicep y el emulador Azurite, todo en Docker.

## 1 · La CLI oficial, en un contenedor

### versión

`$ az version`

```
Azure-cli    Azure-cli-core    Azure-cli-telemetry
-----------  ----------------  ---------------------
2.89.1       2.89.1            1.1.0
```
(código de salida 0)

## 2 · Bicep: lo que escribes y lo que Azure recibe

### instalar Bicep

`$ az bicep install; az bicep version`

```
Bicep CLI version 0.48.1 (cec7951cf6)
```
(código de salida 0)

### el fichero Bicep

`$ cat tienda.bicep; wc -l tienda.bicep`

```
param location string = resourceGroup().location
param nombre string = 'tiendafotos${uniqueString(resourceGroup().id)}'

resource cuenta 'Microsoft.Storage/storageAccounts@2023-05-01' = {
  name: nombre
  location: location
  sku: { name: 'Standard_LRS' }
  kind: 'StorageV2'
  properties: {
    minimumTlsVersion: 'TLS1_2'
    allowBlobPublicAccess: false
  }
}

output id string = cuenta.id
15 tienda.bicep
```
(código de salida 0)

### compilarlo a la plantilla ARM

`$ az bicep build --file tienda.bicep; wc -l tienda.json`

```
42 tienda.json
{
  "$schema": "https://schema.management.azure.com/schemas/2019-04-01/deploymentTemplate.json#",
  "contentVersion": "1.0.0.0",
  "metadata": {
    "_generator": {
      "name": "bicep",
      "version": "0.48.1.52935",
      "templateHash": "3618861106705053660"
    }
  },
  "parameters": {
    "location": {
      "type": "string",
      "defaultValue": "[resourceGroup().location]"
    },
    "nombre": {
      "type": "string",
      "defaultValue": "[format('tiendafotos{0}', uniqueString(resourceGroup().id))]"
    }
  },
  "resources": [
    {
      "type": "Microsoft.Storage/storageAccount
```
(código de salida 0)

### un error lo detecta al compilar

`$ (nombre mal escrito) az bicep build`

```
ERROR: /work/roto.bicep(15,27) : Error BCP053: The type "Microsoft.Storage/storageAccounts" does not contain property "idd". Available properties include "apiVersion", "asserts", "eTag", "extendedLocation", "id", "identity", "kind", "location", "managedBy", "managedByExtended", "name", "placement", "plan", "properties", "scale", "sku", "tags", "type", "zones". [https://aka.ms/bicep/core-diagnostics#BCP053]
```
(código de salida 0)

## 3 · Azure Storage en local con Azurite

### crear un contenedor

`$ az storage container create -n fotos --connection-string …`

```
{
  "created": true
}
```
(código de salida 0)

### subir un blob

`$ az storage blob upload -c fotos -n foto.txt -f foto.txt …`

```
subido

Alive[################################################################]  100.0000%
Finished[#############################################################]  100.0000%
```
(código de salida 0)

### listarlo

`$ az storage blob list -c fotos -o table …`

```
Nombre    Bytes
--------  -------
foto.txt  19
```
(código de salida 0)

### descargarlo

`$ az storage blob download -c fotos -n foto.txt -f copia.txt …`

```
hola desde azurite

Alive[################################################################]  100.0000%
Finished[#############################################################]  100.0000%
```
(código de salida 0)

## 4 · Lo que pesa la herramienta

### tamaño de las imágenes

`$ docker image inspect -f {{.Size}}`

```
mcr.microsoft.com/azure-cli 143206691
mcr.microsoft.com/azure-storage/azurite 111436552
```
(código de salida 0)
