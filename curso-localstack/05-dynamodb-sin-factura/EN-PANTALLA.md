# DynamoDB en local: por qué la clave decide lo que podrás preguntar — lo que sale en pantalla

Comandos y salidas **tal y como salen en las terminales del vídeo**, en el mismo orden.
Se sacaron automáticamente del guion del vídeo; no se escribió nada de memoria.
Las líneas con `$` son lo que tecleas; el resto es la salida que se midió al grabarlo
(tus hashes, tiempos e IDs van a ser otros).

## 1. crear la tabla con clave compuesta

```console
$ aws --profile lab dynamodb create-table \
$     --table-name pedidos \
$     --key-schema \
$       AttributeName=cliente,KeyType=HASH \
$       AttributeName=fecha,KeyType=RANGE \
$     --billing-mode PAY_PER_REQUEST

pedidos    ACTIVE
```

## 2. la consulta que sí es barata

```console
$ aws --profile lab dynamodb query \
$     --table-name pedidos \
$     --key-condition-expression "cliente = :c" \
$     --expression-attribute-values \
$       '{":c":{"S":"ana"}}'

2026-01-05    42
2026-03-11    42
2026-07-02    42
```

## 3. un rango de fechas

```console
$ ... --key-condition-expression \
$     "cliente = :c AND fecha BETWEEN :a AND :b"

2026-03-11
2026-07-02
```

## 4. preguntando por algo que no es la clave

```console
$ aws --profile lab dynamodb query \
$     --table-name pedidos \
$     --key-condition-expression "importe = :t"

An error occurred (ValidationException)
Query condition missed key schema
element
```

## 5. el rodeo, con sus dos contadores

```console
$ aws --profile lab dynamodb scan \
$     --table-name pedidos \
$     --filter-expression "importe = :t" \
$     --query '[Count,ScannedCount]'

2    4

# devueltos: 2   ·   leidos: 4
```

## 6. creando el índice por importe

```console
$ aws --profile lab dynamodb update-table \
$     --table-name pedidos \
$     --global-secondary-index-updates \
$       '[{"Create":{"IndexName":"por-importe", ...

por-importe    CREATING
```

## 7. la misma pregunta, por el índice

```console
$ aws --profile lab dynamodb query \
$     --table-name pedidos \
$     --index-name por-importe \
$     --key-condition-expression "importe = :t"

2    2

# devueltos: 2   ·   leidos: 2
```

## 8. una palabra que no puedes usar

```console
$ ... --filter-expression "total = :t"

An error occurred (ValidationException)
Attribute name is a reserved keyword;
reserved keyword: total
```

## 9. guardar solo si no existe

```console
$ aws --profile lab dynamodb put-item \
$     --table-name pedidos \
$     --item '{...}' \
$     --condition-expression \
$       "attribute_not_exists(cliente)"

(ConditionalCheckFailedException)
The conditional request failed
```

## 10. pidiéndole lo que ha consumido

```console
$ aws --profile lab dynamodb query \
$     --table-name pedidos \
$     --key-condition-expression "cliente = :c" \
$     --return-consumed-capacity TOTAL

  "TableName": "pedidos",
  "CapacityUnits": 0.5
```

## 11. un elemento demasiado grande

```console
$ # un elemento de ~500 KB
$ aws --profile lab dynamodb put-item \
$     --table-name pedidos \
$     --item file://gordo.json

An error occurred (ValidationException)
Item size has exceeded the maximum
allowed size
```
