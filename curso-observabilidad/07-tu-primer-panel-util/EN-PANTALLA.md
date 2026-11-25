# Tu primer panel de Grafana que sirve para algo a las 3 de la mañana — lo que sale en pantalla

Comandos y salidas **tal y como salen en las terminales del vídeo**, en el mismo orden.
Se sacaron automáticamente del guion del vídeo; no se escribió nada de memoria.
Las líneas con `$` son lo que tecleas; el resto es la salida que se midió al grabarlo
(tus hashes, tiempos e IDs van a ser otros).

## 1. las dos direcciones

```console
# tu navegador entra por:
  http://localhost:9090

# pero Grafana tiene que poner:
  http://prometheus:9090
```

## 2. la consulta del panel inútil

```console
rate(tienda_peticiones_total[5m])

# una linea por ruta Y por codigo
# sin unidades, sin umbral
```

## 3. mi panel, con datos reales de ahora

```console
peticiones por segundo   0,333
porcentaje de fallo     14,177 %
latencia media           0,256 s
```
