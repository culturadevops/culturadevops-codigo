# DynamoDB desde Python: por qué rechaza 19,99 y cómo se arregla — lo que sale en pantalla

Comandos y salidas **tal y como salen en las terminales del vídeo**, en el mismo orden.
Se sacaron automáticamente del guion del vídeo; no se escribió nada de memoria.
Las líneas con `$` son lo que tecleas; el resto es la salida que se midió al grabarlo
(tus hashes, tiempos e IDs van a ser otros).

## 1. la forma de bajo nivel

```console
cliente.put_item(
    TableName="art",
    Item={
        "id":     {"S": "2"},
        "precio": {"N": "19.99"}})

# fijate: el numero va como TEXTO
```

## 2. la forma de alto nivel

```console
recurso = sesion.resource("dynamodb")
tabla = recurso.Table("art")

tabla.put_item(
    Item={"id": "1",
          "precio": 19.99})
```

## 3. y esto es lo que contesta

```console
$ python ddb.py

TypeError: Float types are not
supported. Use Decimal types
instead.
```

## 4. el arreglo, y funciona

```console
from decimal import Decimal

tabla.put_item(
    Item={"id": "1",
          "precio": Decimal("19.99")})

guardado
```

## 5. lo que devuelve al leerlo

```console
item = tabla.get_item(Key={"id": "1"})["Item"]
print(item)

{'precio': Decimal('19.99'), 'id': '1'}

# tipo: Decimal
```

## 6. consultar por la clave

```console
from boto3.dynamodb.conditions import Key

r = tabla.query(
    KeyConditionExpression=Key("cliente")
                           .eq("ana"))

for item in r["Items"]:
    print(item["fecha"])
```

## 7. un rango, desde código

```console
r = tabla.query(
    KeyConditionExpression=
        Key("cliente").eq("ana")
        & Key("fecha").between(
            "2026-02-01", "2026-12-31"))
```

## 8. recorrer todo, sin dejarse nada

```console
p = cliente.get_paginator("query")

for pagina in p.paginate(TableName="pedidos",
                         ...):
    for item in pagina["Items"]:
        procesar(item)
```

## 9. guardar solo si no existe

```console
from botocore.exceptions import ClientError

try:
    tabla.put_item(
        Item={"id": "1", ...},
        ConditionExpression=
            "attribute_not_exists(id)")
except ClientError as e:
    print("ya existia")
```

## 10. sumar sin leer antes

```console
tabla.update_item(
    Key={"pagina": "/"},
    UpdateExpression="ADD contador :u",
    ExpressionAttributeValues={
        ":u": 1},
    ReturnValues="UPDATED_NEW")
```

## 11. escribir por lotes sin pensarlo

```console
with tabla.batch_writer() as lote:
    for i in range(5000):
        lote.put_item(
            Item={"id": str(i),
                  "dato": "x"})

# el agrupa y manda por su cuenta
```
