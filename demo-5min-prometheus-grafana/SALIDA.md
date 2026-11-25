# SALIDA — Prometheus y Grafana en 5 minutos (cultura-devops)

Generado 2026-10-23 12:34 UTC con `python correr.py`. Imágenes `prom/prometheus:v3.15.1` y `grafana/grafana:13.2.4`; red de Docker propia; cliente curl+jq en Alpine.

## 1 · La configuración

### prometheus.yml

```
global:
  scrape_interval: 5s
  evaluation_interval: 5s
rule_files: [/etc/prometheus/reglas.yml]
scrape_configs:
  - job_name: prometheus
    static_configs: [{targets: ["localhost:9090"]}]
  - job_name: grafana
    static_configs: [{targets: ["grafana:3000"]}]
  - job_name: pagos
    static_configs: [{targets: ["pagos:8080"]}]
```

### reglas.yml

```
groups:
  - name: basicas
    rules:
      - alert: ServicioCaido
        expr: up == 0
        for: 20s
        labels: {severidad: critica}
        annotations: {resumen: "{{ $labels.job }} no responde"}
```

## 2 · Los objetivos

### ¿quién responde?

`$ curl -s prometheus:9090/api/v1/targets | jq …`

```
grafana	up	
pagos	down	Get "http://pagos:8080/metrics": context deadline exceeded
prometheus	up
```
(código de salida 0)

### PromQL: up

`$ curl -s 'prometheus:9090/api/v1/query?query=up' | jq …`

```
up{job="grafana"} = 1
up{job="pagos"} = 0
up{job="prometheus"} = 1
```
(código de salida 0)

## 3 · La alerta

### pending → firing (sondeando /api/v1/alerts cada segundo)

`$ curl -s prometheus:9090/api/v1/alerts | jq …`

```
t+ 21.6s desde el arranque · ServicioCaido pagos pending
t+ 46.7s desde el arranque · ServicioCaido pagos firing
```

## 4 · Grafana

### salud

`$ curl -s grafana:3000/api/health`

```
{"database":"ok","version":"13.2.4"}
```
(código de salida 0)

### la fuente de datos (aprovisionada por archivo)

`$ curl -s -u admin:admin grafana:3000/api/datasources | jq …`

```
Prometheus	prometheus	http://prometheus:9090
```
(código de salida 0)

### la misma consulta, a través de Grafana

`$ curl -s -u admin:admin -X POST grafana:3000/api/ds/query -d '{…expr: up…}' | jq …`

```
grafana = 1
pagos = 0
prometheus = 1
```
(código de salida 0)
