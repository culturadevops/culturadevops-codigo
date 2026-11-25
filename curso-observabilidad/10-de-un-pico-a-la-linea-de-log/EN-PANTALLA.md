# De un pico en la gráfica a la línea de log que lo explica — lo que sale en pantalla

Comandos y salidas **tal y como salen en las terminales del vídeo**, en el mismo orden.
Se sacaron automáticamente del guion del vídeo; no se escribió nada de memoria.
Las líneas con `$` son lo que tecleas; el resto es la salida que se midió al grabarlo
(tus hashes, tiempos e IDs van a ser otros).

## 1. paso 1 · dónde está el pico

```console
sum(rate(tienda_peticiones_total{codigo="500"}[2m]))

pico: 0,238 errores/s
a las 10:58:49
```

## 2. paso 2 · los logs de ese instante

```console
{app="tienda", nivel="error"}
desde 10:58:19  hasta 10:59:19

# sin buscar ninguna palabra
```

## 3. paso 3 · la causa

```console
10:58:25  no se pudo calcular el impuesto:
          pais sin tarifa · pais XX
10:58:26  ... pais XX
10:58:29  ... pais XX
10:58:51  ... pais XX
```
