# SALIDA extra — Azure en local (vídeo 409)

Generado 2026-10-13 21:02 UTC con `python correr_extra.py`.

## 1 · El linter de Bicep

### un parámetro que nadie usa

`$ az bicep lint --file fija.bicep`

```
WARNING: /work/fija.bicep(1,7) : Warning no-unused-params: Parameter "entorno" is declared but never used. [https://aka.ms/bicep/linter-diagnostics#no-unused-params]
```
(código de salida 0)

## 2 · De ARM a Bicep

### la plantilla JSON

`$ wc -l plantilla.json`

```
22 plantilla.json
```
(código de salida 0)

### decompilarla

`$ az bicep decompile --file plantilla.json; cat plantilla.bicep`

```
resource tiendafotos2027 'Microsoft.Storage/storageAccounts@2023-05-01' = {
  name: 'tiendafotos2027'
  location: resourceGroup().location
  sku: {
    name: 'Standard_LRS'
  }
  kind: 'StorageV2'
}
8 plantilla.bicep
```
(código de salida 0)

## 3 · Un blob privado y un SAS de solo lectura (Azurite)

### leerlo sin permiso

`$ curl -s -o /dev/null -w '%{http_code}' http://azurite:10000/devstoreaccount1/fotos/foto.txt`

```
403
```
(código de salida 0)

### el SAS: solo lectura, caduca en una hora

`$ az storage blob generate-sas --permissions r --expiry …`

```
se=2026-10-13T22%3A02Z
sp=r
sv=2026-04-06
sr=b
sig=mBmmegRh…
```
(código de salida 0)

### leerlo con el SAS

`$ curl -s "http://azurite:10000/devstoreaccount1/fotos/foto.txt?$SAS"`

```
hola desde azurite
```
(código de salida 0)

### intentar escribir con el mismo SAS

`$ curl -s -X PUT -H 'x-ms-blob-type: BlockBlob' -d otro "http://azurite:10000/devstoreaccount1/fotos/foto.txt?$SAS"`

```
403
hola desde azurite
```
(código de salida 0)
