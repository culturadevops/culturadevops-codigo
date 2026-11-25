# Levanta Prometheus, Loki y Grafana con un compose (y compruébalos) — lo que sale en pantalla

Comandos y salidas **tal y como salen en las terminales del vídeo**, en el mismo orden.
Se sacaron automáticamente del guion del vídeo; no se escribió nada de memoria.
Las líneas con `$` son lo que tecleas; el resto es la salida que se midió al grabarlo
(tus hashes, tiempos e IDs van a ser otros).

## 1. docker-compose.yml

```console
services:
  prometheus:
    image: prom/prometheus:v3.1.0
    ports: ["9090:9090"]
  loki:
    image: grafana/loki:3.3.2
    ports: ["3100:3100"]
  grafana:
    image: grafana/grafana:11.4.0
    ports: ["3001:3000"]
```

## 2. lo que dijo Docker

```console
$ docker compose up -d

Error response from daemon:
ports are not available

bind: Solo se permite un uso de cada
direccion de socket
```

## 3. lo que contestaba el 3000

```console
$ curl localhost:3000/api/health

{"statusCode":404,
 "message":"The requested path
  (C:\Users\tu-usuario\AppData\...)"}
```

## 4. quién está de verdad levantado

```console
$ docker ps

obs-prometheus   Up   9090->9090
obs-loki         Up   3100->3100

# obs-grafana no esta. Ahi estaba el fallo.
```

## 5. Loki, a los 6 segundos

```console
$ curl localhost:3100/ready

HTTP 503
Ingester not ready: waiting for 15s
after being ready
```

## 6. las tres direcciones de salud

```console
$ curl localhost:9090/-/ready
Prometheus Server is Ready.

$ curl localhost:3001/api/health
{"database": "ok", "version": "11.4.0"}

$ curl localhost:3100/ready
ready
```
