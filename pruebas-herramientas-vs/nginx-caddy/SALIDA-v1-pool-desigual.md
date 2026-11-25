# SALIDA — ¿Nginx o Caddy? (cultura-devops, serie «¿X o Y? Lo medí» de herramientas)

> Corrida del 2026-11-05 14:52, bajo el candado _logs/banco.lock. Regenerable con `python proxies.py nginx caddy`. ⛔ Ninguna cifra de blog: todo salió de aquí.

- Nginx: `nginx version: nginx/1.30.6` — imagen oficial `nginx:1.30.6-alpine`
- Caddy: `v2.11.8 h1:E2pv1BoZ5bJaWqFkU6QvLa21iGAX8bDzlEQG4dDQ/Vc=` — imagen oficial `caddy:2.11.8-alpine`
- Docker `29.6.2` (Docker Desktop, Windows 11, 24 hilos). Proxy con 2 CPU y 1g, 2 procesos/hilos de trabajo; backend Go con 6 CPU; wrk con 6 CPU; hey con 4.
- Configs en proxies/: sin registro de accesos en ninguno, conexiones persistentes al backend en todos, el mismo certificado ECDSA P-256 en HTTPS. wrk habla HTTP/1.1 (sin HTTP/2 ni HTTP/3).

## 0 · ¿Hacen lo mismo? (antes de medir)

- Esperado: /api = sha256 4613a38a7f79ada3… (backend directo, 1.024 bytes); /static/archivo.html = sha256 618b26fef3054c7c… (4.096 bytes)
- Nginx HTTP /static/archivo.html: 200, 4096 bytes, HTTP/1.1, sha256 618b26fef3054c7c… → igual
- Nginx HTTPS /static/archivo.html: 200, 4096 bytes, HTTP/1.1, sha256 618b26fef3054c7c… → igual
- Nginx HTTP /api: 200, 1024 bytes, HTTP/1.1, sha256 4613a38a7f79ada3… → igual
- Nginx HTTPS /api: 200, 1024 bytes, HTTP/1.1, sha256 4613a38a7f79ada3… → igual
- Nginx TLS negociado con el cliente de carga: `New, TLSv1.3, Cipher is TLS_AES_256_GCM_SHA384`
- Caddy HTTP /static/archivo.html: 200, 4096 bytes, HTTP/1.1, sha256 618b26fef3054c7c… → igual
- Caddy HTTPS /static/archivo.html: 200, 4096 bytes, HTTP/2, sha256 618b26fef3054c7c… → igual
- Caddy HTTP /api: 200, 1024 bytes, HTTP/1.1, sha256 4613a38a7f79ada3… → igual
- Caddy HTTPS /api: 200, 1024 bytes, HTTP/2, sha256 4613a38a7f79ada3… → igual
- Caddy TLS negociado con el cliente de carga: `New, TLSv1.3, Cipher is TLS_AES_128_GCM_SHA256`

## 1 · Lo que despliegas (imagen oficial, sin la config)

| proxy | imagen | tamaño en disco |
|---|---|---|
| Nginx | `nginx:1.30.6-alpine` | 24,9 MiB |
| Caddy | `caddy:2.11.8-alpine` | 23,7 MiB |

Techo del backend solo (wrk directo, sin proxy, 10 s): 639.798 pet/s, p50 0,07 ms. Si un proxy se acercara a esa cifra, el cuello sería el backend.

## 2 · Arranque y memoria en reposo (contenedor nuevo → primera respuesta 200 por el proxy; mediana de 5)

| proxy | 1.ª respuesta (Docker incluido) | memoria en reposo |
|---|---|---|
| Nginx | 221 ms | 12,5 MiB |
| Caddy | 208 ms | 12,2 MiB |

## 3 · A tope: wrk con 64 conexiones (4 hilos), 20 s tras 5 s de calentamiento

Proxy con 2 CPU y 1 GiB. Memoria = máximo de `docker stats` durante la carga; CPU = media (200 % = las 2 CPU llenas). Errores = los que cuenta wrk (de socket por tipo y respuestas no 2xx) sobre todas las peticiones de la corrida.

| ruta | proxy | peticiones/s | p50 | p99 | memoria máx. | CPU media | errores |
|---|---|---|---|---|---|---|---|
| estático 4 KiB · HTTP | Nginx | 255.960 | 0,24 ms | 0,41 ms | 12,7 MiB | 180 % | 0 de 5.144.734 |
| estático 4 KiB · HTTP | Caddy | 73.801 | 0,83 ms | 3,21 ms | 26,3 MiB | 180 % | timeout 63 de 1.479.023 |
| estático 4 KiB · HTTPS | Nginx | 95.891 | 0,65 ms | 1,02 ms | 16,2 MiB | 184 % | 0 de 1.922.478 |
| estático 4 KiB · HTTPS | Caddy | 77.416 | 0,78 ms | 3,53 ms | 27,6 MiB | 182 % | timeout 26 de 1.551.781 |
| proxy /api (1 KiB) · HTTP | Nginx | 175.236 | 0,35 ms | 0,79 ms | 16,4 MiB | 184 % | 0 de 3.522.128 |
| proxy /api (1 KiB) · HTTP | Caddy | 50.174 | 1,13 ms | 3,90 ms | 32,2 MiB | 178 % | timeout 49 de 1.004.466 |
| proxy /api (1 KiB) · HTTPS | Nginx | 94.070 | 0,66 ms | 1,07 ms | 19,1 MiB | 182 % | timeout 63 de 1.882.837 |
| proxy /api (1 KiB) · HTTPS | Caddy | 46.535 | 1,20 ms | 5,42 ms | 36,3 MiB | 181 % | timeout 40 de 932.216 |

## 4 · Muchas conexiones: wrk con 1000 conexiones abiertas a la vez, proxy /api por HTTP, 20 s

Si un proxy está en el par, también va Nginx con `keepalive 1024` en el upstream (en vez de 64): con 64, las conexiones al backend que pasan de 64 se abren y se cierran en cada petición. Es la ÚNICA línea que cambia (proxies/nginx-ka1024.conf).

| proxy | peticiones/s | p50 | p99 | memoria máx. | errores (wrk) |
|---|---|---|---|---|---|
| Nginx | 7.723 | 110,69 ms | 478,90 ms | 35,8 MiB |  · no-2xx 20776 de 154.729 |
| Caddy | 793 | 854,91 ms | 4.220,00 ms | 182,0 MiB | timeout 77 · no-2xx 97 de 15.870 |
| Nginx (keepalive 1024) | 145.064 | 6,79 ms | 9,94 ms | 32,5 MiB | 0 de 2.904.418 |

Lo que dejó cada proxy en su log de errores durante esta prueba (los 3 mensajes más repetidos; N = número):

- Nginx: 20905× `[crit] N#N: *N connect() to N.N.N.N:N failed (N: Address not available) while connecting to upstream, client: N.N.N.N, server: , request: "G`
- Caddy: 118× `N.N.N.N:N: connect: cannot assign requested address","request":{"remote_ip":"N.N.N.N","remote_port":"N","client_ip":"N.N.N.N","proto":"HTTP/`; 2× `because it requires TLS","network":"tcp","addr":":N"}`; 1× `disabled"}`
- Nginx (keepalive 1024): nada

## 5 · El mismo tráfico para los dos: ritmo fijo con hey (50 clientes, 15 s)

Ritmo = la mitad de lo que aguantó el más lento en esa ruta (a tope la latencia sale de la cola). Aquí lo que cuenta es cuánta CPU gasta cada uno para servir LO MISMO, y la latencia sin cola.

| ruta | ritmo pedido | proxy | peticiones/s servidas | p50 | p99 | CPU media | memoria máx. |
|---|---|---|---|---|---|---|---|
| proxy /api (1 KiB) · HTTP | 25.100/s | Nginx | 25.095 | 0,30 ms | 0,70 ms | 41 % | 14,6 MiB |
| proxy /api (1 KiB) · HTTP | 25.100/s | Caddy | 21.734 | 0,70 ms | 11,30 ms | 164 % | 32,9 MiB |
| proxy /api (1 KiB) · HTTPS | 23.300/s | Nginx | 23.285 | 0,40 ms | 0,80 ms | 52 % | 17,9 MiB |
| proxy /api (1 KiB) · HTTPS | 23.300/s | Caddy | 21.760 | 0,60 ms | 6,10 ms | 138 % | 32,5 MiB |
| estático 4 KiB · HTTP | 36.900/s | Nginx | 36.892 | 0,10 ms | 0,30 ms | 33 % | 13,7 MiB |
| estático 4 KiB · HTTP | 36.900/s | Caddy | 36.841 | 0,40 ms | 1,70 ms | 99 % | 24,7 MiB |
| estático 4 KiB · HTTPS | 38.700/s | Nginx | 38.686 | 0,30 ms | 0,70 ms | 79 % | 15,7 MiB |
| estático 4 KiB · HTTPS | 38.700/s | Caddy | 38.503 | 0,40 ms | 1,90 ms | 104 % | 27,5 MiB |

