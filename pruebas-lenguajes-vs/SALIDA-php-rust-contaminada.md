# SALIDA — ¿PHP o Rust? (cultura-devops)

> Corrida del 2026-11-04 16:45. Regenerable con `python correr.py php rust`. ⛔ Ninguna cifra de blog: todo salió de aquí. Servidores de canales/golandia/recursos/pruebas-go-* (mismo contrato).

- php: `FrankenPHP v1.13.3 PHP 8.5.12 Caddy v2.11.7 h1:yj0Y4fYZGPkSvibBJ1sTWE33xC0fxztVyXEW5iIdUT4=` — dunglas/frankenphp:1.13.3-php8.5
- rust: `rustc 1.99.1 (58cf8f9c3 2026-10-13)` — debian:trixie-slim + binario (Rust 1.99.1, axum + tokio)
- Docker `29.6.2`. Servidores con 2 CPU y 1g; `hey -c 16` con 4 CPU desde otro contenedor.
- /trabajo?n=20000: crea 20000 objetos, los mete en un mapa, los ordena y arma un JSON a mano. /suma?n=200000: multiplicar y módulo en un bucle.

## 1 · Construir la imagen desde cero (`docker build --no-cache`, dependencias incluidas; la imagen base ya descargada no cuenta)

| lenguaje | qué se cronometra | segundos |
|---|---|---|
| php | copiar el código (PHP no compila) | 0.7 |
| rust | cargo build --release (descarga de crates incluida) | 10.8 |

## 2 · Lo que despliegas

| imagen | base | tamaño en disco |
|---|---|---|
| php | dunglas/frankenphp:1.13.3-php8.5 | 201.2 MiB |
| rust | debian:trixie-slim + binario (Rust 1.99.1, axum + tokio) | 29.0 MiB |

## 0 · ¿Hacen lo mismo? (antes de medir)

- php clásico (FrankenPHP): total 9990000, primeros ids [0, 1000, 2000, 3000, 4000]…, suma 99863963591 → igual
- php worker (FrankenPHP): total 9990000, primeros ids [0, 1000, 2000, 3000, 4000]…, suma 99863963591 → igual
- php worker + JIT: total 9990000, primeros ids [0, 1000, 2000, 3000, 4000]…, suma 99863963591 → igual
- rust (axum): total 9990000, primeros ids [0, 1000, 2000, 3000, 4000]…, suma 99863963591 → igual

## 3 · Arranque: contenedor nuevo → primera respuesta 200 (mediana de 8) y memoria en reposo

| variante | 1ª respuesta (docker incluido) | «listo» (su propio reloj) | memoria en reposo |
|---|---|---|---|
| php clásico (FrankenPHP) | 241 ms | — | 24.6 MiB |
| php worker (FrankenPHP) | 239 ms | 0.0 ms | 25.5 MiB |
| php worker + JIT | 249 ms | 0.0 ms | 26.2 MiB |
| rust (axum) | 201 ms | 0.0 ms | 1.9 MiB |

## A · Cómputo de UNA petición (mediana del reloj del propio servidor, 30 de calentamiento + 200 medidas, de una en una)

| variante | /trabajo (20.000 objetos) | /suma (200.000 vueltas) |
|---|---|---|
| php clásico (FrankenPHP) | 11.68 ms | 0.664 ms |
| php worker (FrankenPHP) | 13.59 ms | 0.677 ms |
| php worker + JIT | 11.91 ms | 0.401 ms |
| rust (axum) | 1.79 ms | 0.111 ms |

## 4 · Carga con memoria: /trabajo (objetos, mapa, orden, JSON), a tope

`hey -c 16` desde otro contenedor; servidor con 2 CPU y 1g. «En frío»: los primeros 10 s tras arrancar. «Templado»: los 20 s siguientes.

| variante | peticiones/s en frío | peticiones/s templado | p50 | p99 | memoria máx. bajo carga |
|---|---|---|---|---|---|
| php clásico (FrankenPHP) | 156 | 156 | 101.0 ms | 157.1 ms | 64 MiB |
| php worker (FrankenPHP) | 135 | 132 | 110.5 ms | 171.3 ms | 62 MiB |
| php worker + JIT | 153 | 151 | 102.9 ms | 160.6 ms | 65 MiB |
| rust (axum) | 808 | 811 | 19.5 ms | 31.2 ms | 11 MiB |

## 5 · Carga de CPU pura: /suma, a tope

`hey -c 16` desde otro contenedor; servidor con 2 CPU y 1g. «En frío»: los primeros 10 s tras arrancar. «Templado»: los 20 s siguientes.

| variante | peticiones/s en frío | peticiones/s templado | p50 | p99 | memoria máx. bajo carga |
|---|---|---|---|---|---|
| php clásico (FrankenPHP) | 2516 | 2519 | 6.3 ms | 11.8 ms | 33 MiB |
| php worker (FrankenPHP) | 2551 | 2518 | 6.4 ms | 11.6 ms | 33 MiB |
| php worker + JIT | 3861 | 3834 | 4.2 ms | 7.7 ms | 34 MiB |
| rust (axum) | 15701 | 16279 | 1.0 ms | 1.7 ms | 5 MiB |

## 6 · Latencia de una petición sola: /trabajo

Un solo cliente a 5 peticiones/s (`hey -c 1 -q 5`), 20 s, tras 10 s de calentamiento a tope. Cada petición llega sola: no hay cola, es lo que tarda el servidor en atender una.

| variante | peticiones/s logradas | p50 | p99 |
|---|---|---|---|
| php clásico (FrankenPHP) | 5 | 13.40 ms | 14.50 ms |
| php worker (FrankenPHP) | 5 | 15.70 ms | 17.70 ms |
| php worker + JIT | 5 | 13.90 ms | 17.10 ms |
| rust (axum) | 5 | 3.10 ms | 5.90 ms |

## 7 · Latencia de una petición sola: /suma

Un solo cliente a 5 peticiones/s (`hey -c 1 -q 5`), 20 s, tras 10 s de calentamiento a tope. Cada petición llega sola: no hay cola, es lo que tarda el servidor en atender una.

| variante | peticiones/s logradas | p50 | p99 |
|---|---|---|---|
| php clásico (FrankenPHP) | 5 | 1.50 ms | 2.10 ms |
| php worker (FrankenPHP) | 5 | 1.40 ms | 2.60 ms |
| php worker + JIT | 5 | 1.30 ms | 3.30 ms |
| rust (axum) | 5 | 0.50 ms | 1.50 ms |

