# Cuánto te cuesta cada exportador: mi app son 13 series de 3.586 — lo que sale en pantalla

Comandos y salidas **tal y como salen en las terminales del vídeo**, en el mismo orden.
Se sacaron automáticamente del guion del vídeo; no se escribió nada de memoria.
Las líneas con `$` son lo que tecleas; el resto es la salida que se midió al grabarlo
(tus hashes, tiempos e IDs van a ser otros).

## 1. lo que se añade

```console
  cadvisor:
    image: gcr.io/cadvisor/cadvisor:v0.49.1
    ports: ["8080:8080"]
    privileged: true
    volumes: [ /var/run, /sys, ... ]
```

## 2. lo que publica de verdad

```console
container_memory_usage_bytes
  id="/"            1726 MB
  id="/docker"       340 MB
  id="/restricted"   287 MB

# series con nombre de contenedor: 0
```

## 3. quién ocupa qué

```console
contenedores   1.808 series
maquina        1.036 series
prometheus       718 series
tienda            13 series
               ---------
TOTAL          3.586 series
```

## 4. quedarse con lo que sirve

```console
metric_relabel_configs:
  - source_labels: [__name__]
    regex: 'container_(cpu|memory)_.+'
    action: keep

# de 1.808 series a unas pocas decenas
```
