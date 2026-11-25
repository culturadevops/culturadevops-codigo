# SALIDA — ¿Deno o Java? (cultura-devops)

> Corrida del 2026-11-05 08:41. Regenerable con `python correr.py deno java`. ⛔ Ninguna cifra de blog: todo salió de aquí. Servidores de canales/golandia/recursos/pruebas-go-* (mismo contrato).

- deno: `deno 2.9.8 (stable, release, x86_64-unknown-linux-gnu)` — denoland/deno:2.9.8 (Deno.serve)
- java: `openjdk version "25.0.5" 2026-10-20 LTS` — eclipse-temurin:25-jre + jar (com.sun.net.httpserver)
- Docker `29.6.2`. Servidores con 2 CPU y 1g; `hey -c 16` con 4 CPU desde otro contenedor.
- /trabajo?n=20000: crea 20000 objetos, los mete en un mapa, los ordena y arma un JSON a mano. /suma?n=200000: multiplicar y módulo en un bucle.

## 1 · Construir la imagen desde cero (`docker build --no-cache`, dependencias incluidas; la imagen base ya descargada no cuenta)

| lenguaje | qué se cronometra | segundos |
|---|---|---|
| deno | copiar + deno check (comprobar tipos) | 1.3 |
| java | javac + jar | 1.1 |

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
| deno (1 hilo) | 268 ms | 5.8 ms | 20.2 MiB |
| deno serve --parallel | 247 ms | — | 30.2 MiB |
| java (hilos virtuales) | 266 ms | 18.8 ms | 34.6 MiB |
| java (hilos de plataforma) | 259 ms | 17.8 ms | 33.8 MiB |

## A · Cómputo de UNA petición (mediana del reloj del propio servidor, 30 de calentamiento + 200 medidas, de una en una)

| variante | /trabajo (20.000 objetos) | /suma (200.000 vueltas) |
|---|---|---|
| deno (1 hilo) | 2.99 ms | 1.178 ms |
| deno serve --parallel | 3.17 ms | 1.180 ms |
| java (hilos virtuales) | 2.00 ms | 0.098 ms |
| java (hilos de plataforma) | 1.96 ms | 0.098 ms |

## 4 · Carga con memoria: /trabajo (objetos, mapa, orden, JSON), a tope

`hey -c 16` desde otro contenedor; servidor con 2 CPU y 1g. «En frío»: los primeros 10 s tras arrancar. «Templado»: los 20 s siguientes.

| variante | peticiones/s en frío | peticiones/s templado | p50 | p99 | memoria máx. bajo carga |
|---|---|---|---|---|---|
| deno (1 hilo) | 249 | 250 | 63.7 ms | 70.0 ms | 77 MiB |
| deno serve --parallel | 478 | 492 | 52.3 ms | 70.0 ms | 137 MiB |
| java (hilos virtuales) | 1012 | 1107 | 13.7 ms | 16.7 ms | 303 MiB |
| java (hilos de plataforma) | 1008 | 1098 | 14.6 ms | 17.3 ms | 294 MiB |

## 5 · Carga de CPU pura: /suma, a tope

`hey -c 16` desde otro contenedor; servidor con 2 CPU y 1g. «En frío»: los primeros 10 s tras arrancar. «Templado»: los 20 s siguientes.

| variante | peticiones/s en frío | peticiones/s templado | p50 | p99 | memoria máx. bajo carga |
|---|---|---|---|---|---|
| deno (1 hilo) | 832 | 840 | 19.0 ms | 20.1 ms | 26 MiB |
| deno serve --parallel | 1667 | 1665 | 10.4 ms | 11.6 ms | 40 MiB |
| java (hilos virtuales) | 13869 | 14686 | 0.4 ms | 22.7 ms | 56 MiB |
| java (hilos de plataforma) | 14022 | 14804 | 1.0 ms | 3.2 ms | 56 MiB |

## 6 · Latencia de una petición sola: /trabajo

Un solo cliente a 5 peticiones/s (`hey -c 1 -q 5`), 20 s, tras 10 s de calentamiento a tope. Cada petición llega sola: no hay cola, es lo que tarda el servidor en atender una.

| variante | peticiones/s logradas | p50 | p99 |
|---|---|---|---|
| deno (1 hilo) | 5 | 4.80 ms | 9.40 ms |
| deno serve --parallel | 5 | 4.50 ms | 6.40 ms |
| java (hilos virtuales) | 5 | 2.20 ms | 3.80 ms |
| java (hilos de plataforma) | 5 | 2.30 ms | 3.60 ms |

## 7 · Latencia de una petición sola: /suma

Un solo cliente a 5 peticiones/s (`hey -c 1 -q 5`), 20 s, tras 10 s de calentamiento a tope. Cada petición llega sola: no hay cola, es lo que tarda el servidor en atender una.

| variante | peticiones/s logradas | p50 | p99 |
|---|---|---|---|
| deno (1 hilo) | 5 | 1.60 ms | 2.50 ms |
| deno serve --parallel | 5 | 1.60 ms | 2.40 ms |
| java (hilos virtuales) | 5 | 0.60 ms | 1.80 ms |
| java (hilos de plataforma) | 5 | 0.70 ms | 1.50 ms |

