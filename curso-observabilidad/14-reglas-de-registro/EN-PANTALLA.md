# Reglas de registro: precalcular lo que sale caro en Prometheus — lo que sale en pantalla

Comandos y salidas **tal y como salen en las terminales del vídeo**, en el mismo orden.
Se sacaron automáticamente del guion del vídeo; no se escribió nada de memoria.
Las líneas con `$` son lo que tecleas; el resto es la salida que se midió al grabarlo
(tus hashes, tiempos e IDs van a ser otros).

## 1. la consulta cara

```console
sum(rate(tienda_latencia_suma_segundos[5m]))
/
sum(rate(tienda_latencia_cuenta[5m]))
```

## 2. la regla

```console
groups:
  - name: precalculado
    interval: 15s
    rules:
      - record: tienda:latencia_media:5m
        expr: sum(rate(...)) / sum(rate(...))
```

## 3. cómo se nombran

```console
tienda:latencia_media:5m
  ^      ^             ^
  nivel  que mide      ventana

tienda:fallo_porcentaje:5m
```
