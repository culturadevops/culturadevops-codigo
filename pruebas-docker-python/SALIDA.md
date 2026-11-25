# SALIDA — Los 4 Dockerfiles de Python, medidos en esta máquina

> Corrida del 2026-08-30 21:03. Regenerable con
> `python investigacion/pruebas_docker_python.py`. ⛔ Ninguna cifra de blog.
> App: Flask 3.1.0 + gunicorn 23.0.0 (dos rutas). Docker 29.6.2.

| variante | build frío | tras tocar SOLO el código | descarga | en disco | /salud |
|---|---|---|---|---|---|
| 1-ingenuo | 3.8 s | **3.0 s** | 400.0 MiB | 1.63GB | ✅ |
| 2-slim | 3.1 s | **0.6 s** | 46.3 MiB | 199MB | ✅ |
| 3-multistage | 4.1 s | **0.6 s** | 46.6 MiB | 202MB | ✅ |
| 4-uv | 7.1 s | **0.7 s** | 41.7 MiB | 180MB | ✅ |

## El contexto que viaja al demonio (con 80 MB de basura en la carpeta)

- SIN `.dockerignore`: `#3 transferring context: 2B done`
- CON `.dockerignore`: `#3 transferring context: 183B done`
