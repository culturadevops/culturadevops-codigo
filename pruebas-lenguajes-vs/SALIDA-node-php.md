# SALIDA — ¿Node o PHP? (cultura-devops)

> Corrida del 2026-11-04 13:41. Regenerable con `python correr.py node php`. ⛔ Ninguna cifra de blog: todo salió de aquí. Servidores de canales/golandia/recursos/pruebas-go-* (mismo contrato).

- node: `v24.22.2` — node:24-slim (node:http, sin dependencias)
- php: `FrankenPHP v1.13.3 PHP 8.5.12 Caddy v2.11.7 h1:yj0Y4fYZGPkSvibBJ1sTWE33xC0fxztVyXEW5iIdUT4=` — dunglas/frankenphp:1.13.3-php8.5
- Docker `29.6.2`. Servidores con 2 CPU y 1g; `hey -c 16` con 4 CPU desde otro contenedor.
- /trabajo?n=20000: crea 20000 objetos, los mete en un mapa, los ordena y arma un JSON a mano. /suma?n=200000: multiplicar y módulo en un bucle.

## 1 · Construir la imagen desde cero (`docker build --no-cache`, dependencias incluidas; la imagen base ya descargada no cuenta)

| lenguaje | qué se cronometra | segundos |
|---|---|---|
| node | copiar servidor.js (no instala nada) | 0.7 |
| php | copiar el código (PHP no compila) | 0.7 |

## 2 · Lo que despliegas

| imagen | base | tamaño en disco |
|---|---|---|
| node | node:24-slim (node:http, sin dependencias) | 77.3 MiB |
| php | dunglas/frankenphp:1.13.3-php8.5 | 201.2 MiB |

## 0 · ¿Hacen lo mismo? (antes de medir)

- node (1 proceso): total 9990000, primeros ids [0, 1000, 2000, 3000, 4000]…, suma 99863963591 → igual
- node (2 procesos): total 9990000, primeros ids [0, 1000, 2000, 3000, 4000]…, suma 99863963591 → igual
- php clásico (FrankenPHP): total 9990000, primeros ids [0, 1000, 2000, 3000, 4000]…, suma 99863963591 → igual
- php worker (FrankenPHP): total 9990000, primeros ids [0, 1000, 2000, 3000, 4000]…, suma 99863963591 → igual
- php worker + JIT: total 9990000, primeros ids [0, 1000, 2000, 3000, 4000]…, suma 99863963591 → igual

## 3 · Arranque: contenedor nuevo → primera respuesta 200 (mediana de 8) y memoria en reposo

| variante | 1ª respuesta (docker incluido) | «listo» (su propio reloj) | memoria en reposo |
|---|---|---|---|
| node (1 proceso) | 216 ms | 2.9 ms | 12.5 MiB |
| node (2 procesos) | 243 ms | 3.8 ms | 34.3 MiB |
| php clásico (FrankenPHP) | 238 ms | — | 24.3 MiB |
| php worker (FrankenPHP) | 249 ms | 0.0 ms | 25.7 MiB |
| php worker + JIT | 240 ms | 0.0 ms | 26.4 MiB |

## A · Cómputo de UNA petición (mediana del reloj del propio servidor, 30 de calentamiento + 200 medidas, de una en una)

| variante | /trabajo (20.000 objetos) | /suma (200.000 vueltas) |
|---|---|---|
| node (1 proceso) | 3.31 ms | 1.171 ms |
| node (2 procesos) | 3.36 ms | 1.167 ms |
| php clásico (FrankenPHP) | 11.55 ms | 0.666 ms |
| php worker (FrankenPHP) | 13.12 ms | 0.671 ms |
| php worker + JIT | 11.68 ms | 0.401 ms |

## 4 · Carga con memoria: /trabajo (objetos, mapa, orden, JSON), a tope

`hey -c 16` desde otro contenedor; servidor con 2 CPU y 1g. «En frío»: los primeros 10 s tras arrancar. «Templado»: los 20 s siguientes.

| variante | peticiones/s en frío | peticiones/s templado | p50 | p99 | memoria máx. bajo carga |
|---|---|---|---|---|---|
| node (1 proceso) | 249 | 269 | 57.0 ms | 114.6 ms | 118 MiB |
| node (2 procesos) | 399 | 407 | 34.3 ms | 84.4 ms | 277 MiB |
| php clásico (FrankenPHP) | 161 | 161 | 99.5 ms | 155.7 ms | 64 MiB |
| php worker (FrankenPHP) | 143 | 141 | 107.1 ms | 164.0 ms | 64 MiB |
| php worker + JIT | 160 | 160 | 99.9 ms | 154.8 ms | 63 MiB |

## 5 · Carga de CPU pura: /suma, a tope

`hey -c 16` desde otro contenedor; servidor con 2 CPU y 1g. «En frío»: los primeros 10 s tras arrancar. «Templado»: los 20 s siguientes.

| variante | peticiones/s en frío | peticiones/s templado | p50 | p99 | memoria máx. bajo carga |
|---|---|---|---|---|---|
| node (1 proceso) | 827 | 836 | 17.9 ms | 36.2 ms | 25 MiB |
| node (2 procesos) | 1658 | 1671 | 8.3 ms | 17.1 ms | 56 MiB |
| php clásico (FrankenPHP) | 2579 | 2590 | 6.3 ms | 11.1 ms | 33 MiB |
| php worker (FrankenPHP) | 2623 | 2647 | 6.1 ms | 11.1 ms | 34 MiB |
| php worker + JIT | 4122 | 4127 | 3.9 ms | 7.1 ms | 35 MiB |

## 6 · Latencia de una petición sola: /trabajo

Un solo cliente a 5 peticiones/s (`hey -c 1 -q 5`), 20 s, tras 10 s de calentamiento a tope. Cada petición llega sola: no hay cola, es lo que tarda el servidor en atender una.

| variante | peticiones/s logradas | p50 | p99 |
|---|---|---|---|
| node (1 proceso) | 5 | 4.10 ms | 4.90 ms |
| node (2 procesos) | 5 | 4.10 ms | 6.40 ms |
| php clásico (FrankenPHP) | 5 | 13.40 ms | 14.50 ms |
| php worker (FrankenPHP) | 5 | 15.30 ms | 16.30 ms |
| php worker + JIT | 5 | 13.90 ms | 15.50 ms |

## 7 · Latencia de una petición sola: /suma

Un solo cliente a 5 peticiones/s (`hey -c 1 -q 5`), 20 s, tras 10 s de calentamiento a tope. Cada petición llega sola: no hay cola, es lo que tarda el servidor en atender una.

| variante | peticiones/s logradas | p50 | p99 |
|---|---|---|---|
| node (1 proceso) | 5 | 1.70 ms | 2.40 ms |
| node (2 procesos) | 5 | 1.80 ms | 3.20 ms |
| php clásico (FrankenPHP) | 5 | 1.60 ms | 2.60 ms |
| php worker (FrankenPHP) | 5 | 1.50 ms | 2.70 ms |
| php worker + JIT | 5 | 1.20 ms | 1.70 ms |

