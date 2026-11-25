# SALIDA — ¿HAProxy o Nginx? (cultura-devops, serie «¿X o Y? Lo medí» de herramientas)

> Corrida del 2026-11-05 15:30, bajo el candado _logs/banco.lock. Regenerable con `python proxies.py haproxy nginx`. ⛔ Ninguna cifra de blog: todo salió de aquí.

- HAProxy: `HAProxy version 3.4.7-8872a26 2026/10/14 - https://haproxy.org/` — imagen oficial `haproxy:3.4.7-alpine`
- Nginx: `nginx version: nginx/1.30.6` — imagen oficial `nginx:1.30.6-alpine`
- Docker `29.6.2` (Docker Desktop, Windows 11, 24 hilos). Proxy con 2 CPU y 1g, 2 procesos/hilos de trabajo; backend Go con 6 CPU; wrk con 6 CPU; hey con 4.
- Configs en proxies/: sin registro de accesos en ninguno, conexiones persistentes al backend en todos con un pool de 1.024 ociosas (Nginx keepalive 1024, Caddy keepalive_idle_conns_per_host 1024, Traefik maxIdleConnsPerHost 1024; HAProxy sin tope de fábrica), el mismo certificado ECDSA P-256 en HTTPS. wrk habla HTTP/1.1 (sin HTTP/2 ni HTTP/3).

## 0 · ¿Hacen lo mismo? (antes de medir)

- Esperado: /api = sha256 4613a38a7f79ada3… (backend directo, 1.024 bytes)
- HAProxy HTTP /api: 200, 1024 bytes, HTTP/1.1, sha256 4613a38a7f79ada3… → igual
- HAProxy HTTPS /api: 200, 1024 bytes, HTTP/2, sha256 4613a38a7f79ada3… → igual
- HAProxy TLS negociado con el cliente de carga: `New, TLSv1.3, Cipher is TLS_AES_256_GCM_SHA384`
- Nginx HTTP /api: 200, 1024 bytes, HTTP/1.1, sha256 4613a38a7f79ada3… → igual
- Nginx HTTPS /api: 200, 1024 bytes, HTTP/1.1, sha256 4613a38a7f79ada3… → igual
- Nginx TLS negociado con el cliente de carga: `New, TLSv1.3, Cipher is TLS_AES_256_GCM_SHA384`

## 1 · Lo que despliegas (imagen oficial, sin la config)

| proxy | imagen | tamaño en disco |
|---|---|---|
| HAProxy | `haproxy:3.4.7-alpine` | 19,6 MiB |
| Nginx | `nginx:1.30.6-alpine` | 24,9 MiB |

Techo del backend solo (wrk directo, sin proxy, 10 s): 652.981 pet/s, p50 0,07 ms. Si un proxy se acercara a esa cifra, el cuello sería el backend.

## 2 · Arranque y memoria en reposo (contenedor nuevo → primera respuesta 200 por el proxy; mediana de 5)

| proxy | 1.ª respuesta (Docker incluido) | memoria en reposo |
|---|---|---|
| HAProxy | 241 ms | 25,6 MiB |
| Nginx | 237 ms | 13,0 MiB |

## 3 · A tope: wrk con 64 conexiones (4 hilos), 20 s tras 5 s de calentamiento

Proxy con 2 CPU y 1 GiB. Memoria = máximo de `docker stats` durante la carga; CPU = media (200 % = las 2 CPU llenas). Errores = los que cuenta wrk (de socket por tipo y respuestas no 2xx) sobre todas las peticiones de la corrida.

| ruta | proxy | peticiones/s | p50 | p99 | memoria máx. | CPU media | errores |
|---|---|---|---|---|---|---|---|
| proxy /api (1 KiB) · HTTP | HAProxy | 192.818 | 0,31 ms | 0,77 ms | 30,2 MiB | 183 % | 0 de 3.875.595 |
| proxy /api (1 KiB) · HTTP | Nginx | 184.445 | 0,33 ms | 0,79 ms | 15,7 MiB | 184 % | 0 de 3.707.303 |
| proxy /api (1 KiB) · HTTPS | HAProxy | 153.620 | 0,40 ms | 0,81 ms | 32,0 MiB | 185 % | 0 de 3.087.787 |
| proxy /api (1 KiB) · HTTPS | Nginx | 96.601 | 0,64 ms | 1,10 ms | 19,4 MiB | 183 % | timeout 64 de 1.934.220 |

## 4 · Muchas conexiones: wrk con 1000 conexiones abiertas a la vez, proxy /api por HTTP, 20 s

Arriba, la config del banco (pool de 1.024 conexiones ociosas al backend en todos). Abajo, cada proxy «de fábrica», sin tocar ese pool: Nginx sin upstream keepalive (una conexión nueva por petición), Caddy con su pool de 32 y Traefik con el de 200 (valores de su documentación); HAProxy no tiene tope de fábrica y no lleva variante. Es lo ÚNICO que cambia (proxies/*-fabrica.*). Con 1.000 clientes, lo que no cabe en el pool se abre y se cierra en cada petición.

| proxy | peticiones/s | p50 | p99 | memoria máx. | errores (wrk) |
|---|---|---|---|---|---|
| HAProxy | 125.273 | 7,80 ms | 10,13 ms | 53,6 MiB | 0 de 2.508.379 |
| Nginx | 148.742 | 6,64 ms | 9,31 ms | 31,7 MiB | 0 de 2.978.910 |
| Nginx de fábrica (sin keepalive al backend) | 1.368 | 506,59 ms | 1.140,00 ms | 28,8 MiB | no-2xx 25873 de 27.485 |

Lo que dejó cada proxy en su log de errores durante esta prueba (los 3 mensajes más repetidos; N = número):

- HAProxy: nada
- Nginx: nada
- Nginx de fábrica (sin keepalive al backend): 26873× `[crit] N#N: *N connect() to N.N.N.N:N failed (N: Address not available) while connecting to upstream, client: N.N.N.N, server: , request: "G`

## 5 · El mismo tráfico para los dos: ritmo fijo con hey (50 clientes, 15 s)

Ritmo = la mitad de lo que aguantó el más lento en esa ruta (a tope la latencia sale de la cola). Aquí lo que cuenta es cuánta CPU gasta cada uno para servir LO MISMO, y la latencia sin cola.

| ruta | ritmo pedido | proxy | peticiones/s servidas | p50 | p99 | CPU media | memoria máx. |
|---|---|---|---|---|---|---|---|
| proxy /api (1 KiB) · HTTP | 92.200/s | HAProxy | 90.973 | 0,20 ms | 0,70 ms | 122 % | 29,0 MiB |
| proxy /api (1 KiB) · HTTP | 92.200/s | Nginx | 87.503 | 0,30 ms | 0,90 ms | 148 % | 14,9 MiB |
| proxy /api (1 KiB) · HTTPS | 48.300/s | HAProxy | 47.944 | 0,30 ms | 0,80 ms | 69 % | 31,1 MiB |
| proxy /api (1 KiB) · HTTPS | 48.300/s | Nginx | 47.558 | 0,40 ms | 1,00 ms | 107 % | 17,4 MiB |

