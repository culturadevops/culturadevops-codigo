# Métricas o logs: por qué necesitas los dos (con un fallo real) — lo que sale en pantalla

Comandos y salidas **tal y como salen en las terminales del vídeo**, en el mismo orden.
Se sacaron automáticamente del guion del vídeo; no se escribió nada de memoria.
Las líneas con `$` son lo que tecleas; el resto es la salida que se midió al grabarlo
(tus hashes, tiempos e IDs van a ser otros).

## 1. lo que la tienda publica de sí misma

```console
$ curl localhost:8000/metrics

tienda_peticiones_total{codigo="200"} 57
tienda_peticiones_total{codigo="500"} 12
```

## 2. la línea que sí lo explica

```console
09:50:45
{"msg": "no se pudo calcular el impuesto:
        pais sin tarifa",
 "pais": "XX"}
```

## 3. una petición sana, para comparar

```console
09:50:43
{"msg": "pedido ok",
 "pais": "FR", "total": 120.0}
```
