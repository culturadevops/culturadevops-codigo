# SALIDA — ¿Nginx o Caddy? (cultura-devops, serie «¿X o Y? Lo medí» de herramientas)

> Corrida del 2026-11-05 15:15, bajo el candado _logs/banco.lock. Regenerable con `python proxies.py nginx caddy`. ⛔ Ninguna cifra de blog: todo salió de aquí.

- Nginx: `nginx version: nginx/1.30.6` — imagen oficial `nginx:1.30.6-alpine`
- Caddy: `v2.11.8 h1:E2pv1BoZ5bJaWqFkU6QvLa21iGAX8bDzlEQG4dDQ/Vc=` — imagen oficial `caddy:2.11.8-alpine`
- Docker `29.6.2` (Docker Desktop, Windows 11, 24 hilos). Proxy con 2 CPU y 1g, 2 procesos/hilos de trabajo; backend Go con 6 CPU; wrk con 6 CPU; hey con 4.
- Configs en proxies/: sin registro de accesos en ninguno, conexiones persistentes al backend en todos con un pool de 1.024 ociosas (Nginx keepalive 1024, Caddy keepalive_idle_conns_per_host 1024, Traefik maxIdleConnsPerHost 1024; HAProxy sin tope de fábrica), el mismo certificado ECDSA P-256 en HTTPS. wrk habla HTTP/1.1 (sin HTTP/2 ni HTTP/3).

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

Techo del backend solo (wrk directo, sin proxy, 10 s): 652.566 pet/s, p50 0,07 ms. Si un proxy se acercara a esa cifra, el cuello sería el backend.

## 2 · Arranque y memoria en reposo (contenedor nuevo → primera respuesta 200 por el proxy; mediana de 5)

| proxy | 1.ª respuesta (Docker incluido) | memoria en reposo |
|---|---|---|
| Nginx | 223 ms | 13,5 MiB |
| Caddy | 246 ms | 12,1 MiB |

## 3 · A tope: wrk con 64 conexiones (4 hilos), 20 s tras 5 s de calentamiento

Proxy con 2 CPU y 1 GiB. Memoria = máximo de `docker stats` durante la carga; CPU = media (200 % = las 2 CPU llenas). Errores = los que cuenta wrk (de socket por tipo y respuestas no 2xx) sobre todas las peticiones de la corrida.

| ruta | proxy | peticiones/s | p50 | p99 | memoria máx. | CPU media | errores |
|---|---|---|---|---|---|---|---|
| estático 4 KiB · HTTP | Nginx | 264.470 | 0,23 ms | 0,41 ms | 12,5 MiB | 180 % | 0 de 5.315.674 |
| estático 4 KiB · HTTP | Caddy | 74.335 | 0,82 ms | 3,16 ms | 25,6 MiB | 180 % | timeout 64 de 1.488.662 |
| estático 4 KiB · HTTPS | Nginx | 100.343 | 0,62 ms | 0,91 ms | 15,4 MiB | 182 % | 0 de 2.008.599 |
| estático 4 KiB · HTTPS | Caddy | 78.219 | 0,77 ms | 3,24 ms | 26,9 MiB | 181 % | 0 de 1.567.169 |
| proxy /api (1 KiB) · HTTP | Nginx | 180.058 | 0,34 ms | 0,78 ms | 16,4 MiB | 183 % | 0 de 3.619.187 |
| proxy /api (1 KiB) · HTTP | Caddy | 51.773 | 1,09 ms | 3,82 ms | 27,3 MiB | 176 % | timeout 56 de 1.037.153 |
| proxy /api (1 KiB) · HTTPS | Nginx | 96.719 | 0,66 ms | 1,10 ms | 18,9 MiB | 180 % | timeout 64 de 1.936.103 |
| proxy /api (1 KiB) · HTTPS | Caddy | 49.903 | 1,12 ms | 4,18 ms | 31,0 MiB | 181 % | timeout 46 de 1.000.187 |

## 4 · Muchas conexiones: wrk con 1000 conexiones abiertas a la vez, proxy /api por HTTP, 20 s

Arriba, la config del banco (pool de 1.024 conexiones ociosas al backend en todos). Abajo, cada proxy «de fábrica», sin tocar ese pool: Nginx sin upstream keepalive (una conexión nueva por petición), Caddy con su pool de 32 y Traefik con el de 200 (valores de su documentación); HAProxy no tiene tope de fábrica y no lleva variante. Es lo ÚNICO que cambia (proxies/*-fabrica.*). Con 1.000 clientes, lo que no cabe en el pool se abre y se cierra en cada petición.

| proxy | peticiones/s | p50 | p99 | memoria máx. | errores (wrk) |
|---|---|---|---|---|---|
| Nginx | 150.741 | 6,55 ms | 9,19 ms | 31,5 MiB | 0 de 3.015.149 |
| Caddy | 35.854 | 25,92 ms | 39,50 ms | 167,4 MiB | 0 de 718.106 |
| Nginx de fábrica (sin keepalive al backend) | 1.256 | 792,63 ms | 1.030,00 ms | 31,8 MiB | no-2xx 23513 de 25.172 |
| Caddy de fábrica (pool de 32) | 915 | 845,05 ms | 4.020,00 ms | 198,6 MiB | no-2xx 339 de 18.352 |

Lo que dejó cada proxy en su log de errores durante esta prueba (los 3 mensajes más repetidos; N = número):

- Nginx: nada
- Caddy: 2× `because it requires TLS","network":"tcp","addr":":N"}`; 1× `disabled"}`
- Nginx de fábrica (sin keepalive al backend): 24512× `[crit] N#N: *N connect() to N.N.N.N:N failed (N: Address not available) while connecting to upstream, client: N.N.N.N, server: , request: "G`
- Caddy de fábrica (pool de 32): 329× `N.N.N.N:N: connect: cannot assign requested address","request":{"remote_ip":"N.N.N.N","remote_port":"N","client_ip":"N.N.N.N","proto":"HTTP/`; 10× `lookup backend: i/o timeout","request":{"remote_ip":"N.N.N.N","remote_port":"N","client_ip":"N.N.N.N","proto":"HTTP/N.N","method":"GET","hos`; 2× `because it requires TLS","network":"tcp","addr":":N"}`

## 5 · El mismo tráfico para los dos: ritmo fijo con hey (50 clientes, 15 s)

Ritmo = la mitad de lo que aguantó el más lento en esa ruta (a tope la latencia sale de la cola). Aquí lo que cuenta es cuánta CPU gasta cada uno para servir LO MISMO, y la latencia sin cola.

| ruta | ritmo pedido | proxy | peticiones/s servidas | p50 | p99 | CPU media | memoria máx. |
|---|---|---|---|---|---|---|---|
| proxy /api (1 KiB) · HTTP | 25.900/s | Nginx | 25.852 | 0,30 ms | 0,80 ms | 44 % | 14,7 MiB |
| proxy /api (1 KiB) · HTTP | 25.900/s | Caddy | 25.878 | 0,60 ms | 2,80 ms | 99 % | 25,8 MiB |
| proxy /api (1 KiB) · HTTPS | 25.000/s | Nginx | 24.953 | 0,40 ms | 0,80 ms | 58 % | 17,1 MiB |
| proxy /api (1 KiB) · HTTPS | 25.000/s | Caddy | 24.953 | 0,60 ms | 2,90 ms | 105 % | 25,7 MiB |
| estático 4 KiB · HTTP | 37.200/s | Nginx | 37.195 | 0,10 ms | 0,30 ms | 32 % | 13,7 MiB |
| estático 4 KiB · HTTP | 37.200/s | Caddy | 37.134 | 0,30 ms | 1,70 ms | 107 % | 24,0 MiB |
| estático 4 KiB · HTTPS | 39.100/s | Nginx | 39.092 | 0,30 ms | 0,60 ms | 76 % | 15,5 MiB |
| estático 4 KiB · HTTPS | 39.100/s | Caddy | 38.937 | 0,40 ms | 1,80 ms | 105 % | 27,9 MiB |

