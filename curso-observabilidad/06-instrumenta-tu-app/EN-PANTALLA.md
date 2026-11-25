# Instrumenta tu aplicación sin ninguna biblioteca de métricas — lo que sale en pantalla

Comandos y salidas **tal y como salen en las terminales del vídeo**, en el mismo orden.
Se sacaron automáticamente del guion del vídeo; no se escribió nada de memoria.
Las líneas con `$` son lo que tecleas; el resto es la salida que se midió al grabarlo
(tus hashes, tiempos e IDs van a ser otros).

## 1. el formato entero, en una línea

```console
nombre{etiqueta="valor"} numero

tienda_peticiones_total{codigo="200"} 285
```

## 2. las métricas de la tienda

```console
$ curl localhost:8000/metrics

# HELP tienda_peticiones_total Peticiones atendidas
# TYPE tienda_peticiones_total counter
tienda_peticiones_total{ruta="/buscar",codigo="200"} 30
tienda_peticiones_total{ruta="/pedido",codigo="200"} 285
```

## 3. recogida y confirmada

```console
job      salud   muestras   tardo
tienda   up        3       0,0038 s

up{job="tienda"} = 1
```
