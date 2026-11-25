# Alertmanager: agrupar y silenciar sin recibir cien correos — lo que sale en pantalla

Comandos y salidas **tal y como salen en las terminales del vídeo**, en el mismo orden.
Se sacaron automáticamente del guion del vídeo; no se escribió nada de memoria.
Las líneas con `$` son lo que tecleas; el resto es la salida que se midió al grabarlo
(tus hashes, tiempos e IDs van a ser otros).

## 1. las dos piezas de configuración

```console
# en prometheus.yml:
alerting:
  alertmanagers:
    - static_configs:
        - targets: ["alertmanager:9093"]
```

## 2. disparadas aquí, cero allí

```console
Prometheus:
  ErroresAltos        firing
  ErroresAltosSinFor  firing

Alertmanager:
  0 alertas
```

## 3. antes y después de recargar

```console
$ curl localhost:9090/api/v1/alertmanagers
  activos: []

$ curl -X POST localhost:9090/-/reload

$ curl localhost:9090/api/v1/alertmanagers
  activo: http://alertmanager:9093
```

## 4. lo que recibió el receptor

```console
11:32:58  1 alerta en un solo mensaje
          [ErroresAltos]

11:32:58  1 alerta en un solo mensaje
          [ErroresAltosSinFor]
```

## 5. la línea que agrupa

```console
route:
  group_by: [alertname]
  group_wait: 10s
  group_interval: 30s
  repeat_interval: 1h
```
