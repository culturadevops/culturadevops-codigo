# SALIDA — «System design: balanceo de carga, medido» (cultura-devops, vídeo 345)

> Generado por `correr.py`. **No se escribe a mano.**

- fecha: `2026-10-11 04:32:13Z`
- `HAProxy version 3.4.6-56332c5 2026/09/28 - https://haproxy.org/`
- `nginx version: nginx/1.30.5`
- réplicas: r1 y r2 responden en 10 ms, r3 en 200 ms (la lenta). Una sola máquina: los tiempos son de esta, y lo que cuenta es la comparación.

```
== 1 · Cada réplica, sin balanceador ==
$ carga -url http://r1:8000/ -n 200 -c 5
200 bien · 0 fallos · p50 11ms · p99 18ms · total 400ms
  reparto: r1 200
$ carga -url http://r2:8000/ -n 200 -c 5
200 bien · 0 fallos · p50 11ms · p99 28ms · total 500ms
  reparto: r2 200
$ carga -url http://r3:8000/ -n 200 -c 5
200 bien · 0 fallos · p50 201ms · p99 207ms · total 8s
  reparto: r3 200

== 2 · Tres algoritmos en HAProxy (3.000 peticiones, 30 clientes) ==
$ HAProxy · balance roundrobin
3000 bien · 0 fallos · p50 11ms · p99 205ms · total 7.6s
  reparto: r1 1000 · r2 1001 · r3 999
$ HAProxy · balance leastconn
3000 bien · 0 fallos · p50 11ms · p99 201ms · total 1.7s
  reparto: r1 1458 · r2 1462 · r3 80
$ HAProxy · balance source
3000 bien · 0 fallos · p50 201ms · p99 208ms · total 20.2s
  reparto: r3 3000

== 2b · Lo mismo en nginx ==
$ nginx · round robin (por defecto)
3000 bien · 0 fallos · p50 11ms · p99 202ms · total 7.5s
  reparto: r1 1000 · r2 1000 · r3 1000
$ nginx · least_conn
3000 bien · 0 fallos · p50 11ms · p99 201ms · total 1.8s
  reparto: r1 1456 · r2 1454 · r3 90
$ nginx · ip_hash
3000 bien · 0 fallos · p50 11ms · p99 20ms · total 1.1s
  reparto: r1 3000

== 3 · Una réplica se cae a mitad de carga ==
$ carga -durante 12s   (HAProxy sin chequeos; a los 3 s muere el proceso de r2)
segundo  0:  139 bien ·   0 fallos
  segundo  1:  127 bien ·   0 fallos
  segundo  2:  143 bien ·   0 fallos
  segundo  3:   28 bien ·   0 fallos
  segundo  6:   18 bien ·  10 fallos
  segundo  7:    2 bien ·   0 fallos
  segundo  9:   14 bien ·   9 fallos
  segundo 10:    6 bien ·   1 fallos
  segundo 12:    0 bien ·   7 fallos
  segundo 13:    0 bien ·   3 fallos
  477 bien · 30 fallos · p50 11ms · p99 204ms · total 13.4s
  reparto: r1 169 · r2 140 · r3 168
  (r2 vuelve a arrancar para la prueba siguiente: en marcha)
$ carga -durante 12s   (HAProxy con chequeo activo: GET /salud cada 1 s, 3 fallos = fuera; a los 3 s muere el proceso de r2)
segundo  0:  139 bien ·   0 fallos
  segundo  1:  128 bien ·   0 fallos
  segundo  2:  141 bien ·   0 fallos
  segundo  3:   28 bien ·   0 fallos
  segundo  6:   63 bien ·  10 fallos
  segundo  7:   90 bien ·   0 fallos
  segundo  8:   99 bien ·   0 fallos
  segundo  9:   94 bien ·   0 fallos
  segundo 10:   91 bien ·   0 fallos
  segundo 11:   95 bien ·   0 fallos
  segundo 12:   10 bien ·   0 fallos
  978 bien · 10 fallos · p50 11ms · p99 205ms · total 12.2s
  reparto: r1 419 · r2 139 · r3 420
  (r2 vuelve a arrancar para la prueba siguiente: en marcha)
$ docker logs sd-lb | grep -i down
Server api/r2 is DOWN, reason: Layer4 connection problem, info: "ECONNREFUSED returned by OS (Connection refused)", check duration: 0ms. 2 active and 0 backup servers left. 0 sessions active, 0 requeued, 0 remaining in queue.
[WARNING]  (8) : Server api/r2 is DOWN, reason: Layer4 connection problem,
$ carga -durante 12s   (nginx: chequeo pasivo (max_fails=1, fail_timeout=10s) y reintento en otra réplica; a los 3 s muere el proceso de r2)
segundo  0:  138 bien ·   0 fallos
  segundo  1:  132 bien ·   0 fallos
  segundo  2:  133 bien ·   0 fallos
  segundo  3:   95 bien ·   0 fallos
  segundo  4:   94 bien ·   0 fallos
  segundo  5:   95 bien ·   0 fallos
  segundo  6:   92 bien ·   0 fallos
  segundo  7:   95 bien ·   0 fallos
  segundo  8:   95 bien ·   0 fallos
  segundo  9:   93 bien ·   0 fallos
  segundo 10:   96 bien ·   0 fallos
  segundo 11:   93 bien ·   0 fallos
  segundo 12:   10 bien ·   0 fallos
  1261 bien · 0 fallos · p50 11ms · p99 204ms · total 12.2s
  reparto: r1 561 · r2 138 · r3 562
  (r2 vuelve a arrancar para la prueba siguiente: en marcha)

== 4 · L4 contra L7, con 2 clientes que reutilizan su conexión (300 peticiones) ==
$ HAProxy · mode tcp (L4): reparte CONEXIONES
300 bien · 0 fallos · p50 11ms · p99 18ms · total 1.7s
  reparto: r1 151 · r2 149
$ HAProxy · mode http (L7): reparte PETICIONES
300 bien · 0 fallos · p50 11ms · p99 207ms · total 11.3s
  reparto: r1 100 · r2 100 · r3 100
```
