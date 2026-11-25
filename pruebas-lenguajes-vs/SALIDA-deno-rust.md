# SALIDA — ¿Deno o Rust? (cultura-devops)

> Corrida del 2026-11-05 08:11. Regenerable con `python correr.py deno rust`. ⛔ Ninguna cifra de blog: todo salió de aquí. Servidores de canales/golandia/recursos/pruebas-go-* (mismo contrato).

- deno: `deno 2.9.8 (stable, release, x86_64-unknown-linux-gnu)` — denoland/deno:2.9.8 (Deno.serve)
- rust: `rustc 1.99.1 (58cf8f9c3 2026-10-13)` — debian:trixie-slim + binario (Rust 1.99.1, axum + tokio)
- Docker `29.6.2`. Servidores con 2 CPU y 1g; `hey -c 16` con 4 CPU desde otro contenedor.
- /trabajo?n=20000: crea 20000 objetos, los mete en un mapa, los ordena y arma un JSON a mano. /suma?n=200000: multiplicar y módulo en un bucle.

## 1 · Construir la imagen desde cero (`docker build --no-cache`, dependencias incluidas; la imagen base ya descargada no cuenta)

| lenguaje | qué se cronometra | segundos |
|---|---|---|
| deno | copiar + deno check (comprobar tipos) | 2.9 |
| rust | cargo build --release (descarga de crates incluida) | 13.0 |

## 2 · Lo que despliegas

| imagen | base | tamaño en disco |
|---|---|---|
| deno | denoland/deno:2.9.8 (Deno.serve) | 70.5 MiB |
| rust | debian:trixie-slim + binario (Rust 1.99.1, axum + tokio) | 29.0 MiB |

## 0 · ¿Hacen lo mismo? (antes de medir)

- deno (1 hilo): total 9990000, primeros ids [0, 1000, 2000, 3000, 4000]…, suma 99863963591 → igual
- deno serve --parallel: total 9990000, primeros ids [0, 1000, 2000, 3000, 4000]…, suma 99863963591 → igual
- rust (axum): total 9990000, primeros ids [0, 1000, 2000, 3000, 4000]…, suma 99863963591 → igual

## 3 · Arranque: contenedor nuevo → primera respuesta 200 (mediana de 8) y memoria en reposo

| variante | 1ª respuesta (docker incluido) | «listo» (su propio reloj) | memoria en reposo |
|---|---|---|---|
| deno (1 hilo) | 254 ms | 5.4 ms | 20.2 MiB |
| deno serve --parallel | 264 ms | — | 30.7 MiB |
| rust (axum) | 228 ms | 0.0 ms | 0.9 MiB |

## A · Cómputo de UNA petición (mediana del reloj del propio servidor, 30 de calentamiento + 200 medidas, de una en una)

| variante | /trabajo (20.000 objetos) | /suma (200.000 vueltas) |
|---|---|---|
| deno (1 hilo) | 3.03 ms | 1.182 ms |
| deno serve --parallel | 3.26 ms | 1.193 ms |
| rust (axum) | 1.76 ms | 0.111 ms |

## 4 · Carga con memoria: /trabajo (objetos, mapa, orden, JSON), a tope

`hey -c 16` desde otro contenedor; servidor con 2 CPU y 1g. «En frío»: los primeros 10 s tras arrancar. «Templado»: los 20 s siguientes.

| variante | peticiones/s en frío | peticiones/s templado | p50 | p99 | memoria máx. bajo carga |
|---|---|---|---|---|---|
| deno (1 hilo) | 253 | 251 | 59.4 ms | 89.2 ms | 116 MiB |
| deno serve --parallel | 427 | 469 | 33.2 ms | 57.3 ms | 136 MiB |
| rust (axum) | 830 | 831 | 18.9 ms | 31.1 ms | 11 MiB |

## 5 · Carga de CPU pura: /suma, a tope

`hey -c 16` desde otro contenedor; servidor con 2 CPU y 1g. «En frío»: los primeros 10 s tras arrancar. «Templado»: los 20 s siguientes.

| variante | peticiones/s en frío | peticiones/s templado | p50 | p99 | memoria máx. bajo carga |
|---|---|---|---|---|---|
| deno (1 hilo) | 830 | 837 | 19.0 ms | 21.9 ms | 25 MiB |
| deno serve --parallel | 827 | 1606 | 17.5 ms | 19.7 ms | 38 MiB |
| rust (axum) | 16764 | 16551 | 0.9 ms | 1.6 ms | 4 MiB |

## 6 · Latencia de una petición sola: /trabajo

Un solo cliente a 5 peticiones/s (`hey -c 1 -q 5`), 20 s, tras 10 s de calentamiento a tope. Cada petición llega sola: no hay cola, es lo que tarda el servidor en atender una.

| variante | peticiones/s logradas | p50 | p99 |
|---|---|---|---|
| deno (1 hilo) | 5 | 4.70 ms | 9.30 ms |
| deno serve --parallel | 5 | 5.50 ms | 9.00 ms |
| rust (axum) | 5 | 3.40 ms | 8.50 ms |

## 7 · Latencia de una petición sola: /suma

Un solo cliente a 5 peticiones/s (`hey -c 1 -q 5`), 20 s, tras 10 s de calentamiento a tope. Cada petición llega sola: no hay cola, es lo que tarda el servidor en atender una.

| variante | peticiones/s logradas | p50 | p99 |
|---|---|---|---|
| deno (1 hilo) | 5 | 3.30 ms | 6.20 ms |
| deno serve --parallel | 5 | 1.70 ms | 6.10 ms |
| rust (axum) | 5 | 0.50 ms | 3.00 ms |

