# SALIDA — Tier list de frameworks web de Python 2026 (cultura-devops, vídeo 770)

> Corrida del 2026-11-04 17:45. Regenerable con `python correr.py`. ⛔ Ninguna cifra de blog: todo salió de aquí. La misma lógica (app/logica.py) en todos; cambia solo el framework y su servidor.

- `Python 3.13.17` (python:3.13.17-slim, la misma base que «¿Python o X?»). Docker `29.6.2`.
- Servidores con 2 CPU y 1g, 2 procesos cada uno (uno por CPU); `hey -c 16` con 4 CPU desde otro contenedor.
- /trabajo?n=20000: crea 20000 objetos, los mete en un dict, los ordena y arma un JSON a mano. /suma?n=200000: multiplicar y módulo en un bucle. /suma?n=1: el cálculo es casi cero, queda el coste del framework.
- Rutas: Django, Flask y Falcon síncronas (WSGI). FastAPI `def` y Starlette `def` → threadpool; Litestar `sync_to_thread=True` → threadpool; FastAPI `async def` y Sanic `async def` → en el bucle de eventos.

| framework | servidor | dependencias directas (versiones fijadas en req/<fw>.txt) |
|---|---|---|
| Django | gunicorn 26.2 (workers síncronos) | django==6.1.3, gunicorn==26.2.0 |
| Flask | gunicorn 26.2 (workers síncronos) | flask==3.1.3, gunicorn==26.2.0 |
| Falcon | gunicorn 26.2 (workers síncronos) | falcon==4.4.0, gunicorn==26.2.0 |
| FastAPI | uvicorn 0.54 + uvloop + httptools | fastapi==0.162.0, starlette==1.9.0, pydantic==2.14.1, uvicorn[standard]==0.54.0 |
| Starlette | uvicorn 0.54 + uvloop + httptools | starlette==1.10.0, uvicorn[standard]==0.54.0 |
| Litestar | uvicorn 0.54 + uvloop + httptools | litestar==2.25.0, uvicorn[standard]==0.54.0 |
| Sanic | su propio servidor (uvloop) | sanic==25.12.1 |

## 1 · Construir la imagen desde cero (`docker build --no-cache`: pip install incluido; la imagen base ya descargada no cuenta)

| framework | paquetes instalados | segundos |
|---|---|---|
| Django | 4 | 4.9 |
| Flask | 8 | 2.6 |
| Falcon | 2 | 2.3 |
| FastAPI | 20 | 5.3 |
| Starlette | 13 | 3.9 |
| Litestar | 28 | 7.7 |
| Sanic | 12 | 4.6 |

## 2 · Lo que despliegas

| framework | tamaño en disco (python:3.13.17-slim + dependencias + código) |
|---|---|
| Django | 53.1 MiB |
| Flask | 46.5 MiB |
| Falcon | 46.2 MiB |
| FastAPI | 56.3 MiB |
| Starlette | 52.5 MiB |
| Litestar | 62.6 MiB |
| Sanic | 53.1 MiB |

## 0 · ¿Hacen lo mismo? (antes de medir)

El cuerpo de /trabajo?n=20000, /suma?n=200000 y /suma?n=1, comparado byte a byte con fastapi (def) quitando solo el campo "ns" (el reloj del cálculo).

- django: total 9990000, primeros ids [0, 1000, 2000, 3000, 4000]…, suma 99863963591, 2236 + 47 + 32 bytes, application/json → idéntico
- flask: total 9990000, primeros ids [0, 1000, 2000, 3000, 4000]…, suma 99863963591, 2236 + 47 + 32 bytes, application/json → idéntico
- falcon: total 9990000, primeros ids [0, 1000, 2000, 3000, 4000]…, suma 99863963591, 2236 + 47 + 32 bytes, application/json → idéntico
- fastapi (def): total 9990000, primeros ids [0, 1000, 2000, 3000, 4000]…, suma 99863963591, 2236 + 47 + 32 bytes, application/json → idéntico
- fastapi (async def): total 9990000, primeros ids [0, 1000, 2000, 3000, 4000]…, suma 99863963591, 2236 + 47 + 32 bytes, application/json → idéntico
- starlette: total 9990000, primeros ids [0, 1000, 2000, 3000, 4000]…, suma 99863963591, 2236 + 47 + 32 bytes, application/json → idéntico
- litestar: total 9990000, primeros ids [0, 1000, 2000, 3000, 4000]…, suma 99863963591, 2236 + 47 + 32 bytes, application/json → idéntico
- sanic: total 9990000, primeros ids [0, 1000, 2000, 3000, 4000]…, suma 99863963591, 2236 + 47 + 32 bytes, application/json → idéntico

## 3 · Arranque: contenedor nuevo → primera respuesta 200 (mediana de 8) y memoria en reposo

| variante | 1ª respuesta (docker incluido) | «listo» (su propio reloj) | memoria en reposo |
|---|---|---|---|
| django | 392 ms | 156.6 ms | 79.7 MiB |
| flask | 289 ms | 59.0 ms | 56.4 MiB |
| falcon | 308 ms | 81.6 ms | 49.4 MiB |
| fastapi (def) | 489 ms | 110.1 ms | 95.6 MiB |
| fastapi (async def) | 495 ms | 109.6 ms | 94.5 MiB |
| starlette | 386 ms | 11.9 ms | 71.7 MiB |
| litestar | 476 ms | 101.7 ms | 87.9 MiB |
| sanic | 554 ms | 12.4 ms | 113.8 MiB |

## A · Cómputo de UNA petición (mediana del campo ns, 30 de calentamiento + 200 medidas, de una en una)

| variante | /trabajo (20.000 objetos) | /suma (200.000 vueltas) |
|---|---|---|
| django | 8.56 ms | 8.258 ms |
| flask | 8.59 ms | 8.354 ms |
| falcon | 8.45 ms | 8.303 ms |
| fastapi (def) | 8.79 ms | 8.194 ms |
| fastapi (async def) | 8.68 ms | 8.223 ms |
| starlette | 8.92 ms | 8.487 ms |
| litestar | 8.68 ms | 8.513 ms |
| sanic | 8.70 ms | 8.634 ms |

## 4 · Carga con memoria: /trabajo (objetos, dict, orden, JSON), a tope

`hey -c 16` desde otro contenedor; servidor con 2 CPU y 1g. «En frío»: los primeros 10 s tras arrancar. «Templado»: los 20 s siguientes.

| variante | peticiones/s en frío | peticiones/s templado | p50 | p99 | memoria máx. bajo carga |
|---|---|---|---|---|---|
| django | 171 | 172 | 91.3 ms | 108.9 ms | 96 MiB |
| flask | 184 | 184 | 86.2 ms | 96.2 ms | 72 MiB |
| falcon | 191 | 191 | 83.4 ms | 92.3 ms | 64 MiB |
| fastapi (def) | 146 | 142 | 106.1 ms | 236.2 ms | 164 MiB |
| fastapi (async def) | 180 | 179 | 78.3 ms | 163.1 ms | 107 MiB |
| starlette | 155 | 156 | 100.2 ms | 194.9 ms | 141 MiB |
| litestar | 149 | 146 | 103.0 ms | 240.8 ms | 157 MiB |
| sanic | 193 | 195 | 71.9 ms | 148.0 ms | 127 MiB |

## 5 · Carga de CPU pura: /suma, a tope

`hey -c 16` desde otro contenedor; servidor con 2 CPU y 1g. «En frío»: los primeros 10 s tras arrancar. «Templado»: los 20 s siguientes.

| variante | peticiones/s en frío | peticiones/s templado | p50 | p99 | memoria máx. bajo carga |
|---|---|---|---|---|---|
| django | 231 | 231 | 69.0 ms | 72.5 ms | 86 MiB |
| flask | 228 | 227 | 70.4 ms | 74.4 ms | 59 MiB |
| falcon | 231 | 231 | 69.2 ms | 72.2 ms | 51 MiB |
| fastapi (def) | 230 | 232 | 65.4 ms | 148.0 ms | 101 MiB |
| fastapi (async def) | 241 | 240 | 58.3 ms | 119.1 ms | 95 MiB |
| starlette | 225 | 224 | 68.3 ms | 143.3 ms | 78 MiB |
| litestar | 232 | 232 | 65.7 ms | 146.6 ms | 92 MiB |
| sanic | 237 | 237 | 58.9 ms | 121.6 ms | 114 MiB |

## 6 · El coste del framework: /suma?n=1 (casi sin cálculo), a tope

`hey -c 16` desde otro contenedor; servidor con 2 CPU y 1g. «En frío»: los primeros 10 s tras arrancar. «Templado»: los 20 s siguientes.

| variante | peticiones/s en frío | peticiones/s templado | p50 | p99 | memoria máx. bajo carga |
|---|---|---|---|---|---|
| django | 4940 | 3046 | 2.5 ms | 42.3 ms | 89 MiB |
| flask | 7750 | 5530 | 2.0 ms | 50.0 ms | 64 MiB |
| falcon | 11408 | 7294 | 1.4 ms | 61.7 ms | 58 MiB |
| fastapi (def) | 14194 | 15482 | 1.0 ms | 2.2 ms | 101 MiB |
| fastapi (async def) | 37465 | 37096 | 0.4 ms | 0.9 ms | 98 MiB |
| starlette | 18353 | 19794 | 0.8 ms | 1.8 ms | 77 MiB |
| litestar | 16767 | 16689 | 0.9 ms | 2.7 ms | 92 MiB |
| sanic | 83217 | 83538 | 0.2 ms | 0.5 ms | 115 MiB |

## 7 · Latencia de una petición sola: /trabajo

Un solo cliente a 5 peticiones/s (`hey -c 1 -q 5`), 20 s, tras 10 s de calentamiento a tope. Cada petición llega sola: no hay cola, es lo que tarda el servidor en atender una.

| variante | peticiones/s logradas | p50 | p99 |
|---|---|---|---|
| django | 5 | 11.50 ms | 23.10 ms |
| flask | 5 | 11.80 ms | 26.80 ms |
| falcon | 5 | 11.30 ms | 18.60 ms |
| fastapi (def) | 5 | 11.10 ms | 26.20 ms |
| fastapi (async def) | 5 | 10.40 ms | 21.90 ms |
| starlette | 5 | 11.20 ms | 18.80 ms |
| litestar | 5 | 11.00 ms | 25.70 ms |
| sanic | 5 | 10.70 ms | 18.00 ms |

## 8 · Latencia de una petición sola: /suma?n=1 (el framework solo)

Un solo cliente a 5 peticiones/s (`hey -c 1 -q 5`), 20 s, tras 10 s de calentamiento a tope. Cada petición llega sola: no hay cola, es lo que tarda el servidor en atender una.

| variante | peticiones/s logradas | p50 | p99 |
|---|---|---|---|
| django | 5 | 1.30 ms | 1.80 ms |
| flask | 5 | 1.30 ms | 1.90 ms |
| falcon | 5 | 1.00 ms | 1.40 ms |
| fastapi (def) | 5 | 0.80 ms | 1.60 ms |
| fastapi (async def) | 5 | 0.70 ms | 1.70 ms |
| starlette | 5 | 0.70 ms | 1.70 ms |
| litestar | 5 | 0.80 ms | 1.40 ms |
| sanic | 5 | 0.50 ms | 1.20 ms |

