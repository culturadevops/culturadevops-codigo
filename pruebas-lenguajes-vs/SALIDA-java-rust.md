# SALIDA — ¿Java o Rust? (cultura-devops)

> Corrida del 2026-11-04 17:08. Regenerable con `python correr.py java rust`. ⛔ Ninguna cifra de blog: todo salió de aquí. Servidores de canales/golandia/recursos/pruebas-go-* (mismo contrato).

- java: `openjdk version "25.0.5" 2026-10-20 LTS` — eclipse-temurin:25-jre + jar (com.sun.net.httpserver)
- rust: `rustc 1.99.1 (58cf8f9c3 2026-10-13)` — debian:trixie-slim + binario (Rust 1.99.1, axum + tokio)
- Docker `29.6.2`. Servidores con 2 CPU y 1g; `hey -c 16` con 4 CPU desde otro contenedor.
- /trabajo?n=20000: crea 20000 objetos, los mete en un mapa, los ordena y arma un JSON a mano. /suma?n=200000: multiplicar y módulo en un bucle.

## 1 · Construir la imagen desde cero (`docker build --no-cache`, dependencias incluidas; la imagen base ya descargada no cuenta)

| lenguaje | qué se cronometra | segundos |
|---|---|---|
| java | javac + jar | 1.3 |
| rust | cargo build --release (descarga de crates incluida) | 10.6 |

## 2 · Lo que despliegas

| imagen | base | tamaño en disco |
|---|---|---|
| java | eclipse-temurin:25-jre + jar (com.sun.net.httpserver) | 112.0 MiB |
| rust | debian:trixie-slim + binario (Rust 1.99.1, axum + tokio) | 29.0 MiB |

## 0 · ¿Hacen lo mismo? (antes de medir)

- java (hilos virtuales): total 9990000, primeros ids [0, 1000, 2000, 3000, 4000]…, suma 99863963591 → igual
- java (hilos de plataforma): total 9990000, primeros ids [0, 1000, 2000, 3000, 4000]…, suma 99863963591 → igual
- rust (axum): total 9990000, primeros ids [0, 1000, 2000, 3000, 4000]…, suma 99863963591 → igual

## 3 · Arranque: contenedor nuevo → primera respuesta 200 (mediana de 8) y memoria en reposo

| variante | 1ª respuesta (docker incluido) | «listo» (su propio reloj) | memoria en reposo |
|---|---|---|---|
| java (hilos virtuales) | 262 ms | 18.1 ms | 34.7 MiB |
| java (hilos de plataforma) | 256 ms | 18.2 ms | 34.0 MiB |
| rust (axum) | 189 ms | 0.0 ms | 1.8 MiB |

## A · Cómputo de UNA petición (mediana del reloj del propio servidor, 30 de calentamiento + 200 medidas, de una en una)

| variante | /trabajo (20.000 objetos) | /suma (200.000 vueltas) |
|---|---|---|
| java (hilos virtuales) | 1.93 ms | 0.098 ms |
| java (hilos de plataforma) | 1.98 ms | 0.098 ms |
| rust (axum) | 1.75 ms | 0.111 ms |

## 4 · Carga con memoria: /trabajo (objetos, mapa, orden, JSON), a tope

`hey -c 16` desde otro contenedor; servidor con 2 CPU y 1g. «En frío»: los primeros 10 s tras arrancar. «Templado»: los 20 s siguientes.

| variante | peticiones/s en frío | peticiones/s templado | p50 | p99 | memoria máx. bajo carga |
|---|---|---|---|---|---|
| java (hilos virtuales) | 981 | 1070 | 14.5 ms | 18.5 ms | 294 MiB |
| java (hilos de plataforma) | 978 | 1048 | 15.2 ms | 20.4 ms | 289 MiB |
| rust (axum) | 816 | 807 | 19.6 ms | 32.0 ms | 10 MiB |

## 5 · Carga de CPU pura: /suma, a tope

`hey -c 16` desde otro contenedor; servidor con 2 CPU y 1g. «En frío»: los primeros 10 s tras arrancar. «Templado»: los 20 s siguientes.

| variante | peticiones/s en frío | peticiones/s templado | p50 | p99 | memoria máx. bajo carga |
|---|---|---|---|---|---|
| java (hilos virtuales) | 13260 | 14414 | 0.4 ms | 21.7 ms | 57 MiB |
| java (hilos de plataforma) | 15485 | 16428 | 0.9 ms | 1.9 ms | 55 MiB |
| rust (axum) | 16566 | 16505 | 1.0 ms | 1.6 ms | 3 MiB |

## 6 · Latencia de una petición sola: /trabajo

Un solo cliente a 5 peticiones/s (`hey -c 1 -q 5`), 20 s, tras 10 s de calentamiento a tope. Cada petición llega sola: no hay cola, es lo que tarda el servidor en atender una.

| variante | peticiones/s logradas | p50 | p99 |
|---|---|---|---|
| java (hilos virtuales) | 5 | 2.40 ms | 3.90 ms |
| java (hilos de plataforma) | 5 | 2.40 ms | 4.90 ms |
| rust (axum) | 5 | 3.50 ms | 4.40 ms |

## 7 · Latencia de una petición sola: /suma

Un solo cliente a 5 peticiones/s (`hey -c 1 -q 5`), 20 s, tras 10 s de calentamiento a tope. Cada petición llega sola: no hay cola, es lo que tarda el servidor en atender una.

| variante | peticiones/s logradas | p50 | p99 |
|---|---|---|---|
| java (hilos virtuales) | 5 | 0.60 ms | 1.50 ms |
| java (hilos de plataforma) | 5 | 0.70 ms | 1.50 ms |
| rust (axum) | 5 | 0.50 ms | 1.40 ms |

