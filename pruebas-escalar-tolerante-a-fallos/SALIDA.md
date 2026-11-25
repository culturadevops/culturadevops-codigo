# SALIDA — «Cómo escalar un sistema web y hacerlo tolerante a fallos, medido» (cultura-devops, vídeo 396)

> Generado por `correr.py`. **No se escribe a mano.**

- fecha: `2026-10-12 13:38:45Z`
- app en Python 3.13 (app/app.py) · postgres (PostgreSQL) 17.11 · nginx 1.30.5 · Valkey 9.1.2 · MinIO · todo en Docker, en una sola máquina.

```
== 1 · Todo en una máquina: la app, su base de datos (un fichero) y los ficheros subidos ==
$ python carga.py pedidos http://una:8000 100
  100 pedidos creados
$ python carga.py subir http://una:8000 10
  10 ficheros subidos · una: 10
$ docker rm -f una && docker run ... una   # la máquina se pierde y se crea otra igual
$ curl http://una:8000/pedidos
  0 pedidos
$ python carga.py bajar http://una:8000 10 1
  10 descargas · 200: 0 · 404: 10 (100 %)
  404 desde una: 10

== 2 · La base de datos aparte (Postgres con su volumen); los ficheros, todavía en la app ==
$ python carga.py pedidos http://una:8000 100
  100 pedidos creados
$ python carga.py subir http://una:8000 10
  10 ficheros subidos · una: 10
$ docker rm -f una && docker run ... una
$ curl http://una:8000/pedidos
  100 pedidos
$ python carga.py bajar http://una:8000 10 1
  10 descargas · 200: 0 · 404: 10 (100 %)
  404 desde una: 10

== 3 · Dos réplicas, cada una con su disco, detrás de nginx (round robin) ==
$ python carga.py subir http://lb 20
  20 ficheros subidos · app1: 10 · app2: 10
$ python carga.py bajar http://lb 20 5
  100 descargas · 200: 48 · 404: 52 (52 %)
  200 desde app1: 24 · 200 desde app2: 24 · 404 desde app1: 26 · 404 desde app2: 26

== 4 · Los ficheros a un almacén de objetos (MinIO, API de S3) ==
$ python carga.py subir http://lb 20
  20 ficheros subidos · app1: 10 · app2: 10
$ python carga.py bajar http://lb 20 5
  100 descargas · 200: 100 · 404: 0 (0 %)
  200 desde app1: 50 · 200 desde app2: 50

== 5 · Se cae una réplica a mitad de carga (a los 3 s), 10 s, 20 clientes ==
$ python carga.py golpe-caida http://lb /pedidos 10 20 3   # y a los 3 s: docker kill app2
  4479 respuestas en 10 s → 448 por segundo · mediana 44.1 ms · p99 49.7 ms · errores 0
  por segundo:       425  450  449  455  446  448  446  449  446  445
  de ellas, app1:  213  225  224  425  446  448  446  449  446  445
  de ellas, app2:  212  225  225   30    0    0    0    0    0    0
  [nginx: chequeo pasivo por defecto, max_fails=1 fail_timeout=10s, y reintento en la otra réplica]

== 6 · La base de datos se vuelve el cuello de botella: una consulta pesada, 2 réplicas, 20 clientes, 10 s ==
  [ventas: 3.000.000 de filas sin índice; /ventas/7 suma las ventas del producto 7]
$ python carga.py golpe http://lb /ventas/7 10 20   # sin caché
  2142 respuestas en 10 s → 214 por segundo · mediana 89.2 ms · p99 123.9 ms · errores 0
$ python carga.py golpe http://lb /ventas/7 10 20   # con Valkey delante
  4448 respuestas en 10 s → 445 por segundo · mediana 44.1 ms · p99 49.8 ms · errores 0

== 7 · Una CDN de juguete: el origen está «lejos» (150 ms de latencia añadida) y hay una caché cerca ==
$ python carga.py tiempos http://lejos/subidas/foto.jpg 5   # al origen
  1655 ms · 1203 ms · 1204 ms · 1203 ms · 1203 ms
$ python carga.py tiempos http://cerca/subidas/foto.jpg 5   # por la caché cercana
  1656 ms (MISS) · 1 ms (HIT) · 1 ms (HIT) · 1 ms (HIT) · 1 ms (HIT)
```
