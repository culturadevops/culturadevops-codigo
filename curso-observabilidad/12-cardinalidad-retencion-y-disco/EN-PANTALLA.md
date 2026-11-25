# Cardinalidad: metí una etiqueta y generé 78.000 series en un día — lo que sale en pantalla

Comandos y salidas **tal y como salen en las terminales del vídeo**, en el mismo orden.
Se sacaron automáticamente del guion del vídeo; no se escribió nada de memoria.
Las líneas con `$` son lo que tecleas; el resto es la salida que se midió al grabarlo
(tus hashes, tiempos e IDs van a ser otros).

## 1. el cambio que lo rompe

```console
# antes:
tienda_peticiones_total{ruta="/pedido",codigo="200"}

# despues:
tienda_peticiones_total{ruta="/pedido",codigo="200",
                        pedido="164580297"}
```

## 2. y sigue subiendo

```console
  0 s   142 series
 45 s   182 series
 90 s   223 series
135 s   264 series
180 s   305 series
```

## 3. quién genera las series

```console
$ curl localhost:9090/api/v1/status/tsdb

job=prometheus                786
job=tienda                    129

# la tienda paso de 13 a 129
```
