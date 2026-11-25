# SALIDA — «System design: caché y estampida» (cultura-devops, vídeo 346)

> Generado por `correr.py`. **No se escribe a mano.**

- fecha: `2026-10-11 04:52:52Z`
- `postgres (PostgreSQL) 17.11` · `Valkey server v=9.1.2`
- la consulta a la BD lleva pg_sleep(0.02): 20 ms fijos, a propósito (en la estampida, 0.2: la clave caliente es cara de reconstruir). Una sola máquina.

```
$ lab preparar
1000 productos en Postgres · Valkey vacío

== 1 · Sin caché: 2.000 lecturas, 20 a la vez, productos populares (Zipf) ==
$ lab sincache -n 2000
2000 lecturas en 2.12s · p50 20.53ms · p99 39.56ms
  aciertos de caché: 0 (0.0 %) · consultas a la BD: 2000

== 2 · Cache-aside con Valkey (TTL 60 s) ==
$ lab concache -n 2000
2000 lecturas en 450ms · p50 120µs · p99 26.09ms
  aciertos de caché: 1619 (81.0 %) · consultas a la BD: 381

== 3 · La lectura vieja: actualizar la BD sin tocar la caché ==
$ lab vieja
leo el producto 1: 100 €  (ahora está en caché)
  UPDATE precio = 120 en la BD · leo otra vez: 100 €  (de la caché: true)
  UPDATE precio = 130 y DEL de la clave · leo: 130 €  (de la caché: false)

== 4 · La estampida: expira la clave más pedida (200 ms reconstruirla) y llegan 100 peticiones a la vez ==
$ lab estampida -modo nada
nada         100 peticiones a la vez · consultas a la BD:  82 · la más lenta: 678ms
$ lab estampida -modo instancias
instancias   100 peticiones a la vez · consultas a la BD:   4 · la más lenta: 218ms
$ lab estampida -modo singleflight
singleflight 100 peticiones a la vez · consultas a la BD:   1 · la más lenta: 203ms
$ lab estampida -modo cerrojo
cerrojo      100 peticiones a la vez · consultas a la BD:   1 · la más lenta: 244ms

== 5 · 1.000 claves cargadas de golpe con TTL de 5 s, 50 lectores sin parar ==
$ lab expiracion   # TTL 5 s exactos
segundo 0:    0 consultas a la BD
  segundo 1:    0 consultas a la BD
  segundo 2:    0 consultas a la BD
  segundo 3:    0 consultas a la BD
  segundo 4:   13 consultas a la BD
  segundo 5:  780 consultas a la BD
  segundo 6:  223 consultas a la BD
  segundo 7:   23 consultas a la BD
  segundo 8:    3 consultas a la BD
$ lab expiracion -jitter   # TTL entre 3,5 y 6,5 s
segundo 0:    0 consultas a la BD
  segundo 1:    0 consultas a la BD
  segundo 2:    0 consultas a la BD
  segundo 3:  146 consultas a la BD
  segundo 4:  344 consultas a la BD
  segundo 5:  349 consultas a la BD
  segundo 6:  182 consultas a la BD
  segundo 7:   21 consultas a la BD
  segundo 8:  107 consultas a la BD

== 6 · El TTL: más corto, dato más fresco y más consultas (20 lectores, 6 s) ==
$ lab ttl -ttl 1s
TTL 1s    23067 lecturas · aciertos  87.6 % · consultas a la BD: 2853
$ lab ttl -ttl 5s
TTL 5s    35395 lecturas · aciertos  96.3 % · consultas a la BD: 1319
$ lab ttl -ttl 30s
TTL 30s   37778 lecturas · aciertos  97.3 % · consultas a la BD: 1012

== 7 · La caché se llena: maxmemory = lo usado + 1 MB, allkeys-lru, productos de ~2 KB ==
$ lab llena -n 2000
2000 lecturas en 470ms · p50 110µs · p99 28.63ms
  aciertos de caché: 1601 (80.0 %) · consultas a la BD: 399
  claves expulsadas por falta de memoria (evicted_keys): 36

== 8 · Pedir algo que no existe ==
$ lab inexistente
caché negativa false 100 peticiones del producto 5000 (no existe) · consultas a la BD: 100
  caché negativa true  100 peticiones del producto 5000 (no existe) · consultas a la BD: 1

== 9 · La caché se cae ==
$ docker stop sd-valkey
$ lab caida -n 400
400 lecturas en 20.63s · p50 323.8ms · p99 14.17325s
  aciertos de caché: 0 (0.0 %) · consultas a la BD: 400
  (202 avisos de go-redis, como: redis: connection pool: failed to dial after 5 attempts: dial tcp: lookup sd-valkey: i/o timeout)
```
