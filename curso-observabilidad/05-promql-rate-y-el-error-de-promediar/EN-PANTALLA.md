# PromQL: rate, sum by y el error de promediar promedios — lo que sale en pantalla

Comandos y salidas **tal y como salen en las terminales del vídeo**, en el mismo orden.
Se sacaron automáticamente del guion del vídeo; no se escribió nada de memoria.
Las líneas con `$` son lo que tecleas; el resto es la salida que se midió al grabarlo
(tus hashes, tiempos e IDs van a ser otros).

## 1. de un contador a un ritmo

```console
# el contador, en bruto: no dice nada
tienda_peticiones_total   ->  315

# el ritmo: esto sí
rate(tienda_peticiones_total[5m])
```

## 2. juntar por lo que te interesa

```console
# todo junto:
sum(rate(tienda_peticiones_total[5m]))

# agrupado por codigo de respuesta:
sum by (codigo) (
  rate(tienda_peticiones_total[5m]))
```

## 3. el porcentaje de fallo

```console
sum(rate(tienda_peticiones_total{codigo="500"}[5m]))
/
sum(rate(tienda_peticiones_total[5m]))
* 100
```

## 4. lo que hay en mi tienda

```console
ruta      peticiones   media
/pedido      285      0,0311 s
/buscar       30      2,1520 s
```

## 5. las dos consultas

```console
# A: sumar todo y dividir una vez
sum(suma_segundos) / sum(cuenta)

# B: la media de cada ruta, promediada
avg(suma_segundos / cuenta)
```

## 6. el percentil, bien calculado

```console
histogram_quantile(0.95,
  sum by (le) (
    rate(duracion_bucket[5m])))

# el percentil 95 de TODAS tus copias
```
