# SALIDA — ¿Python o PHP? (cultura-devops)

> Corrida del 2026-11-04 13:28. Regenerable con `python correr.py python php`. ⛔ Ninguna cifra de blog: todo salió de aquí. Servidores de canales/golandia/recursos/pruebas-go-* (mismo contrato).

- python: `Python 3.13.17` — python:3.13.17-slim + FastAPI 0.162 + uvicorn 0.54
- php: `FrankenPHP v1.13.3 PHP 8.5.12 Caddy v2.11.7 h1:yj0Y4fYZGPkSvibBJ1sTWE33xC0fxztVyXEW5iIdUT4=` — dunglas/frankenphp:1.13.3-php8.5
- Docker `29.6.2`. Servidores con 2 CPU y 1g; `hey -c 16` con 4 CPU desde otro contenedor.
- /trabajo?n=20000: crea 20000 objetos, los mete en un mapa, los ordena y arma un JSON a mano. /suma?n=200000: multiplicar y módulo en un bucle.

## 1 · Construir la imagen desde cero (`docker build --no-cache`, dependencias incluidas; la imagen base ya descargada no cuenta)

| lenguaje | qué se cronometra | segundos |
|---|---|---|
| python | pip install de FastAPI + uvicorn | 5.4 |
| php | copiar el código (PHP no compila) | 0.7 |

## 2 · Lo que despliegas

| imagen | base | tamaño en disco |
|---|---|---|
| python | python:3.13.17-slim + FastAPI 0.162 + uvicorn 0.54 | 56.3 MiB |
| php | dunglas/frankenphp:1.13.3-php8.5 | 201.2 MiB |

## 0 · ¿Hacen lo mismo? (antes de medir)

- python (1 proceso): total 9990000, primeros ids [0, 1000, 2000, 3000, 4000]…, suma 99863963591 → igual
- python (2 procesos): total 9990000, primeros ids [0, 1000, 2000, 3000, 4000]…, suma 99863963591 → igual
- php clásico (FrankenPHP): total 9990000, primeros ids [0, 1000, 2000, 3000, 4000]…, suma 99863963591 → igual
- php worker (FrankenPHP): total 9990000, primeros ids [0, 1000, 2000, 3000, 4000]…, suma 99863963591 → igual
- php worker + JIT: total 9990000, primeros ids [0, 1000, 2000, 3000, 4000]…, suma 99863963591 → igual

## 3 · Arranque: contenedor nuevo → primera respuesta 200 (mediana de 8) y memoria en reposo

| variante | 1ª respuesta (docker incluido) | «listo» (su propio reloj) | memoria en reposo |
|---|---|---|---|
| python (1 proceso) | 443 ms | 121.6 ms | 37.3 MiB |
| python (2 procesos) | 483 ms | 110.7 ms | 95.3 MiB |
| php clásico (FrankenPHP) | 232 ms | — | 24.3 MiB |
| php worker (FrankenPHP) | 234 ms | 0.0 ms | 25.6 MiB |
| php worker + JIT | 239 ms | 0.0 ms | 26.2 MiB |

## A · Cómputo de UNA petición (mediana del reloj del propio servidor, 30 de calentamiento + 200 medidas, de una en una)

| variante | /trabajo (20.000 objetos) | /suma (200.000 vueltas) |
|---|---|---|
| python (1 proceso) | 8.25 ms | 8.121 ms |
| python (2 procesos) | 8.79 ms | 8.349 ms |
| php clásico (FrankenPHP) | 11.86 ms | 0.684 ms |
| php worker (FrankenPHP) | 13.04 ms | 0.669 ms |
| php worker + JIT | 11.43 ms | 0.401 ms |

## 4 · Carga con memoria: /trabajo (objetos, mapa, orden, JSON), a tope

`hey -c 16` desde otro contenedor; servidor con 2 CPU y 1g. «En frío»: los primeros 10 s tras arrancar. «Templado»: los 20 s siguientes.

| variante | peticiones/s en frío | peticiones/s templado | p50 | p99 | memoria máx. bajo carga |
|---|---|---|---|---|---|
| python (1 proceso) | 78 | 77 | 192.5 ms | 462.2 ms | 97 MiB |
| python (2 procesos) | 155 | 152 | 37.3 ms | 398.3 ms | 178 MiB |
| php clásico (FrankenPHP) | 161 | 162 | 99.1 ms | 113.2 ms | 61 MiB |
| php worker (FrankenPHP) | 142 | 142 | 106.4 ms | 163.3 ms | 62 MiB |
| php worker + JIT | 159 | 158 | 100.8 ms | 156.6 ms | 63 MiB |

## 5 · Carga de CPU pura: /suma, a tope

`hey -c 16` desde otro contenedor; servidor con 2 CPU y 1g. «En frío»: los primeros 10 s tras arrancar. «Templado»: los 20 s siguientes.

| variante | peticiones/s en frío | peticiones/s templado | p50 | p99 | memoria máx. bajo carga |
|---|---|---|---|---|---|
| python (1 proceso) | 117 | 117 | 130.6 ms | 292.8 ms | 41 MiB |
| python (2 procesos) | 234 | 236 | 63.4 ms | 146.9 ms | 100 MiB |
| php clásico (FrankenPHP) | 2588 | 2556 | 6.4 ms | 11.2 ms | 33 MiB |
| php worker (FrankenPHP) | 2627 | 2630 | 6.0 ms | 11.3 ms | 33 MiB |
| php worker + JIT | 4065 | 4064 | 4.0 ms | 7.2 ms | 35 MiB |

## 6 · Latencia de una petición sola: /trabajo

Un solo cliente a 5 peticiones/s (`hey -c 1 -q 5`), 20 s, tras 10 s de calentamiento a tope. Cada petición llega sola: no hay cola, es lo que tarda el servidor en atender una.

| variante | peticiones/s logradas | p50 | p99 |
|---|---|---|---|
| python (1 proceso) | 5 | 11.20 ms | 22.20 ms |
| python (2 procesos) | 5 | 11.00 ms | 21.30 ms |
| php clásico (FrankenPHP) | 5 | 13.40 ms | 14.50 ms |
| php worker (FrankenPHP) | 5 | 15.40 ms | 16.30 ms |
| php worker + JIT | 5 | 13.80 ms | 14.80 ms |

## 7 · Latencia de una petición sola: /suma

Un solo cliente a 5 peticiones/s (`hey -c 1 -q 5`), 20 s, tras 10 s de calentamiento a tope. Cada petición llega sola: no hay cola, es lo que tarda el servidor en atender una.

| variante | peticiones/s logradas | p50 | p99 |
|---|---|---|---|
| python (1 proceso) | 5 | 9.30 ms | 11.20 ms |
| python (2 procesos) | 5 | 9.30 ms | 11.10 ms |
| php clásico (FrankenPHP) | 5 | 1.60 ms | 2.20 ms |
| php worker (FrankenPHP) | 5 | 1.40 ms | 2.10 ms |
| php worker + JIT | 5 | 1.30 ms | 2.10 ms |

