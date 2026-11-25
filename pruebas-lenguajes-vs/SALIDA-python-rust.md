# SALIDA — ¿Python o Rust? (cultura-devops)

> Corrida del 2026-11-04 13:19. Regenerable con `python correr.py python rust`. ⛔ Ninguna cifra de blog: todo salió de aquí. Servidores de canales/golandia/recursos/pruebas-go-* (mismo contrato).

- python: `Python 3.13.17` — python:3.13.17-slim + FastAPI 0.162 + uvicorn 0.54
- rust: `rustc 1.99.1 (58cf8f9c3 2026-10-13)` — debian:trixie-slim + binario (Rust 1.99.1, axum + tokio)
- Docker `29.6.2`. Servidores con 2 CPU y 1g; `hey -c 16` con 4 CPU desde otro contenedor.
- /trabajo?n=20000: crea 20000 objetos, los mete en un mapa, los ordena y arma un JSON a mano. /suma?n=200000: multiplicar y módulo en un bucle.

## 1 · Construir la imagen desde cero (`docker build --no-cache`, dependencias incluidas; la imagen base ya descargada no cuenta)

| lenguaje | qué se cronometra | segundos |
|---|---|---|
| python | pip install de FastAPI + uvicorn | 5.1 |
| rust | cargo build --release (descarga de crates incluida) | 10.4 |

## 2 · Lo que despliegas

| imagen | base | tamaño en disco |
|---|---|---|
| python | python:3.13.17-slim + FastAPI 0.162 + uvicorn 0.54 | 56.3 MiB |
| rust | debian:trixie-slim + binario (Rust 1.99.1, axum + tokio) | 29.0 MiB |

## 0 · ¿Hacen lo mismo? (antes de medir)

- python (1 proceso): total 9990000, primeros ids [0, 1000, 2000, 3000, 4000]…, suma 99863963591 → igual
- python (2 procesos): total 9990000, primeros ids [0, 1000, 2000, 3000, 4000]…, suma 99863963591 → igual
- rust (axum): total 9990000, primeros ids [0, 1000, 2000, 3000, 4000]…, suma 99863963591 → igual

## 3 · Arranque: contenedor nuevo → primera respuesta 200 (mediana de 8) y memoria en reposo

| variante | 1ª respuesta (docker incluido) | «listo» (su propio reloj) | memoria en reposo |
|---|---|---|---|
| python (1 proceso) | 434 ms | 121.6 ms | 36.9 MiB |
| python (2 procesos) | 481 ms | 106.9 ms | 95.5 MiB |
| rust (axum) | 197 ms | 0.0 ms | 2.0 MiB |

## A · Cómputo de UNA petición (mediana del reloj del propio servidor, 30 de calentamiento + 200 medidas, de una en una)

| variante | /trabajo (20.000 objetos) | /suma (200.000 vueltas) |
|---|---|---|
| python (1 proceso) | 8.25 ms | 8.184 ms |
| python (2 procesos) | 8.57 ms | 8.246 ms |
| rust (axum) | 1.72 ms | 0.111 ms |

## 4 · Carga con memoria: /trabajo (objetos, mapa, orden, JSON), a tope

`hey -c 16` desde otro contenedor; servidor con 2 CPU y 1g. «En frío»: los primeros 10 s tras arrancar. «Templado»: los 20 s siguientes.

| variante | peticiones/s en frío | peticiones/s templado | p50 | p99 | memoria máx. bajo carga |
|---|---|---|---|---|---|
| python (1 proceso) | 78 | 76 | 197.1 ms | 468.8 ms | 97 MiB |
| python (2 procesos) | 152 | 150 | 100.6 ms | 237.3 ms | 167 MiB |
| rust (axum) | 844 | 842 | 18.8 ms | 30.1 ms | 11 MiB |

## 5 · Carga de CPU pura: /suma, a tope

`hey -c 16` desde otro contenedor; servidor con 2 CPU y 1g. «En frío»: los primeros 10 s tras arrancar. «Templado»: los 20 s siguientes.

| variante | peticiones/s en frío | peticiones/s templado | p50 | p99 | memoria máx. bajo carga |
|---|---|---|---|---|---|
| python (1 proceso) | 118 | 118 | 130.2 ms | 309.4 ms | 42 MiB |
| python (2 procesos) | 235 | 235 | 64.8 ms | 146.1 ms | 100 MiB |
| rust (axum) | 16755 | 16766 | 0.9 ms | 1.6 ms | 3 MiB |

## 6 · Latencia de una petición sola: /trabajo

Un solo cliente a 5 peticiones/s (`hey -c 1 -q 5`), 20 s, tras 10 s de calentamiento a tope. Cada petición llega sola: no hay cola, es lo que tarda el servidor en atender una.

| variante | peticiones/s logradas | p50 | p99 |
|---|---|---|---|
| python (1 proceso) | 5 | 11.00 ms | 24.30 ms |
| python (2 procesos) | 5 | 11.00 ms | 22.70 ms |
| rust (axum) | 5 | 3.40 ms | 4.30 ms |

## 7 · Latencia de una petición sola: /suma

Un solo cliente a 5 peticiones/s (`hey -c 1 -q 5`), 20 s, tras 10 s de calentamiento a tope. Cada petición llega sola: no hay cola, es lo que tarda el servidor en atender una.

| variante | peticiones/s logradas | p50 | p99 |
|---|---|---|---|
| python (1 proceso) | 5 | 9.40 ms | 10.80 ms |
| python (2 procesos) | 5 | 9.30 ms | 10.20 ms |
| rust (axum) | 5 | 0.60 ms | 1.10 ms |

