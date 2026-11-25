# SALIDA — ¿Deno o Bun? (cultura-devops)

> Corrida del 2026-11-05 07:26. Regenerable con `python correr.py deno bun`. ⛔ Ninguna cifra de blog: todo salió de aquí. Servidores de canales/golandia/recursos/pruebas-go-* (mismo contrato).

- deno: `deno 2.9.8 (stable, release, x86_64-unknown-linux-gnu)` — denoland/deno:2.9.8 (Deno.serve)
- bun: `1.4.3` — oven/bun:1.4.3-slim (el mismo servidor.js)
- Docker `29.6.2`. Servidores con 2 CPU y 1g; `hey -c 16` con 4 CPU desde otro contenedor.
- /trabajo?n=20000: crea 20000 objetos, los mete en un mapa, los ordena y arma un JSON a mano. /suma?n=200000: multiplicar y módulo en un bucle.

## 1 · Construir la imagen desde cero (`docker build --no-cache`, dependencias incluidas; la imagen base ya descargada no cuenta)

| lenguaje | qué se cronometra | segundos |
|---|---|---|
| deno | copiar + deno check (comprobar tipos) | 1.6 |
| bun | copiar servidor.js (no instala nada) | 0.7 |

## 2 · Lo que despliegas

| imagen | base | tamaño en disco |
|---|---|---|
| deno | denoland/deno:2.9.8 (Deno.serve) | 70.5 MiB |
| bun | oven/bun:1.4.3-slim (el mismo servidor.js) | 70.6 MiB |

## 0 · ¿Hacen lo mismo? (antes de medir)

- deno (1 hilo): total 9990000, primeros ids [0, 1000, 2000, 3000, 4000]…, suma 99863963591 → igual
- deno serve --parallel: total 9990000, primeros ids [0, 1000, 2000, 3000, 4000]…, suma 99863963591 → igual
- bun (1 proceso): total 9990000, primeros ids [0, 1000, 2000, 3000, 4000]…, suma 99863963591 → igual
- bun (2 procesos): total 9990000, primeros ids [0, 1000, 2000, 3000, 4000]…, suma 99863963591 → igual

## 3 · Arranque: contenedor nuevo → primera respuesta 200 (mediana de 8) y memoria en reposo

| variante | 1ª respuesta (docker incluido) | «listo» (su propio reloj) | memoria en reposo |
|---|---|---|---|
| deno (1 hilo) | 242 ms | 5.6 ms | 19.9 MiB |
| deno serve --parallel | 236 ms | — | 30.4 MiB |
| bun (1 proceso) | 188 ms | 0.2 ms | 3.7 MiB |
| bun (2 procesos) | 196 ms | 3.5 ms | 11.1 MiB |

## A · Cómputo de UNA petición (mediana del reloj del propio servidor, 30 de calentamiento + 200 medidas, de una en una)

| variante | /trabajo (20.000 objetos) | /suma (200.000 vueltas) |
|---|---|---|
| deno (1 hilo) | 3.27 ms | 1.170 ms |
| deno serve --parallel | 3.34 ms | 1.169 ms |
| bun (1 proceso) | 4.22 ms | 1.608 ms |
| bun (2 procesos) | 4.29 ms | 1.610 ms |

## 4 · Carga con memoria: /trabajo (objetos, mapa, orden, JSON), a tope

`hey -c 16` desde otro contenedor; servidor con 2 CPU y 1g. «En frío»: los primeros 10 s tras arrancar. «Templado»: los 20 s siguientes.

| variante | peticiones/s en frío | peticiones/s templado | p50 | p99 | memoria máx. bajo carga |
|---|---|---|---|---|---|
| deno (1 hilo) | 246 | 250 | 59.9 ms | 87.2 ms | 115 MiB |
| deno serve --parallel | 476 | 472 | 23.9 ms | 80.8 ms | 146 MiB |
| bun (1 proceso) | 234 | 228 | 65.4 ms | 136.0 ms | 34 MiB |
| bun (2 procesos) | 391 | 400 | 33.8 ms | 77.4 ms | 61 MiB |

## 5 · Carga de CPU pura: /suma, a tope

`hey -c 16` desde otro contenedor; servidor con 2 CPU y 1g. «En frío»: los primeros 10 s tras arrancar. «Templado»: los 20 s siguientes.

| variante | peticiones/s en frío | peticiones/s templado | p50 | p99 | memoria máx. bajo carga |
|---|---|---|---|---|---|
| deno (1 hilo) | 825 | 830 | 19.2 ms | 20.4 ms | 26 MiB |
| deno serve --parallel | 1643 | 1607 | 17.6 ms | 18.9 ms | 40 MiB |
| bun (1 proceso) | 603 | 604 | 24.9 ms | 50.2 ms | 7 MiB |
| bun (2 procesos) | 1206 | 1199 | 14.8 ms | 30.3 ms | 17 MiB |

## 6 · Latencia de una petición sola: /trabajo

Un solo cliente a 5 peticiones/s (`hey -c 1 -q 5`), 20 s, tras 10 s de calentamiento a tope. Cada petición llega sola: no hay cola, es lo que tarda el servidor en atender una.

| variante | peticiones/s logradas | p50 | p99 |
|---|---|---|---|
| deno (1 hilo) | 5 | 4.40 ms | 6.00 ms |
| deno serve --parallel | 5 | 4.40 ms | 5.70 ms |
| bun (1 proceso) | 5 | 5.30 ms | 6.50 ms |
| bun (2 procesos) | 5 | 5.60 ms | 8.70 ms |

## 7 · Latencia de una petición sola: /suma

Un solo cliente a 5 peticiones/s (`hey -c 1 -q 5`), 20 s, tras 10 s de calentamiento a tope. Cada petición llega sola: no hay cola, es lo que tarda el servidor en atender una.

| variante | peticiones/s logradas | p50 | p99 |
|---|---|---|---|
| deno (1 hilo) | 5 | 1.60 ms | 2.20 ms |
| deno serve --parallel | 5 | 1.60 ms | 2.90 ms |
| bun (1 proceso) | 5 | 2.00 ms | 2.80 ms |
| bun (2 procesos) | 5 | 2.00 ms | 2.90 ms |

