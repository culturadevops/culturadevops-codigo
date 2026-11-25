# SALIDA — ¿Node o Java? (cultura-devops)

> Corrida del 2026-11-04 17:24. Regenerable con `python correr.py node java`. ⛔ Ninguna cifra de blog: todo salió de aquí. Servidores de canales/golandia/recursos/pruebas-go-* (mismo contrato).

- node: `v24.22.2` — node:24-slim (node:http, sin dependencias)
- java: `openjdk version "25.0.5" 2026-10-20 LTS` — eclipse-temurin:25-jre + jar (com.sun.net.httpserver)
- Docker `29.6.2`. Servidores con 2 CPU y 1g; `hey -c 16` con 4 CPU desde otro contenedor.
- /trabajo?n=20000: crea 20000 objetos, los mete en un mapa, los ordena y arma un JSON a mano. /suma?n=200000: multiplicar y módulo en un bucle.

## 1 · Construir la imagen desde cero (`docker build --no-cache`, dependencias incluidas; la imagen base ya descargada no cuenta)

| lenguaje | qué se cronometra | segundos |
|---|---|---|
| node | copiar servidor.js (no instala nada) | 1.4 |
| java | javac + jar | 1.5 |

## 2 · Lo que despliegas

| imagen | base | tamaño en disco |
|---|---|---|
| node | node:24-slim (node:http, sin dependencias) | 77.3 MiB |
| java | eclipse-temurin:25-jre + jar (com.sun.net.httpserver) | 112.0 MiB |

## 0 · ¿Hacen lo mismo? (antes de medir)

- node (1 proceso): total 9990000, primeros ids [0, 1000, 2000, 3000, 4000]…, suma 99863963591 → igual
- node (2 procesos): total 9990000, primeros ids [0, 1000, 2000, 3000, 4000]…, suma 99863963591 → igual
- java (hilos virtuales): total 9990000, primeros ids [0, 1000, 2000, 3000, 4000]…, suma 99863963591 → igual
- java (hilos de plataforma): total 9990000, primeros ids [0, 1000, 2000, 3000, 4000]…, suma 99863963591 → igual

## 3 · Arranque: contenedor nuevo → primera respuesta 200 (mediana de 8) y memoria en reposo

| variante | 1ª respuesta (docker incluido) | «listo» (su propio reloj) | memoria en reposo |
|---|---|---|---|
| node (1 proceso) | 504 ms | 3.3 ms | 12.6 MiB |
| node (2 procesos) | 227 ms | 4.4 ms | 34.2 MiB |
| java (hilos virtuales) | 253 ms | 17.7 ms | 34.7 MiB |
| java (hilos de plataforma) | 267 ms | 17.5 ms | 34.2 MiB |

## A · Cómputo de UNA petición (mediana del reloj del propio servidor, 30 de calentamiento + 200 medidas, de una en una)

| variante | /trabajo (20.000 objetos) | /suma (200.000 vueltas) |
|---|---|---|
| node (1 proceso) | 3.35 ms | 1.176 ms |
| node (2 procesos) | 3.47 ms | 1.176 ms |
| java (hilos virtuales) | 2.03 ms | 0.098 ms |
| java (hilos de plataforma) | 2.01 ms | 0.098 ms |

## 4 · Carga con memoria: /trabajo (objetos, mapa, orden, JSON), a tope

`hey -c 16` desde otro contenedor; servidor con 2 CPU y 1g. «En frío»: los primeros 10 s tras arrancar. «Templado»: los 20 s siguientes.

| variante | peticiones/s en frío | peticiones/s templado | p50 | p99 | memoria máx. bajo carga |
|---|---|---|---|---|---|
| node (1 proceso) | 240 | 209 | 63.6 ms | 189.6 ms | 115 MiB |
| node (2 procesos) | 381 | 339 | 39.2 ms | 137.4 ms | 257 MiB |
| java (hilos virtuales) | 492 | 981 | 15.8 ms | 27.3 ms | 296 MiB |
| java (hilos de plataforma) | 739 | 1058 | 15.0 ms | 19.8 ms | 297 MiB |

## 5 · Carga de CPU pura: /suma, a tope

`hey -c 16` desde otro contenedor; servidor con 2 CPU y 1g. «En frío»: los primeros 10 s tras arrancar. «Templado»: los 20 s siguientes.

| variante | peticiones/s en frío | peticiones/s templado | p50 | p99 | memoria máx. bajo carga |
|---|---|---|---|---|---|
| node (1 proceso) | 809 | 820 | 18.3 ms | 37.2 ms | 23 MiB |
| node (2 procesos) | 1621 | 1638 | 9.5 ms | 19.9 ms | 56 MiB |
| java (hilos virtuales) | 15226 | 16262 | 0.4 ms | 18.6 ms | 57 MiB |
| java (hilos de plataforma) | 13805 | 14689 | 1.0 ms | 3.8 ms | 54 MiB |

## 6 · Latencia de una petición sola: /trabajo

Un solo cliente a 5 peticiones/s (`hey -c 1 -q 5`), 20 s, tras 10 s de calentamiento a tope. Cada petición llega sola: no hay cola, es lo que tarda el servidor en atender una.

| variante | peticiones/s logradas | p50 | p99 |
|---|---|---|---|
| node (1 proceso) | 5 | 5.20 ms | 7.70 ms |
| node (2 procesos) | 5 | 4.30 ms | 6.40 ms |
| java (hilos virtuales) | 5 | 2.30 ms | 3.80 ms |
| java (hilos de plataforma) | 5 | 2.40 ms | 3.80 ms |

## 7 · Latencia de una petición sola: /suma

Un solo cliente a 5 peticiones/s (`hey -c 1 -q 5`), 20 s, tras 10 s de calentamiento a tope. Cada petición llega sola: no hay cola, es lo que tarda el servidor en atender una.

| variante | peticiones/s logradas | p50 | p99 |
|---|---|---|---|
| node (1 proceso) | 5 | 1.70 ms | 2.80 ms |
| node (2 procesos) | 5 | 1.80 ms | 2.80 ms |
| java (hilos virtuales) | 5 | 0.70 ms | 1.80 ms |
| java (hilos de plataforma) | 5 | 0.70 ms | 1.60 ms |

