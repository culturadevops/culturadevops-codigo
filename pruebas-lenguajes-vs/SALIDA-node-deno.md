# SALIDA — ¿Node o Deno? (cultura-devops)

> Corrida del 2026-11-04 12:58. Regenerable con `python correr.py node deno`. ⛔ Ninguna cifra de blog: todo salió de aquí. Servidores de canales/golandia/recursos/pruebas-go-* (mismo contrato).

- node: `v24.22.2` — node:24-slim (node:http, sin dependencias)
- deno: `deno 2.9.8 (stable, release, x86_64-unknown-linux-gnu)` — denoland/deno:2.9.8 (Deno.serve)
- Docker `29.6.2`. Servidores con 2 CPU y 1g; `hey -c 16` con 4 CPU desde otro contenedor.
- /trabajo?n=20000: crea 20000 objetos, los mete en un mapa, los ordena y arma un JSON a mano. /suma?n=200000: multiplicar y módulo en un bucle.

## 1 · Construir la imagen desde cero (`docker build --no-cache`, dependencias incluidas; la imagen base ya descargada no cuenta)

| lenguaje | qué se cronometra | segundos |
|---|---|---|
| node | copiar servidor.js (no instala nada) | 0.6 |
| deno | copiar + deno check (comprobar tipos) | 1.2 |

## 2 · Lo que despliegas

| imagen | base | tamaño en disco |
|---|---|---|
| node | node:24-slim (node:http, sin dependencias) | 77.3 MiB |
| deno | denoland/deno:2.9.8 (Deno.serve) | 70.5 MiB |

## 0 · ¿Hacen lo mismo? (antes de medir)

- node (1 proceso): total 9990000, primeros ids [0, 1000, 2000, 3000, 4000]…, suma 99863963591 → igual
- node (2 procesos): total 9990000, primeros ids [0, 1000, 2000, 3000, 4000]…, suma 99863963591 → igual
- deno (1 hilo): total 9990000, primeros ids [0, 1000, 2000, 3000, 4000]…, suma 99863963591 → igual
- deno serve --parallel: total 9990000, primeros ids [0, 1000, 2000, 3000, 4000]…, suma 99863963591 → igual

## 3 · Arranque: contenedor nuevo → primera respuesta 200 (mediana de 8) y memoria en reposo

| variante | 1ª respuesta (docker incluido) | «listo» (su propio reloj) | memoria en reposo |
|---|---|---|---|
| node (1 proceso) | 198 ms | 2.9 ms | 12.6 MiB |
| node (2 procesos) | 228 ms | 3.8 ms | 34.2 MiB |
| deno (1 hilo) | 254 ms | 5.1 ms | 20.1 MiB |
| deno serve --parallel | 256 ms | — | 30.6 MiB |

## A · Cómputo de UNA petición (mediana del reloj del propio servidor, 30 de calentamiento + 200 medidas, de una en una)

| variante | /trabajo (20.000 objetos) | /suma (200.000 vueltas) |
|---|---|---|
| node (1 proceso) | 3.24 ms | 1.167 ms |
| node (2 procesos) | 3.43 ms | 1.174 ms |
| deno (1 hilo) | 2.95 ms | 1.165 ms |
| deno serve --parallel | 3.14 ms | 1.165 ms |

## 4 · Carga con memoria: /trabajo (objetos, mapa, orden, JSON), a tope

`hey -c 16` desde otro contenedor; servidor con 2 CPU y 1g. «En frío»: los primeros 10 s tras arrancar. «Templado»: los 20 s siguientes.

| variante | peticiones/s en frío | peticiones/s templado | p50 | p99 | memoria máx. bajo carga |
|---|---|---|---|---|---|
| node (1 proceso) | 260 | 263 | 56.9 ms | 115.2 ms | 123 MiB |
| node (2 procesos) | 425 | 434 | 31.1 ms | 86.2 ms | 266 MiB |
| deno (1 hilo) | 254 | 257 | 58.3 ms | 85.8 ms | 126 MiB |
| deno serve --parallel | 481 | 493 | 15.9 ms | 84.2 ms | 150 MiB |

## 5 · Carga de CPU pura: /suma, a tope

`hey -c 16` desde otro contenedor; servidor con 2 CPU y 1g. «En frío»: los primeros 10 s tras arrancar. «Templado»: los 20 s siguientes.

| variante | peticiones/s en frío | peticiones/s templado | p50 | p99 | memoria máx. bajo carga |
|---|---|---|---|---|---|
| node (1 proceso) | 819 | 836 | 17.9 ms | 36.2 ms | 23 MiB |
| node (2 procesos) | 1641 | 1671 | 8.3 ms | 17.7 ms | 54 MiB |
| deno (1 hilo) | 841 | 845 | 18.9 ms | 19.5 ms | 26 MiB |
| deno serve --parallel | 841 | 1692 | 9.2 ms | 13.2 ms | 40 MiB |

## 6 · Latencia de una petición sola: /trabajo

Un solo cliente a 5 peticiones/s (`hey -c 1 -q 5`), 20 s, tras 10 s de calentamiento a tope. Cada petición llega sola: no hay cola, es lo que tarda el servidor en atender una.

| variante | peticiones/s logradas | p50 | p99 |
|---|---|---|---|
| node (1 proceso) | 5 | 4.30 ms | 5.20 ms |
| node (2 procesos) | 5 | 4.20 ms | 5.90 ms |
| deno (1 hilo) | 5 | 4.30 ms | 5.50 ms |
| deno serve --parallel | 5 | 4.30 ms | 6.70 ms |

## 7 · Latencia de una petición sola: /suma

Un solo cliente a 5 peticiones/s (`hey -c 1 -q 5`), 20 s, tras 10 s de calentamiento a tope. Cada petición llega sola: no hay cola, es lo que tarda el servidor en atender una.

| variante | peticiones/s logradas | p50 | p99 |
|---|---|---|---|
| node (1 proceso) | 5 | 1.80 ms | 2.60 ms |
| node (2 procesos) | 5 | 1.80 ms | 2.90 ms |
| deno (1 hilo) | 5 | 1.70 ms | 2.30 ms |
| deno serve --parallel | 5 | 1.70 ms | 2.60 ms |

