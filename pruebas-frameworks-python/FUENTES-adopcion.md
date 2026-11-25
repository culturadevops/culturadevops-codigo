# Adopción de los frameworks web de Python (leído 2026-11-04 16:53, `python adopcion.py`)

## Descargas de PyPI (pypistats.org, API pública)

«Último mes» = /recent (last_month, últimos 30 días). «Periodo» = /overall?mirrors=false (sin espejos), sumado sobre los días que devuelve la API (pypistats guarda unos 180).

| paquete | último mes | última semana | periodo (sin espejos) | días del periodo | última versión | publicada |
|---|---|---|---|---|---|---|
| starlette | 500.961.483 | 159.564.147 | 3.933.251.612 | 2026-04-08 → 2026-11-03 | 1.10.0 | 2026-10-24 |
| fastapi | 381.578.963 | 122.696.725 | 3.400.328.320 | 2026-04-08 → 2026-11-03 | 0.162.0 | 2026-10-23 |
| flask | 136.480.505 | 55.313.509 | 1.318.503.651 | 2026-04-08 → 2026-11-03 | 3.1.3 | 2026-02-19 |
| django | 41.143.691 | 11.850.997 | 339.270.666 | 2026-04-08 → 2026-11-03 | 6.1.3 | 2026-11-03 |
| litestar | 1.703.807 | 403.884 | 12.420.137 | 2026-04-08 → 2026-11-03 | 2.25.0 | 2026-10-18 |
| falcon | 1.355.130 | 370.323 | 9.442.818 | 2026-04-08 → 2026-11-03 | 4.4.0 | 2026-09-30 |
| sanic | 1.100.035 | 238.533 | 11.661.093 | 2026-04-08 → 2026-11-03 | 25.12.1 | 2026-05-31 |

⚠️ Starlette es dependencia de FastAPI: sus descargas incluyen todas las de FastAPI. Ninguna descarga es un usuario (CI, Docker, dependencias).

Fuentes: https://pypistats.org/api/packages/<paquete>/recent · https://pypistats.org/api/packages/<paquete>/overall?mirrors=false · https://pypi.org/pypi/<paquete>/json

BigQuery público (bigquery-public-data.pypi.file_downloads): NO usado, sin bq/gcloud ni credenciales en esta máquina.

## Stack Overflow Developer Survey 2026 · Web frameworks and technologies (n = 10.281)

Copiado de ../pruebas-lenguajes-vs/FUENTES-so2026.md; verificado contra la página el 2026-11-04.

| framework | uso | quieren usarlo | admirado |
|---|---|---|---|
| FastAPI | 18,5 % (1.903 de 10.281) | 13,5 % | 51,3 % |
| Flask | 12,5 % (1.284) | 7,1 % | 38,1 % |
| Django | 11,3 % (1.160) | 8,2 % | 43,8 % |

Starlette, Litestar, Sanic y Falcon NO aparecen en la lista de la encuesta.
Uso: https://survey.stackoverflow.co/2026/technology/data/web-framework · Querido/admirado: https://survey.stackoverflow.co/2026/technology/data/da-webframe
