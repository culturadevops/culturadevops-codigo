# SALIDA — ¿Traefik o Nginx? (cultura-devops, serie «¿X o Y? Lo medí» de herramientas)

> Corrida del 2026-11-05 10:35, bajo el candado _logs/banco.lock. Regenerable con `python proxies.py traefik nginx`. ⛔ Ninguna cifra de blog: todo salió de aquí.

- Traefik: `Version:      3.7.17` — imagen oficial `traefik:v3.7.17`
- Nginx: `nginx version: nginx/1.30.6` — imagen oficial `nginx:1.30.6-alpine`
- Docker `29.6.2` (Docker Desktop, Windows 11, 24 hilos). Proxy con 2 CPU y 1g, 2 procesos/hilos de trabajo; backend Go con 6 CPU; wrk con 6 CPU; hey con 4.
- Configs en proxies/: sin registro de accesos en ninguno, conexiones persistentes al backend en todos, el mismo certificado ECDSA P-256 en HTTPS. wrk habla HTTP/1.1 (sin HTTP/2 ni HTTP/3).

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

Techo del backend solo (wrk directo, sin proxy, 10 s): 606.125 pet/s, p50 0,07 ms. Si un proxy se acercara a esa cifra, el cuello sería el backend.

## 2 · Arranque y memoria en reposo (contenedor nuevo → primera respuesta 200 por el proxy; mediana de 5)

| proxy | 1.ª respuesta (Docker incluido) | memoria en reposo |
|---|---|---|
| Traefik | 288 ms | 16,7 MiB |
| Nginx | 224 ms | 13,2 MiB |

## 3 · A tope: wrk con 64 conexiones (4 hilos), 20 s tras 5 s de calentamiento

Proxy con 2 CPU y 1 GiB. Memoria = máximo de `docker stats` durante la carga; CPU = media (200 % = las 2 CPU llenas).

| ruta | proxy | peticiones/s | p50 | p99 | memoria máx. | CPU media | errores |
|---|---|---|---|---|---|---|---|
| proxy /api (1 KiB) · HTTP | Traefik | 69.537 | 0,84 ms | 3,80 ms | 49,0 MiB | 180 % | 63 |
| proxy /api (1 KiB) · HTTP | Nginx | 167.001 | 0,36 ms | 0,89 ms | 15,4 MiB | 180 % | 64 |
| proxy /api (1 KiB) · HTTPS | Traefik | 67.200 | 0,87 ms | 3,94 ms | 49,9 MiB | 179 % | 20 |
| proxy /api (1 KiB) · HTTPS | Nginx | 86.841 | 0,69 ms | 1,37 ms | 18,4 MiB | 181 % | 63 |

## 4 · Muchas conexiones: wrk con 1000 conexiones abiertas a la vez, proxy /api por HTTP, 20 s

| proxy | peticiones/s | p50 | p99 | memoria máx. | errores de socket | respuestas no 2xx |
|---|---|---|---|---|---|---|
| Traefik | 42.593 | 21,46 ms | 241,54 ms | 264,4 MiB | 0 | 0 |
| Nginx | 2.183 | 395,92 ms | 1.010,00 ms | 35,4 MiB | 0 | 18312 |

## 5 · El mismo tráfico para los dos: ritmo fijo con hey (50 clientes, 15 s)

Ritmo = la mitad de lo que aguantó el más lento en esa ruta (a tope la latencia sale de la cola). Aquí lo que cuenta es cuánta CPU gasta cada uno para servir LO MISMO, y la latencia sin cola.

| ruta | ritmo pedido | proxy | peticiones/s servidas | p50 | p99 | CPU media | memoria máx. |
|---|---|---|---|---|---|---|---|
| proxy /api (1 KiB) · HTTP | 34.800/s | Traefik | 34.233 | 0,40 ms | 2,80 ms | 104 % | 43,4 MiB |
| proxy /api (1 KiB) · HTTP | 34.800/s | Nginx | 34.809 | 0,50 ms | 1,00 ms | 56 % | 14,6 MiB |
| proxy /api (1 KiB) · HTTPS | 33.600/s | Traefik | 33.014 | 0,50 ms | 3,00 ms | 107 % | 43,9 MiB |
| proxy /api (1 KiB) · HTTPS | 33.600/s | Nginx | 33.523 | 0,40 ms | 1,00 ms | 80 % | 17,0 MiB |

