# Un panel de Grafana que vale para todos tus servicios — lo que sale en pantalla

Comandos y salidas **tal y como salen en las terminales del vídeo**, en el mismo orden.
Se sacaron automáticamente del guion del vídeo; no se escribió nada de memoria.
Las líneas con `$` son lo que tecleas; el resto es la salida que se midió al grabarlo
(tus hashes, tiempos e IDs van a ser otros).

## 1. la consulta, antes y después

```console
# antes: la ruta escrita a mano
rate(tienda_peticiones_total{ruta="/pedido"}[5m])

# despues: la ruta la elige quien mira
rate(tienda_peticiones_total{ruta="$ruta"}[5m])
```

## 2. las opciones se preguntan

```console
label_values(tienda_peticiones_total, ruta)

# devuelve, ahora mismo:
  /pedido
  /buscar
```

## 3. varios valores en la misma consulta

```console
# con la variable en modo multiple:
rate(tienda_peticiones_total{ruta=~"$ruta"}[5m])

#            fijate en el =~
# eso acepta /pedido|/buscar de golpe
```
