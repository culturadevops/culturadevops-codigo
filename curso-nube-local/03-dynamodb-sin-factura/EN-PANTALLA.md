# DynamoDB sin factura: Query y Scan parecen iguales con 3 filas (curso 3/8) — lo que sale en pantalla

Comandos y salidas **tal y como salen en las terminales del vídeo**, en el mismo orden.
Se sacaron automáticamente del guion del vídeo; no se escribió nada de memoria.
Las líneas con `$` son lo que tecleas; el resto es la salida que se midió al grabarlo
(tus hashes, tiempos e IDs van a ser otros).

## 1. S3 · el metodo y la ruta lo dicen todo

```console
GET     /fotos/gato.txt         -> traeme el objeto
PUT     /fotos/gato.txt         -> guardalo
DELETE  /fotos/gato.txt         -> borralo
HEAD    /fotos                  -> existe el bucket?
```

## 2. DynamoDB · SIEMPRE post a la raiz

```console
POST /  HTTP/1.1
X-Amz-Target: DynamoDB_20120810.PutItem
Content-Type: application/x-amz-json-1.0

{"TableName":"pedidos","Item":{...}}
```

## 3. crear la tabla · salida real

```console
$ aws ... dynamodb create-table --table-name pedidos \
$    --key-schema AttributeName=cliente,KeyType=HASH \
$                AttributeName=fecha,KeyType=RANGE \
$    --billing-mode PAY_PER_REQUEST
pedidos
```

## 4. tres pedidos, dos estanterias

```console
ana   · 2026-01-03 · 42,5
ana   · 2026-02-11 · 17
luis  · 2026-01-20 · 99
```

## 5. Query · salida real

```console
$ aws ... dynamodb query --table-name pedidos \
$    --key-condition-expression 'cliente = :c' \
$    --expression-attribute-values '{":c":{"S":"ana"}}'
[
    "2026-01-03",
    "2026-02-11"
]
```

## 6. un tramo de la estanteria · salida real

```console
$ ... 'cliente = :c AND begins_with(fecha, :f)'
$ ... '{":c":{"S":"ana"},":f":{"S":"2026-01"}}'
1
```

## 7. Scan · salida real

```console
$ aws ... dynamodb scan --table-name pedidos --select COUNT
3
```

## 8. como viaja de verdad un elemento

```console
{
  "cliente": {"S": "ana"},
  "fecha":   {"S": "2026-01-03"},
  "total":   {"N": "42.5"}
}
```

## 9. el material del curso

```console
aws-cli/2.36.19  ·  la oficial de Amazon
nubecita:curso   ·  10,5 MB en disco
corrida: 2026-09-03 · salida-real.txt
```
