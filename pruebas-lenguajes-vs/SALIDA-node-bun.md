# SALIDA — ¿Node o Bun? (cultura-devops)

> Corrida del 2026-11-04 12:48. Regenerable con `python correr.py node bun`. ⛔ Ninguna cifra de blog: todo salió de aquí. Servidores de canales/golandia/recursos/pruebas-go-* (mismo contrato).

- node: `v24.22.2` — node:24-slim (node:http, sin dependencias)
- bun: `1.4.3` — oven/bun:1.4.3-slim (el mismo servidor.js)
- Docker `29.6.2`. Servidores con 2 CPU y 1g; `hey -c 16` con 4 CPU desde otro contenedor.
- /trabajo?n=20000: crea 20000 objetos, los mete en un mapa, los ordena y arma un JSON a mano. /suma?n=200000: multiplicar y módulo en un bucle.

## 1 · Construir la imagen desde cero (`docker build --no-cache`, dependencias incluidas; la imagen base ya descargada no cuenta)

| lenguaje | qué se cronometra | segundos |
|---|---|---|
| node | copiar servidor.js (no instala nada) | 0.6 |
| bun | copiar servidor.js (no instala nada) | 0.6 |

## 2 · Lo que despliegas

| imagen | base | tamaño en disco |
|---|---|---|
| node | node:24-slim (node:http, sin dependencias) | 77.3 MiB |
| bun | oven/bun:1.4.3-slim (el mismo servidor.js) | 70.6 MiB |

## 0 · ¿Hacen lo mismo? (antes de medir)

- node (1 proceso): total 9990000, primeros ids [0, 1000, 2000, 3000, 4000]…, suma 99863963591 → igual
- node (2 procesos): total 9990000, primeros ids [0, 1000, 2000, 3000, 4000]…, suma 99863963591 → igual
- bun (1 proceso): total 9990000, primeros ids [0, 1000, 2000, 3000, 4000]…, suma 99863963591 → igual
- bun (2 procesos): total 9990000, primeros ids [0, 1000, 2000, 3000, 4000]…, suma 99863963591 → igual

## 3 · Arranque: contenedor nuevo → primera respuesta 200 (mediana de 8) y memoria en reposo

| variante | 1ª respuesta (docker incluido) | «listo» (su propio reloj) | memoria en reposo |
|---|---|---|---|
| node (1 proceso) | 192 ms | 3.1 ms | 12.5 MiB |
| node (2 procesos) | 219 ms | 4.2 ms | 34.2 MiB |
| bun (1 proceso) | 207 ms | 0.2 ms | 3.9 MiB |
| bun (2 procesos) | 201 ms | 3.5 ms | 10.8 MiB |

## A · Cómputo de UNA petición (mediana del reloj del propio servidor, 30 de calentamiento + 200 medidas, de una en una)

| variante | /trabajo (20.000 objetos) | /suma (200.000 vueltas) |
|---|---|---|
| node (1 proceso) | 3.35 ms | 1.172 ms |
| node (2 procesos) | 3.47 ms | 1.186 ms |
| bun (1 proceso) | 4.15 ms | 1.603 ms |
| bun (2 procesos) | 4.57 ms | 1.612 ms |

## 4 · Carga con memoria: /trabajo (objetos, mapa, orden, JSON), a tope

`hey -c 16` desde otro contenedor; servidor con 2 CPU y 1g. «En frío»: los primeros 10 s tras arrancar. «Templado»: los 20 s siguientes.

| variante | peticiones/s en frío | peticiones/s templado | p50 | p99 | memoria máx. bajo carga |
|---|---|---|---|---|---|
| node (1 proceso) | 250 | 255 | 58.7 ms | 120.0 ms | 116 MiB |
| node (2 procesos) | 405 | 417 | 32.7 ms | 88.4 ms | 280 MiB |
| bun (1 proceso) | 237 | 241 | 62.2 ms | 129.0 ms | 29 MiB |
| bun (2 procesos) | 415 | 403 | 36.5 ms | 85.1 ms | 71 MiB |

## 5 · Carga de CPU pura: /suma, a tope

`hey -c 16` desde otro contenedor; servidor con 2 CPU y 1g. «En frío»: los primeros 10 s tras arrancar. «Templado»: los 20 s siguientes.

| variante | peticiones/s en frío | peticiones/s templado | p50 | p99 | memoria máx. bajo carga |
|---|---|---|---|---|---|
| node (1 proceso) | 822 | 826 | 18.1 ms | 36.9 ms | 23 MiB |
| node (2 procesos) | 1632 | 1644 | 8.4 ms | 18.3 ms | 55 MiB |
| bun (1 proceso) | 604 | 602 | 24.8 ms | 50.7 ms | 7 MiB |
| bun (2 procesos) | 1208 | 1207 | 13.0 ms | 26.9 ms | 17 MiB |

## 6 · Latencia de una petición sola: /trabajo

Un solo cliente a 5 peticiones/s (`hey -c 1 -q 5`), 20 s, tras 10 s de calentamiento a tope. Cada petición llega sola: no hay cola, es lo que tarda el servidor en atender una.

| variante | peticiones/s logradas | p50 | p99 |
|---|---|---|---|
| node (1 proceso) | 5 | 4.30 ms | 5.10 ms |
| node (2 procesos) | 5 | 4.20 ms | 5.20 ms |
| bun (1 proceso) | 5 | 5.20 ms | 7.80 ms |
| bun (2 procesos) | 5 | 5.10 ms | 8.10 ms |

## 7 · Latencia de una petición sola: /suma

Un solo cliente a 5 peticiones/s (`hey -c 1 -q 5`), 20 s, tras 10 s de calentamiento a tope. Cada petición llega sola: no hay cola, es lo que tarda el servidor en atender una.

| variante | peticiones/s logradas | p50 | p99 |
|---|---|---|---|
| node (1 proceso) | 5 | 1.70 ms | 2.50 ms |
| node (2 procesos) | 5 | 1.70 ms | 2.70 ms |
| bun (1 proceso) | 5 | 2.00 ms | 2.80 ms |
| bun (2 procesos) | 5 | 2.10 ms | 3.20 ms |

