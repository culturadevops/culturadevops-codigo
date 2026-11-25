# Salida ejecutada — vídeo 216 «Escribí DynamoDB en Python»

> Corrida del 2026-09-07. Servidor: `dynamo_py.py` en `python:3.12-alpine`, solo biblioteca estándar.
> Cliente: **boto3 OFICIAL**, en otro contenedor, por red de Docker.

```
=== boto3 OFICIAL contra un DynamoDB escrito en Python ===
  boto3 1.43.89

--- create_table -> ok (cliente = partición, pedido = ordenación)
  put_item        -> ok
  get_item        -> {'cliente': 'ana', 'pedido': 'p1', 'total': Decimal('19.99')}

--- 1 · POR QUÉ RECHAZA 19,99 SI LO MANDAS COMO FLOAT ---
  boto3 se niega ANTES de salir a la red:
    Float types are not supported. Use Decimal types instead.
  y por el cable los números viajan como CADENA. Míralo en crudo:
    {'cliente': {'S': 'ana'}, 'pedido': {'S': 'p1'}, 'total': {'N': '19.99'}}
    ^ {'N': '19.99'} — texto. Un float ya trae el error de coma flotante metido,
      así que el protocolo transporta la cifra tal cual la escribiste.

--- 2 · QUERY Y SCAN NO SON LA MISMA OPERACIÓN ---
  metidos 1.000 items (200 clientes x 5 pedidos)

  query('c042') -> 5 items · 49.7 ms
  scan (mismo)  -> 5 items · 48.4 ms

  ITEMS QUE TOCÓ EL SERVIDOR POR DENTRO:
     Query -> 5   (solo su partición)
     Scan  -> 1001   (la tabla entera)
     ^ mismo resultado, mismo filtro, y uno leyó 5 y el otro 1.000.
       Con 3 filas parecen iguales. Ese es el vídeo.

--- 3 · el FilterExpression NO ahorra lectura ---
  scan devolvió Count=5 pero ScannedCount=1001
  ^ te cobran por lo escaneado, no por lo devuelto.
```

### 🥇 Lo que sostiene el vídeo 216

**Query y Scan no son la misma operación optimizada.** Mismo filtro, mismo resultado —5 items— y
por dentro uno leyó **5** y el otro **1.001**. Con tres filas parecen iguales; con el contador
delante, no lo son.

Y el corolario que se paga en la factura: `Count=5` pero `ScannedCount=1001`. **Te cobran por lo
escaneado, no por lo devuelto**, porque el `FilterExpression` se aplica DESPUÉS de leer.

**Por qué rechaza 19,99.** boto3 se niega antes de salir a la red —*«Float types are not
supported. Use Decimal types instead»*— y por el cable se ve el motivo: `{'N': '19.99'}`, texto.
Un float ya trae el error de coma flotante metido, así que el protocolo transporta la cifra tal
cual la escribiste.

### 🐛 El fallo que boto3 destapó, y que se cuenta en el vídeo

Primera versión: el `Scan` con filtro devolvía **0 items**, sin ningún error.

El motivo es que boto3 **no manda `cliente = :v0`**. Manda `#n0 = :v0` y aparte un diccionario
`ExpressionAttributeNames` con `{"#n0": "cliente"}`, para que los nombres de campo no choquen con
las palabras reservadas de DynamoDB. Si no resuelves el alias, el filtro no encuentra nada y el
Scan devuelve cero tan tranquilo.

Es la misma clase de fallo que el `ContentLength` del S3: aparece solo cuando enchufas el cliente
de verdad. Corregido el 2026-09-07 con boto3 1.43.89.
