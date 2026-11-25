# SALIDA — ¿Traefik o Nginx? (cultura-devops, serie «¿X o Y? Lo medí» de herramientas)

> Corrida del 2026-11-05 15:24, bajo el candado _logs/banco.lock. Regenerable con `python proxies.py traefik nginx`. ⛔ Ninguna cifra de blog: todo salió de aquí.

- Traefik: `Version:      3.7.17` — imagen oficial `traefik:v3.7.17`
- Nginx: `nginx version: nginx/1.30.6` — imagen oficial `nginx:1.30.6-alpine`
- Docker `29.6.2` (Docker Desktop, Windows 11, 24 hilos). Proxy con 2 CPU y 1g, 2 procesos/hilos de trabajo; backend Go con 6 CPU; wrk con 6 CPU; hey con 4.
- Configs en proxies/: sin registro de accesos en ninguno, conexiones persistentes al backend en todos con un pool de 1.024 ociosas (Nginx keepalive 1024, Caddy keepalive_idle_conns_per_host 1024, Traefik maxIdleConnsPerHost 1024; HAProxy sin tope de fábrica), el mismo certificado ECDSA P-256 en HTTPS. wrk habla HTTP/1.1 (sin HTTP/2 ni HTTP/3).

## 0 · ¿Hacen lo mismo? (antes de medir)

- Esperado: /api = sha256 4613a38a7f79ada3… (backend directo, 1.024 bytes)
- Traefik HTTP /api: 200, 1024 bytes, HTTP/1.1, sha256 4613a38a7f79ada3… → igual
- Traefik HTTPS /api: 200, 1024 bytes, HTTP/2, sha256 4613a38a7f79ada3… → igual
- Traefik TLS negociado con el cliente de carga: `New, TLSv1.3, Cipher is TLS_AES_128_GCM_SHA256`
- Nginx HTTP /api: 200, 1024 bytes, HTTP/1.1, sha256 4613a38a7f79ada3… → igual
- Nginx HTTPS /api: 200, 1024 bytes, HTTP/1.1, sha256 4613a38a7f79ada3… → igual
- Nginx TLS negociado con el cliente de carga: `New, TLSv1.3, Cipher is TLS_AES_256_GCM_SHA384`

## 1 · Lo que despliegas (imagen oficial, sin la config)

| proxy | imagen | tamaño en disco |
|---|---|---|
| Traefik | `traefik:v3.7.17` | 52,6 MiB |
| Nginx | `nginx:1.30.6-alpine` | 24,9 MiB |

Techo del backend solo (wrk directo, sin proxy, 10 s): 652.084 pet/s, p50 0,07 ms. Si un proxy se acercara a esa cifra, el cuello sería el backend.

## 2 · Arranque y memoria en reposo (contenedor nuevo → primera respuesta 200 por el proxy; mediana de 5)

| proxy | 1.ª respuesta (Docker incluido) | memoria en reposo |
|---|---|---|
| Traefik | 249 ms | 16,3 MiB |
| Nginx | 234 ms | 13,1 MiB |

## 3 · A tope: wrk con 64 conexiones (4 hilos), 20 s tras 5 s de calentamiento

Proxy con 2 CPU y 1 GiB. Memoria = máximo de `docker stats` durante la carga; CPU = media (200 % = las 2 CPU llenas). Errores = los que cuenta wrk (de socket por tipo y respuestas no 2xx) sobre todas las peticiones de la corrida.

| ruta | proxy | peticiones/s | p50 | p99 | memoria máx. | CPU media | errores |
|---|---|---|---|---|---|---|---|
| proxy /api (1 KiB) · HTTP | Traefik | 74.782 | 0,78 ms | 3,58 ms | 42,4 MiB | 183 % | 0 de 1.503.120 |
| proxy /api (1 KiB) · HTTP | Nginx | 185.552 | 0,33 ms | 0,80 ms | 15,7 MiB | 182 % | timeout 58 de 3.715.875 |
| proxy /api (1 KiB) · HTTPS | Traefik | 71.521 | 0,82 ms | 3,74 ms | 45,4 MiB | 181 % | timeout 53 de 1.432.046 |
| proxy /api (1 KiB) · HTTPS | Nginx | 99.485 | 0,63 ms | 1,12 ms | 18,8 MiB | 184 % | timeout 64 de 1.992.194 |

## 4 · Muchas conexiones: wrk con 1000 conexiones abiertas a la vez, proxy /api por HTTP, 20 s

Arriba, la config del banco (pool de 1.024 conexiones ociosas al backend en todos). Abajo, cada proxy «de fábrica», sin tocar ese pool: Nginx sin upstream keepalive (una conexión nueva por petición), Caddy con su pool de 32 y Traefik con el de 200 (valores de su documentación); HAProxy no tiene tope de fábrica y no lleva variante. Es lo ÚNICO que cambia (proxies/*-fabrica.*). Con 1.000 clientes, lo que no cabe en el pool se abre y se cierra en cada petición.

| proxy | peticiones/s | p50 | p99 | memoria máx. | errores (wrk) |
|---|---|---|---|---|---|
| Traefik | 49.529 | 19,33 ms | 36,02 ms | 321,2 MiB | 0 de 995.211 |
| Nginx | 150.215 | 6,49 ms | 9,54 ms | 32,9 MiB | 0 de 3.005.673 |
| Traefik de fábrica (pool de 200) | 47.970 | 19,67 ms | 36,10 ms | 272,6 MiB | 0 de 963.848 |
| Nginx de fábrica (sin keepalive al backend) | 1.368 | 728,83 ms | 870,85 ms | 29,1 MiB | timeout 6 · no-2xx 26438 de 27.426 |

Lo que dejó cada proxy en su log de errores durante esta prueba (los 3 mensajes más repetidos; N = número):

- Traefik: nada
- Nginx: nada
- Traefik de fábrica (pool de 200): nada
- Nginx de fábrica (sin keepalive al backend): 27384× `[crit] N#N: *N connect() to N.N.N.N:N failed (N: Address not available) while connecting to upstream, client: N.N.N.N, server: , request: "G`

## 5 · El mismo tráfico para los dos: ritmo fijo con hey (50 clientes, 15 s)

Ritmo = la mitad de lo que aguantó el más lento en esa ruta (a tope la latencia sale de la cola). Aquí lo que cuenta es cuánta CPU gasta cada uno para servir LO MISMO, y la latencia sin cola.

| ruta | ritmo pedido | proxy | peticiones/s servidas | p50 | p99 | CPU media | memoria máx. |
|---|---|---|---|---|---|---|---|
| proxy /api (1 KiB) · HTTP | 37.400/s | Traefik | 36.632 | 0,50 ms | 2,80 ms | 105 % | 41,4 MiB |
| proxy /api (1 KiB) · HTTP | 37.400/s | Nginx | 37.414 | 0,40 ms | 0,80 ms | 59 % | 14,9 MiB |
| proxy /api (1 KiB) · HTTPS | 35.800/s | Traefik | 35.064 | 0,50 ms | 3,00 ms | 111 % | 42,8 MiB |
| proxy /api (1 KiB) · HTTPS | 35.800/s | Nginx | 35.776 | 0,50 ms | 1,00 ms | 77 % | 17,9 MiB |

