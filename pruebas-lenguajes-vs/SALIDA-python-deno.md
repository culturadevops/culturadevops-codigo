# SALIDA — ¿Python o Deno? (cultura-devops)

> Corrida del 2026-11-05 07:36. Regenerable con `python correr.py python deno`. ⛔ Ninguna cifra de blog: todo salió de aquí. Servidores de canales/golandia/recursos/pruebas-go-* (mismo contrato).

- python: `Python 3.13.17` — python:3.13.17-slim + FastAPI 0.162 + uvicorn 0.54
- deno: `deno 2.9.8 (stable, release, x86_64-unknown-linux-gnu)` — denoland/deno:2.9.8 (Deno.serve)
- Docker `29.6.2`. Servidores con 2 CPU y 1g; `hey -c 16` con 4 CPU desde otro contenedor.
- /trabajo?n=20000: crea 20000 objetos, los mete en un mapa, los ordena y arma un JSON a mano. /suma?n=200000: multiplicar y módulo en un bucle.

## 1 · Construir la imagen desde cero (`docker build --no-cache`, dependencias incluidas; la imagen base ya descargada no cuenta)

| lenguaje | qué se cronometra | segundos |
|---|---|---|
| python | pip install de FastAPI + uvicorn | 5.3 |
| deno | copiar + deno check (comprobar tipos) | 1.2 |

## 2 · Lo que despliegas

| imagen | base | tamaño en disco |
|---|---|---|
| python | python:3.13.17-slim + FastAPI 0.162 + uvicorn 0.54 | 56.3 MiB |
| deno | denoland/deno:2.9.8 (Deno.serve) | 70.5 MiB |

## 0 · ¿Hacen lo mismo? (antes de medir)

- python (1 proceso): total 9990000, primeros ids [0, 1000, 2000, 3000, 4000]…, suma 99863963591 → igual
- python (2 procesos): total 9990000, primeros ids [0, 1000, 2000, 3000, 4000]…, suma 99863963591 → igual
- deno (1 hilo): total 9990000, primeros ids [0, 1000, 2000, 3000, 4000]…, suma 99863963591 → igual
- deno serve --parallel: total 9990000, primeros ids [0, 1000, 2000, 3000, 4000]…, suma 99863963591 → igual

## 3 · Arranque: contenedor nuevo → primera respuesta 200 (mediana de 8) y memoria en reposo

| variante | 1ª respuesta (docker incluido) | «listo» (su propio reloj) | memoria en reposo |
|---|---|---|---|
| python (1 proceso) | 447 ms | 126.5 ms | 37.0 MiB |
| python (2 procesos) | 482 ms | 113.5 ms | 95.5 MiB |
| deno (1 hilo) | 254 ms | 5.2 ms | 20.0 MiB |
| deno serve --parallel | 232 ms | — | 30.6 MiB |

## A · Cómputo de UNA petición (mediana del reloj del propio servidor, 30 de calentamiento + 200 medidas, de una en una)

| variante | /trabajo (20.000 objetos) | /suma (200.000 vueltas) |
|---|---|---|
| python (1 proceso) | 8.28 ms | 8.292 ms |
| python (2 procesos) | 8.64 ms | 8.207 ms |
| deno (1 hilo) | 3.05 ms | 1.166 ms |
| deno serve --parallel | 3.21 ms | 1.170 ms |

## 4 · Carga con memoria: /trabajo (objetos, mapa, orden, JSON), a tope

`hey -c 16` desde otro contenedor; servidor con 2 CPU y 1g. «En frío»: los primeros 10 s tras arrancar. «Templado»: los 20 s siguientes.

| variante | peticiones/s en frío | peticiones/s templado | p50 | p99 | memoria máx. bajo carga |
|---|---|---|---|---|---|
| python (1 proceso) | 75 | 75 | 203.5 ms | 465.4 ms | 101 MiB |
| python (2 procesos) | 143 | 147 | 103.6 ms | 233.5 ms | 168 MiB |
| deno (1 hilo) | 268 | 256 | 58.3 ms | 88.8 ms | 121 MiB |
| deno serve --parallel | 480 | 470 | 34.7 ms | 63.1 ms | 152 MiB |

## 5 · Carga de CPU pura: /suma, a tope

`hey -c 16` desde otro contenedor; servidor con 2 CPU y 1g. «En frío»: los primeros 10 s tras arrancar. «Templado»: los 20 s siguientes.

| variante | peticiones/s en frío | peticiones/s templado | p50 | p99 | memoria máx. bajo carga |
|---|---|---|---|---|---|
| python (1 proceso) | 117 | 117 | 131.7 ms | 309.7 ms | 42 MiB |
| python (2 procesos) | 233 | 232 | 64.7 ms | 151.9 ms | 100 MiB |
| deno (1 hilo) | 842 | 843 | 18.9 ms | 19.8 ms | 26 MiB |
| deno serve --parallel | 1665 | 1675 | 10.4 ms | 13.0 ms | 39 MiB |

## 6 · Latencia de una petición sola: /trabajo

Un solo cliente a 5 peticiones/s (`hey -c 1 -q 5`), 20 s, tras 10 s de calentamiento a tope. Cada petición llega sola: no hay cola, es lo que tarda el servidor en atender una.

| variante | peticiones/s logradas | p50 | p99 |
|---|---|---|---|
| python (1 proceso) | 5 | 13.60 ms | 25.40 ms |
| python (2 procesos) | 5 | 14.70 ms | 27.50 ms |
| deno (1 hilo) | 5 | 6.90 ms | 11.50 ms |
| deno serve --parallel | 5 | 5.70 ms | 10.10 ms |

## 7 · Latencia de una petición sola: /suma

Un solo cliente a 5 peticiones/s (`hey -c 1 -q 5`), 20 s, tras 10 s de calentamiento a tope. Cada petición llega sola: no hay cola, es lo que tarda el servidor en atender una.

| variante | peticiones/s logradas | p50 | p99 |
|---|---|---|---|
| python (1 proceso) | 5 | 11.00 ms | 16.80 ms |
| python (2 procesos) | 5 | 10.40 ms | 15.50 ms |
| deno (1 hilo) | 5 | 2.90 ms | 7.20 ms |
| deno serve --parallel | 5 | 2.50 ms | 9.30 ms |

