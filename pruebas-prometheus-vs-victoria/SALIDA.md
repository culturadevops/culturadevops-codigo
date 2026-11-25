# SALIDA — Prometheus vs VictoriaMetrics (vídeo 337)

Generado 2026-10-08 00:12 UTC con `python correr.py`. Prometheus 3.15.0 y VictoriaMetrics v1.153.0, 6 min raspando 3 node-exporter cada 5 s.

## 1 · Los dos, la misma configuración de scrape

### prometheus.yml (lo usan los dos)

`$ cat prometheus.yml`

```
global:
  scrape_interval: 5s
scrape_configs:
  - job_name: nodos
    static_configs:
      - targets: ['nodo1:9100', 'nodo2:9100', 'nodo3:9100']
```

### versiones

`$ --version`

```
prometheus, version 3.15.0 (branch: HEAD, revision: 5241a27fe3c6983549fccc32f6e65917408c63cd)
victoria-metrics-20260925-135025-tags-v1.153.0-0-g3acd30be34
```

### arranque

`$ docker ps`

```
vm  victoriametrics/victoria-metrics:latest
prom  prom/prometheus:latest
nodo3  prom/node-exporter:latest
nodo2  prom/node-exporter:latest
nodo1  prom/node-exporter:latest
```

## 2 · Ingesta durante 6 minutos

### series activas (el mismo PromQL)

`$ count({__name__!=""})`

```
Prometheus:      3156
VictoriaMetrics: 3162
```

## 3 · Memoria y disco con los mismos datos

### memoria

`$ docker stats --no-stream`

```
prom 34.86MiB / 15.36GiB
vm 222.4MiB / 15.36GiB
```

### disco

`$ du -sh del directorio de datos`

```
Prometheus: 1.5M
VictoriaMetrics: 828.0K
```

## 4 · Las mismas consultas PromQL

### mismas consultas, los dos

`$ GET /api/v1/query?query=…  (el mismo endpoint)`

```
consulta                         Prometheus            VictoriaMetrics
up de los nodos                  3                     3
memoria libre media (bytes)      12385013760           12413982037.333334
tasa de CPU, 1m (núcleo-seg/s)   72.33464049539668     72.33616666666661
```

### ¿VictoriaMetrics habla el idioma de Prometheus?

`$ GET /api/v1/query en :8428`

```
sí: el mismo endpoint /api/v1/query y el mismo PromQL (más su extensión MetricsQL)
```

## 5 · Compresión: bytes por muestra

### bytes por muestra (orientativo)

`$ disco / muestras`

```
Prometheus y VM comprimen distinto; VM suele ocupar bastante menos por muestra.
Ver disco (sección 3) contra muestras (sección 2).
```
