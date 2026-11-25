# SALIDA — Python contra Node, medidos en esta máquina

> Corrida del 2026-08-30 21:11. Regenerable con
> `python investigacion/pruebas_python_node.py`. ⛔ Ninguna cifra de blog.

- `Docker version 29.6.2, build dfc4efb` · `Python 3.13.14` (python:3.13-slim) · `v22.23.2` (node:22-slim)
- Mismo servidor HTTP, librería estándar en ambos (http.server con hilos / node:http).
- Trabajo de CPU por petición: 200.000 vueltas de multiplicar y módulo.

## 1 · Imágenes

| imagen | descarga | en disco |
|---|---|---|
| `cdo-pyvsnode-python:1` | 40.98 MiB | 176MB |
| `cdo-pyvsnode-node:1` | 76.20 MiB | 327MB |
| `python:3.13-slim` | 40.99 MiB | 178MB |

## 2 · Arranque (mediana de 8)

| lenguaje | 1ª respuesta (docker incluido) | proceso «listo» (su reloj) |
|---|---|---|
| python | 297 ms | 3.0 ms |
| node | 190 ms | 1.0 ms |

## 3 · Memoria (docker stats, MiB)

| lenguaje | reposo | tras 2.000 de CPU | bajo 300 concurrentes | tras la carga |
|---|---|---|---|---|
| python | 14.7 | 16.8 | 20.2 | 20.0 |
| node | 9.8 | 15.5 | 18.4 | 18.4 |

## 4 · Templado y el JIT (2.000 peticiones. n=200.000)

| lenguaje | ext p50 | ext p99 | cómputo primeras 20 | cómputo últimas 500 |
|---|---|---|---|---|
| python | 21.07 ms | 34.31 ms | 8.417 ms | 8.404 ms |
| node | 2.12 ms | 27.72 ms | 1.208 ms | 1.176 ms |

## 5 · Concurrencia: 300 × 100 ms de espera

| lenguaje | total | secuencial teórico |
|---|---|---|
| python | 2014 ms | 30.000 ms |
| node | 2013 ms | 30.000 ms |
