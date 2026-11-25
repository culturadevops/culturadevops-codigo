# SALIDA — ¿Deno o Java? (cultura-devops)

> Corrida del 2026-11-05 08:00. Regenerable con `python correr.py deno java`. ⛔ Ninguna cifra de blog: todo salió de aquí. Servidores de canales/golandia/recursos/pruebas-go-* (mismo contrato).

- deno: `deno 2.9.8 (stable, release, x86_64-unknown-linux-gnu)` — denoland/deno:2.9.8 (Deno.serve)
- java: `openjdk version "25.0.5" 2026-10-20 LTS` — eclipse-temurin:25-jre + jar (com.sun.net.httpserver)
- Docker `29.6.2`. Servidores con 2 CPU y 1g; `hey -c 16` con 4 CPU desde otro contenedor.
- /trabajo?n=20000: crea 20000 objetos, los mete en un mapa, los ordena y arma un JSON a mano. /suma?n=200000: multiplicar y módulo en un bucle.

## 1 · Construir la imagen desde cero (`docker build --no-cache`, dependencias incluidas; la imagen base ya descargada no cuenta)

| lenguaje | qué se cronometra | segundos |
|---|---|---|
| deno | copiar + deno check (comprobar tipos) | 1.3 |
| java | javac + jar | 1.6 |

## 2 · Lo que despliegas

| imagen | base | tamaño en disco |
|---|---|---|
| deno | denoland/deno:2.9.8 (Deno.serve) | 70.5 MiB |
| java | eclipse-temurin:25-jre + jar (com.sun.net.httpserver) | 112.0 MiB |

## 0 · ¿Hacen lo mismo? (antes de medir)

- deno (1 hilo): total 9990000, primeros ids [0, 1000, 2000, 3000, 4000]…, suma 99863963591 → igual
- deno serve --parallel: total 9990000, primeros ids [0, 1000, 2000, 3000, 4000]…, suma 99863963591 → igual
- java (hilos virtuales): total 9990000, primeros ids [0, 1000, 2000, 3000, 4000]…, suma 99863963591 → igual
- java (hilos de plataforma): total 9990000, primeros ids [0, 1000, 2000, 3000, 4000]…, suma 99863963591 → igual

## 3 · Arranque: contenedor nuevo → primera respuesta 200 (mediana de 8) y memoria en reposo

| variante | 1ª respuesta (docker incluido) | «listo» (su propio reloj) | memoria en reposo |
|---|---|---|---|
| deno (1 hilo) | 290 ms | 6.1 ms | 20.1 MiB |
| deno serve --parallel | 267 ms | — | 29.4 MiB |
| java (hilos virtuales) | 266 ms | 19.8 ms | 32.7 MiB |
| java (hilos de plataforma) | 575 ms | 41.2 ms | 31.7 MiB |

## A · Cómputo de UNA petición (mediana del reloj del propio servidor, 30 de calentamiento + 200 medidas, de una en una)

| variante | /trabajo (20.000 objetos) | /suma (200.000 vueltas) |
|---|---|---|
| deno (1 hilo) | 9.81 ms | 3.440 ms |
| deno serve --parallel | 6.49 ms | 1.244 ms |
| java (hilos virtuales) | 3.27 ms | 0.098 ms |
| java (hilos de plataforma) | 2.61 ms | 0.109 ms |

## 4 · Carga con memoria: /trabajo (objetos, mapa, orden, JSON), a tope

`hey -c 16` desde otro contenedor; servidor con 2 CPU y 1g. «En frío»: los primeros 10 s tras arrancar. «Templado»: los 20 s siguientes.

| variante | peticiones/s en frío | peticiones/s templado | p50 | p99 | memoria máx. bajo carga |
|---|---|---|---|---|---|
| deno (1 hilo) | 212 | 211 | 74.3 ms | 99.9 ms | 99 MiB |
| deno serve --parallel | 400 | 420 | 37.1 ms | 66.6 ms | 144 MiB |
| java (hilos virtuales) | 769 | 916 | 16.6 ms | 25.1 ms | 301 MiB |
| java (hilos de plataforma) | 828 | 902 | 17.0 ms | 24.7 ms | 300 MiB |

## 5 · Carga de CPU pura: /suma, a tope

`hey -c 16` desde otro contenedor; servidor con 2 CPU y 1g. «En frío»: los primeros 10 s tras arrancar. «Templado»: los 20 s siguientes.

| variante | peticiones/s en frío | peticiones/s templado | p50 | p99 | memoria máx. bajo carga |
|---|---|---|---|---|---|
| deno (1 hilo) | 800 | 819 | 19.2 ms | 24.2 ms | 24 MiB |
| deno serve --parallel | 1624 | 1541 | 10.0 ms | 14.7 ms | 38 MiB |
| java (hilos virtuales) | 12684 | 13573 | 0.5 ms | 20.6 ms | 58 MiB |
| java (hilos de plataforma) | 12453 | 12014 | 1.1 ms | 8.7 ms | 56 MiB |

## 6 · Latencia de una petición sola: /trabajo

Un solo cliente a 5 peticiones/s (`hey -c 1 -q 5`), 20 s, tras 10 s de calentamiento a tope. Cada petición llega sola: no hay cola, es lo que tarda el servidor en atender una.

| variante | peticiones/s logradas | p50 | p99 |
|---|---|---|---|
| deno (1 hilo) | 5 | 4.70 ms | 86.30 ms |
| deno serve --parallel | 5 | 4.60 ms | 6.50 ms |
| java (hilos virtuales) | 5 | 2.50 ms | 4.70 ms |
| java (hilos de plataforma) | 5 | 2.60 ms | 3.80 ms |

## 7 · Latencia de una petición sola: /suma

Un solo cliente a 5 peticiones/s (`hey -c 1 -q 5`), 20 s, tras 10 s de calentamiento a tope. Cada petición llega sola: no hay cola, es lo que tarda el servidor en atender una.

| variante | peticiones/s logradas | p50 | p99 |
|---|---|---|---|
| deno (1 hilo) | 5 | 1.60 ms | 4.30 ms |
| deno serve --parallel | 5 | 1.70 ms | 3.60 ms |
| java (hilos virtuales) | 5 | 0.60 ms | 1.90 ms |
| java (hilos de plataforma) | 5 | 0.60 ms | 7.40 ms |

