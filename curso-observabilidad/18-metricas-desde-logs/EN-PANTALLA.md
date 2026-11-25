# Métricas a partir de logs, cuando no puedes tocar la aplicación — lo que sale en pantalla

Comandos y salidas **tal y como salen en las terminales del vídeo**, en el mismo orden.
Se sacaron automáticamente del guion del vídeo; no se escribió nada de memoria.
Las líneas con `$` son lo que tecleas; el resto es la salida que se midió al grabarlo
(tus hashes, tiempos e IDs van a ser otros).

## 1. de líneas a métrica

```console
# buscar lineas:
{app="tienda", nivel="error"}

# contarlas por segundo:
sum(rate({app="tienda", nivel="error"}[2m]))
```

## 2. lo que hay que montar

```console
logs -> se cuentan una vez cada 15 s
     -> se guarda como metrica
     -> los paneles consultan esa

# Loki lee los logs una vez, no mil
```
