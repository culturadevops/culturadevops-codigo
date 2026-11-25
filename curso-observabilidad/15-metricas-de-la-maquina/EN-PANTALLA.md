# Métricas de la máquina sin tocar tu código: node_exporter — lo que sale en pantalla

Comandos y salidas **tal y como salen en las terminales del vídeo**, en el mismo orden.
Se sacaron automáticamente del guion del vídeo; no se escribió nada de memoria.
Las líneas con `$` son lo que tecleas; el resto es la salida que se midió al grabarlo
(tus hashes, tiempos e IDs van a ser otros).

## 1. seis líneas en el compose

```console
  node-exporter:
    image: prom/node-exporter:v1.8.2
    ports: ["9100:9100"]

# y un objetivo mas en prometheus.yml
```

## 2. las cuatro que se miran

```console
memoria disponible   14,15 GB
carga de 1 minuto     0,01
nucleos              24
procesador usado     77,2 %
```

## 3. la alerta que predice

```console
predict_linear(
  node_filesystem_avail_bytes[6h],
  4 * 3600)  < 0

# se llena en menos de 4 horas
```

## 4. lo que me dijo Docker

```console
$ docker compose up -d

Error response from daemon:
path / is mounted on / but it is
not a shared or slave mount
```
