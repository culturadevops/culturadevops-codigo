# SALIDA — ¿Node o Rust? (cultura-devops)

> Corrida del 2026-11-04 17:16. Regenerable con `python correr.py node rust`. ⛔ Ninguna cifra de blog: todo salió de aquí. Servidores de canales/golandia/recursos/pruebas-go-* (mismo contrato).

- node: `v24.22.2` — node:24-slim (node:http, sin dependencias)
- rust: `rustc 1.99.1 (58cf8f9c3 2026-10-13)` — debian:trixie-slim + binario (Rust 1.99.1, axum + tokio)
- Docker `29.6.2`. Servidores con 2 CPU y 1g; `hey -c 16` con 4 CPU desde otro contenedor.
- /trabajo?n=20000: crea 20000 objetos, los mete en un mapa, los ordena y arma un JSON a mano. /suma?n=200000: multiplicar y módulo en un bucle.

## 1 · Construir la imagen desde cero (`docker build --no-cache`, dependencias incluidas; la imagen base ya descargada no cuenta)

| lenguaje | qué se cronometra | segundos |
|---|---|---|
| node | copiar servidor.js (no instala nada) | 0.6 |
| rust | cargo build --release (descarga de crates incluida) | 11.1 |

## 2 · Lo que despliegas

| imagen | base | tamaño en disco |
|---|---|---|
| node | node:24-slim (node:http, sin dependencias) | 77.3 MiB |
| rust | debian:trixie-slim + binario (Rust 1.99.1, axum + tokio) | 29.0 MiB |

## 0 · ¿Hacen lo mismo? (antes de medir)

- node (1 proceso): total 9990000, primeros ids [0, 1000, 2000, 3000, 4000]…, suma 99863963591 → igual
- node (2 procesos): total 9990000, primeros ids [0, 1000, 2000, 3000, 4000]…, suma 99863963591 → igual
- rust (axum): total 9990000, primeros ids [0, 1000, 2000, 3000, 4000]…, suma 99863963591 → igual

## 3 · Arranque: contenedor nuevo → primera respuesta 200 (mediana de 8) y memoria en reposo

| variante | 1ª respuesta (docker incluido) | «listo» (su propio reloj) | memoria en reposo |
|---|---|---|---|
| node (1 proceso) | 218 ms | 3.2 ms | 12.7 MiB |
| node (2 procesos) | 240 ms | 4.1 ms | 34.1 MiB |
| rust (axum) | 188 ms | 0.0 ms | 1.9 MiB |

## A · Cómputo de UNA petición (mediana del reloj del propio servidor, 30 de calentamiento + 200 medidas, de una en una)

| variante | /trabajo (20.000 objetos) | /suma (200.000 vueltas) |
|---|---|---|
| node (1 proceso) | 3.46 ms | 1.175 ms |
| node (2 procesos) | 3.46 ms | 1.174 ms |
| rust (axum) | 1.76 ms | 0.111 ms |

## 4 · Carga con memoria: /trabajo (objetos, mapa, orden, JSON), a tope

`hey -c 16` desde otro contenedor; servidor con 2 CPU y 1g. «En frío»: los primeros 10 s tras arrancar. «Templado»: los 20 s siguientes.

| variante | peticiones/s en frío | peticiones/s templado | p50 | p99 | memoria máx. bajo carga |
|---|---|---|---|---|---|
| node (1 proceso) | 245 | 253 | 60.5 ms | 122.3 ms | 123 MiB |
| node (2 procesos) | 402 | 407 | 33.4 ms | 90.5 ms | 271 MiB |
| rust (axum) | 800 | 806 | 19.6 ms | 31.6 ms | 11 MiB |

## 5 · Carga de CPU pura: /suma, a tope

`hey -c 16` desde otro contenedor; servidor con 2 CPU y 1g. «En frío»: los primeros 10 s tras arrancar. «Templado»: los 20 s siguientes.

| variante | peticiones/s en frío | peticiones/s templado | p50 | p99 | memoria máx. bajo carga |
|---|---|---|---|---|---|
| node (1 proceso) | 808 | 814 | 18.4 ms | 37.5 ms | 22 MiB |
| node (2 procesos) | 1604 | 1632 | 9.5 ms | 20.1 ms | 55 MiB |
| rust (axum) | 16465 | 16438 | 1.0 ms | 1.7 ms | 4 MiB |

## 6 · Latencia de una petición sola: /trabajo

Un solo cliente a 5 peticiones/s (`hey -c 1 -q 5`), 20 s, tras 10 s de calentamiento a tope. Cada petición llega sola: no hay cola, es lo que tarda el servidor en atender una.

| variante | peticiones/s logradas | p50 | p99 |
|---|---|---|---|
| node (1 proceso) | 5 | 4.40 ms | 6.80 ms |
| node (2 procesos) | 5 | 4.80 ms | 9.60 ms |
| rust (axum) | 5 | 3.40 ms | 4.20 ms |

## 7 · Latencia de una petición sola: /suma

Un solo cliente a 5 peticiones/s (`hey -c 1 -q 5`), 20 s, tras 10 s de calentamiento a tope. Cada petición llega sola: no hay cola, es lo que tarda el servidor en atender una.

| variante | peticiones/s logradas | p50 | p99 |
|---|---|---|---|
| node (1 proceso) | 5 | 1.70 ms | 2.50 ms |
| node (2 procesos) | 5 | 1.70 ms | 2.80 ms |
| rust (axum) | 5 | 0.50 ms | 2.60 ms |

