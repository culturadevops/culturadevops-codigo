# SALIDA — FastAPI contra Express, medidos en esta máquina (la revancha del 152)

> Corrida del 2026-08-31 06:54. Regenerable con
> `python investigacion/pruebas_fastapi_express.py`. ⛔ Ninguna cifra de blog.
> FastAPI 0.116.1 + uvicorn 0.35.0 sobre python:3.13-slim · Express 5.1.0 sobre
> node:22-slim. Referencias del 152 (stdlib): python p50 21,07 · node p50 2,12 ·
> bucle 8,40 / 1,18 ms · reposo 14,7 / 9,8 MiB.

## 1 · Imágenes (con las dependencias del framework)

| imagen | descarga | en disco |
|---|---|---|
| `cdo-revancha-fastapi:1` | 49.01 MiB | 211MB |
| `cdo-revancha-express:1` | 78.96 MiB | 345MB |

## 2 · Arranque (mediana de 8)

| framework | 1ª respuesta (docker incluido) | proceso «listo» |
|---|---|---|
| fastapi | 409 ms | 0.9 ms |
| express | 229 ms | 2.0 ms |

## 3 · Memoria (MiB)

| framework | reposo | tras 2.000 de CPU | bajo 300 concurrentes |
|---|---|---|---|
| fastapi | 31.7 | 33.9 | 39.0 |
| express | 17.5 | 52.2 | 54.2 |

## 4 · Templado (2.000 peticiones. n=200.000)

| framework | ext p50 | ext p99 | cómputo primeras 20 | cómputo últimas 500 |
|---|---|---|---|---|
| fastapi | 21.76 ms | 37.16 ms | 8.657 ms | 8.412 ms |
| express | 2.29 ms | 27.90 ms | 1.218 ms | 1.190 ms |

## 5 · Concurrencia: 300 × 100 ms de espera

| framework | total |
|---|---|
| fastapi | 2011 ms |
| express | 2006 ms |
