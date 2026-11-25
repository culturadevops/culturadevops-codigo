# SALIDA — «System design: polling, long polling, SSE y WebSockets» (cultura-devops, vídeo 355)

> Generado por `correr.py`. **No se escribe a mano.**

- fecha: `2026-10-11 14:47:32Z`
- servidor y clientes en Go 1.27.2 (coder/websocket v1.8.15) · `nginx version: nginx/1.30.5`
- una notificación cada 3 s; 100 clientes durante 30 s. Una sola máquina.

```
== 1 · Las cuatro maneras, directas al servidor (100 clientes, 30 s, un evento cada 3 s) ==
$ cli -modo poll -cada 5s
poll cada 5s 100 clientes · 30s:  500 eventos recibidos · retraso medio 1.254s · peor 2.267s · 1200 peticiones/min · conexiones abiertas a la vez: 0
               bytes en la red: 145 KB en total · 298 bytes por evento recibido
$ cli -modo poll -cada 1s
poll cada 1s 100 clientes · 30s: 1000 eventos recibidos · retraso medio 455ms · peor 484ms · 6000 peticiones/min · conexiones abiertas a la vez: 0
               bytes en la red: 729 KB en total · 747 bytes por evento recibido
$ cli -modo longpoll
longpoll     100 clientes · 30s: 1000 eventos recibidos · retraso medio 2ms · peor 6ms · 2400 peticiones/min · conexiones abiertas a la vez: 100
               bytes en la red: 291 KB en total · 298 bytes por evento recibido
$ cli -modo sse
sse          100 clientes · 30s: 1000 eventos recibidos · retraso medio 1ms · peor 9ms · 200 peticiones/min · conexiones abiertas a la vez: 100
               bytes en la red: 73 KB en total · 75 bytes por evento recibido
$ cli -modo ws
ws           100 clientes · 30s: 1000 eventos recibidos · retraso medio 1ms · peor 4ms · 200 peticiones/min · conexiones abiertas a la vez: 100
               bytes en la red: 76 KB en total · 78 bytes por evento recibido

== 1b · Lo que pesa tener conexiones abiertas: 2.000 a la vez ==
$ cli -modo memoria-sse -clientes 2000
sse 2000 conexiones abiertas · memoria del servidor: 5 MB antes, 64 MB con ellas · 29.9 KB por conexión
$ cli -modo memoria-ws -clientes 2000
ws  2000 conexiones abiertas · memoria del servidor: 5 MB antes, 69 MB con ellas · 32.9 KB por conexión

== 2 · Detrás de nginx, con la configuración que se suele copiar ==
$ cat nginx.conf   # location / { proxy_pass http://srv:8080; }
$ cli -url http://sd-proxy -modo sse
sse          100 clientes · 30s: 1000 eventos recibidos · retraso medio 2ms · peor 8ms · 200 peticiones/min · conexiones abiertas a la vez: 100
               bytes en la red: 77 KB en total · 79 bytes por evento recibido
$ cli -url http://sd-proxy -modo ws
ws           100 clientes · 30s:    0 eventos recibidos · retraso medio 0s · peor 0s · 200 peticiones/min · conexiones abiertas a la vez: 0
  error: failed to WebSocket dial: expected handshake response status code 101 but got 426

== 2b · El mismo nginx con gzip para text/event-stream ==
$ cli -url http://sd-proxy -modo sse   # gzip on
sse          100 clientes · 30s:    0 eventos recibidos · retraso medio 0s · peor 0s · 200 peticiones/min · conexiones abiertas a la vez: 100
  error: Get "http://sd-proxy/sse": context deadline exceeded

== 2c · Un flujo SSE que pasa 75 s sin eventos ==
$ cli -url http://sd-proxy -modo silencio -durante 75s   # nginx por defecto
silencio: la conexión se cortó a los 1m0s · unexpected EOF
$ cli -modo silencio -durante 75s   # directo, sin nginx
silencio: la conexión sigue abierta a los 1m15s (fin de la prueba)

== 3 · El arreglo ==
$ cli -url http://sd-proxy -modo sse -sin-buffer   # gzip on, y el servidor manda X-Accel-Buffering: no
sse          100 clientes · 30s: 1000 eventos recibidos · retraso medio 3ms · peor 6ms · 200 peticiones/min · conexiones abiertas a la vez: 100
               bytes en la red: 62 KB en total · 64 bytes por evento recibido
$ cat nginx.conf   # sin gzip para text/event-stream · Upgrade y Connection · proxy_read_timeout 1h
$ cli -url http://sd-proxy -modo sse
sse          100 clientes · 30s: 1000 eventos recibidos · retraso medio 2ms · peor 6ms · 200 peticiones/min · conexiones abiertas a la vez: 100
               bytes en la red: 78 KB en total · 80 bytes por evento recibido
$ cli -url http://sd-proxy -modo ws
ws           100 clientes · 30s: 1000 eventos recibidos · retraso medio 2ms · peor 8ms · 200 peticiones/min · conexiones abiertas a la vez: 100
               bytes en la red: 79 KB en total · 81 bytes por evento recibido
$ cli -url http://sd-proxy -modo silencio -durante 75s
silencio: la conexión sigue abierta a los 1m15s (fin de la prueba)
```
