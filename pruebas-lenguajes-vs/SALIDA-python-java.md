# SALIDA — ¿Python o Java? (cultura-devops)

> Corrida del 2026-11-04 13:08. Regenerable con `python correr.py python java`. ⛔ Ninguna cifra de blog: todo salió de aquí. Servidores de canales/golandia/recursos/pruebas-go-* (mismo contrato).

- python: `Python 3.13.17` — python:3.13.17-slim + FastAPI 0.162 + uvicorn 0.54
- java: `Unable to find image 'eclipse-temurin:25-jdk' locally` — eclipse-temurin:25-jre + jar (com.sun.net.httpserver)
- Docker `29.6.2`. Servidores con 2 CPU y 1g; `hey -c 16` con 4 CPU desde otro contenedor.
- /trabajo?n=20000: crea 20000 objetos, los mete en un mapa, los ordena y arma un JSON a mano. /suma?n=200000: multiplicar y módulo en un bucle.

## 1 · Construir la imagen desde cero (`docker build --no-cache`, dependencias incluidas; la imagen base ya descargada no cuenta)

| lenguaje | qué se cronometra | segundos |
|---|---|---|
| python | pip install de FastAPI + uvicorn | 5.2 |
| java | javac + jar | 1.2 |

## 2 · Lo que despliegas

| imagen | base | tamaño en disco |
|---|---|---|
| python | python:3.13.17-slim + FastAPI 0.162 + uvicorn 0.54 | 56.3 MiB |
| java | eclipse-temurin:25-jre + jar (com.sun.net.httpserver) | 112.0 MiB |

## 0 · ¿Hacen lo mismo? (antes de medir)

- python (1 proceso): total 9990000, primeros ids [0, 1000, 2000, 3000, 4000]…, suma 99863963591 → igual
- python (2 procesos): total 9990000, primeros ids [0, 1000, 2000, 3000, 4000]…, suma 99863963591 → igual
- java (hilos virtuales): total 9990000, primeros ids [0, 1000, 2000, 3000, 4000]…, suma 99863963591 → igual
- java (hilos de plataforma): total 9990000, primeros ids [0, 1000, 2000, 3000, 4000]…, suma 99863963591 → igual

## 3 · Arranque: contenedor nuevo → primera respuesta 200 (mediana de 8) y memoria en reposo

| variante | 1ª respuesta (docker incluido) | «listo» (su propio reloj) | memoria en reposo |
|---|---|---|---|
| python (1 proceso) | 446 ms | 126.1 ms | 37.1 MiB |
| python (2 procesos) | 494 ms | 109.8 ms | 95.6 MiB |
| java (hilos virtuales) | 254 ms | 16.8 ms | 34.7 MiB |
| java (hilos de plataforma) | 248 ms | 17.4 ms | 34.5 MiB |

## A · Cómputo de UNA petición (mediana del reloj del propio servidor, 30 de calentamiento + 200 medidas, de una en una)

| variante | /trabajo (20.000 objetos) | /suma (200.000 vueltas) |
|---|---|---|
| python (1 proceso) | 8.26 ms | 8.155 ms |
| python (2 procesos) | 8.90 ms | 8.248 ms |
| java (hilos virtuales) | 1.84 ms | 0.098 ms |
| java (hilos de plataforma) | 1.91 ms | 0.098 ms |

## 4 · Carga con memoria: /trabajo (objetos, mapa, orden, JSON), a tope

`hey -c 16` desde otro contenedor; servidor con 2 CPU y 1g. «En frío»: los primeros 10 s tras arrancar. «Templado»: los 20 s siguientes.

| variante | peticiones/s en frío | peticiones/s templado | p50 | p99 | memoria máx. bajo carga |
|---|---|---|---|---|---|
| python (1 proceso) | 77 | 76 | 196.3 ms | 487.0 ms | 97 MiB |
| python (2 procesos) | 153 | 153 | 98.9 ms | 235.1 ms | 172 MiB |
| java (hilos virtuales) | 1035 | 1124 | 13.4 ms | 16.6 ms | 292 MiB |
| java (hilos de plataforma) | 1035 | 1128 | 14.3 ms | 16.5 ms | 293 MiB |

## 5 · Carga de CPU pura: /suma, a tope

`hey -c 16` desde otro contenedor; servidor con 2 CPU y 1g. «En frío»: los primeros 10 s tras arrancar. «Templado»: los 20 s siguientes.

| variante | peticiones/s en frío | peticiones/s templado | p50 | p99 | memoria máx. bajo carga |
|---|---|---|---|---|---|
| python (1 proceso) | 115 | 115 | 132.2 ms | 303.8 ms | 42 MiB |
| python (2 procesos) | 231 | 233 | 64.8 ms | 147.1 ms | 100 MiB |
| java (hilos virtuales) | 13931 | 14734 | 0.4 ms | 19.8 ms | 61 MiB |
| java (hilos de plataforma) | 14046 | 14848 | 1.0 ms | 4.2 ms | 55 MiB |

## 6 · Latencia de una petición sola: /trabajo

Un solo cliente a 5 peticiones/s (`hey -c 1 -q 5`), 20 s, tras 10 s de calentamiento a tope. Cada petición llega sola: no hay cola, es lo que tarda el servidor en atender una.

| variante | peticiones/s logradas | p50 | p99 |
|---|---|---|---|
| python (1 proceso) | 5 | 10.70 ms | 22.10 ms |
| python (2 procesos) | 5 | 10.60 ms | 21.80 ms |
| java (hilos virtuales) | 5 | 2.40 ms | 4.20 ms |
| java (hilos de plataforma) | 5 | 2.40 ms | 4.20 ms |

## 7 · Latencia de una petición sola: /suma

Un solo cliente a 5 peticiones/s (`hey -c 1 -q 5`), 20 s, tras 10 s de calentamiento a tope. Cada petición llega sola: no hay cola, es lo que tarda el servidor en atender una.

| variante | peticiones/s logradas | p50 | p99 |
|---|---|---|---|
| python (1 proceso) | 5 | 9.30 ms | 10.40 ms |
| python (2 procesos) | 5 | 9.20 ms | 9.90 ms |
| java (hilos virtuales) | 5 | 0.80 ms | 1.70 ms |
| java (hilos de plataforma) | 5 | 0.80 ms | 1.90 ms |

