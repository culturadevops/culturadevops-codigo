# Cómo recoge Prometheus: por qué va a buscar en vez de esperar — lo que sale en pantalla

Comandos y salidas **tal y como salen en las terminales del vídeo**, en el mismo orden.
Se sacaron automáticamente del guion del vídeo; no se escribió nada de memoria.
Las líneas con `$` son lo que tecleas; el resto es la salida que se midió al grabarlo
(tus hashes, tiempos e IDs van a ser otros).

## 1. lo que Prometheus va a buscar

```console
$ curl localhost:8000/metrics

tienda_peticiones_total{codigo="200"} 57
tienda_peticiones_total{codigo="500"} 12
```

## 2. prometheus.yml

```console
global:
  scrape_interval: 15s

scrape_configs:
  - job_name: tienda
    static_configs:
      - targets: ["host.docker.internal:8000"]
```

## 3. recargar sin reiniciar

```console
$ curl -X POST localhost:9090/-/reload

# el objetivo nuevo aparece al momento
# y no se pierde el historico
```

## 4. los tres objetivos

```console
job          salud   muestras
prometheus   up      655
tienda       up        3
fantasma     down      0
```

## 5. el error, completo

```console
fantasma   down

Get "http://host.docker.internal:9999/metrics":
dial tcp 192.168.65.254:9999:
connect: connection refused
```

## 6. la métrica que se inventa él

```console
up{job="prometheus"} = 1
up{job="tienda"}     = 1
up{job="fantasma"}   = 0
```

## 7. las otras dos que apunta solo

```console
cuanto tardo en recoger:
  prometheus  0,0021 s
  tienda      0,0038 s

cuantos datos trajo:
  prometheus  655 muestras
  tienda        3 muestras
```
