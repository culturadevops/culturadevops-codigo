# SALIDA — Uptime Kuma (vídeo 326)

Generado 2026-10-07 20:58 UTC con `python correr.py`. Imagen louislam/uptime-kuma:2. Intervalo de los monitores: 20 s, sin reintentos.

## 1 · Levantar Uptime Kuma y los servicios a vigilar

### arranque

`$ docker run -d --name kuma -p 3001:3001 louislam/uptime-kuma:2`

```
[36m2026-10-07T20:54:10Z[0m [[32mSERVER[0m] [36mINFO:[0m Uptime Kuma Version: 2.5.5
[36m2026-10-07T20:54:11Z[0m [[38;5;119mMIGRATION[0m] [36mINFO:[0m -  http://localhost:3001
(listo en 1 s)
```

### tamaño de la imagen

`$ docker image inspect louislam/uptime-kuma:2`

```
602 MB
```

## 2 · Cuenta, notificación a ntfy y tres monitores

### configurar por socket.io

`$ python cliente.py setup`

```
setup: {'ok': True, 'msg': 'successAdded', 'msgi18n': True}
login: {'ok': True}
addNotification: {'ok': True, 'msg': 'Saved.', 'msgi18n': True, 'id': 1}
add: Web (HTTP) -> {'ok': True, 'msg': 'successAdded', 'msgi18n': True, 'monitorID': 1}
add: Redis (TCP) -> {'ok': True, 'msg': 'successAdded', 'msgi18n': True, 'monitorID': 2}
add: DNS de web -> {'ok': True, 'msg': 'successAdded', 'msgi18n': True, 'monitorID': 3}
```

## 3 · Todo arriba

### latidos

`$ SELECT ... FROM heartbeat (kuma.db)`

```
20:55:05  Redis (TCP)  UP        0 ms  0 ms
20:55:05  Web (HTTP)   UP        6 ms  200 - OK
20:55:06  DNS de web   UP        0 ms  Records: 192.168.16.2
20:55:25  Redis (TCP)  UP        1 ms  1 ms
20:55:25  Web (HTTP)   UP        3 ms  200 - OK
20:55:26  DNS de web   UP        1 ms  Records: 192.168.16.2
```

### uso de memoria

`$ docker stats --no-stream kuma`

```
kuma 126.1MiB / 15.36GiB 0.40%
```

## 4 · Se cae la web

### parar la web

`$ docker stop web`

```
parada a las 20:55:58 UTC
```

### latidos

`$ SELECT ... FROM heartbeat (kuma.db)`

```
20:56:05  Web (HTTP)   DOWN         -  timeout of 16000ms exceeded
20:56:25  Redis (TCP)  UP        1 ms  1 ms
20:56:25  Web (HTTP)   DOWN         -  connect EHOSTUNREACH 192.168.16.2:80
20:56:26  DNS de web   DOWN         -  queryA ENODATA web
20:56:45  Redis (TCP)  UP        1 ms  1 ms
20:56:46  DNS de web   DOWN         -  queryA ENODATA web
```

### alertas recibidas en ntfy

`$ curl ntfy/alertas/json?poll=1`

```
20:56:07  prio=5  DNS de web Down [Uptime-Kuma] | queryA ENODATA web
20:56:21  prio=5  Web (HTTP) Down [Uptime-Kuma] | timeout of 16000ms exceeded
```

## 5 · Vuelve la web

### latidos

`$ SELECT ... FROM heartbeat (kuma.db)`

```
20:57:25  Redis (TCP)  UP        1 ms  1 ms
20:57:25  Web (HTTP)   UP        2 ms  200 - OK
20:57:26  DNS de web   UP        0 ms  Records: 192.168.16.2
20:57:45  Redis (TCP)  UP        1 ms  1 ms
20:57:45  Web (HTTP)   UP        1 ms  200 - OK
20:57:46  DNS de web   UP        1 ms  Records: 192.168.16.2
```

### alertas recibidas en ntfy

`$ curl ntfy/alertas/json?poll=1`

```
20:56:07  prio=5  DNS de web Down [Uptime-Kuma] | queryA ENODATA web
20:56:21  prio=5  Web (HTTP) Down [Uptime-Kuma] | timeout of 16000ms exceeded
20:57:09  prio=5  Web (HTTP) Up [Uptime-Kuma] | 200 - OK
20:57:26  prio=5  DNS de web Up [Uptime-Kuma] | Records: 192.168.16.2
```
