# -*- coding: utf-8 -*-
"""adopcion.py — adopción de los frameworks del banco, con fuente, para el vídeo 770 → FUENTES-adopcion.md

  · Descargas de PyPI: API pública de pypistats.org (/api/packages/<p>/recent y /overall?mirrors=false, sin espejos).
    BigQuery (bigquery-public-data.pypi) NO se usó: en esta máquina no hay bq ni gcloud ni credenciales de Google Cloud.
  · Última versión y su fecha: API JSON de pypi.org.
  · Stack Overflow 2026: ya leído en ../pruebas-lenguajes-vs/FUENTES-so2026.md (verificado de nuevo 2026-11-04 contra
    survey.stackoverflow.co/2026/technology/data/web-framework y /da-webframe: solo FastAPI, Flask y Django están en la lista).
⚠️ Una descarga no es un usuario: cuenta CI, imágenes Docker y dependencias. Starlette la instala cada FastAPI (y anyio, etc.),
   así que sus descargas incluyen las de FastAPI. Se dice así en el vídeo.

    python adopcion.py
"""
import json
import time
import urllib.request
from datetime import date, datetime
from pathlib import Path

AQUI = Path(__file__).resolve().parent
PAQ = ["django", "flask", "fastapi", "starlette", "litestar", "sanic", "falcon"]
UA = {"User-Agent": "cultura-devops-banco/1.0 (vídeo 770)"}


def get(url):
    for intento in range(4):
        try:
            with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=30) as r:
                return json.loads(r.read())
        except Exception:
            if intento == 3:
                raise
            time.sleep(3 * (intento + 1))


def main():
    filas = []
    for p in PAQ:
        rec = get(f"https://pypistats.org/api/packages/{p}/recent")["data"]
        time.sleep(1)
        ov = get(f"https://pypistats.org/api/packages/{p}/overall?mirrors=false")["data"]
        dias = sorted(d["date"] for d in ov if d["category"] == "without_mirrors")
        total = sum(d["downloads"] for d in ov if d["category"] == "without_mirrors")
        time.sleep(1)
        info = get(f"https://pypi.org/pypi/{p}/json")
        ver = info["info"]["version"]
        subida = min(f["upload_time_iso_8601"] for f in info["urls"])[:10] if info["urls"] else "?"
        filas.append((p, rec["last_month"], rec["last_week"], total, dias[0], dias[-1], ver, subida))
    out = [f"# Adopción de los frameworks web de Python (leído {datetime.now():%Y-%m-%d %H:%M}, `python adopcion.py`)\n",
           "## Descargas de PyPI (pypistats.org, API pública)\n",
           "«Último mes» = /recent (last_month, últimos 30 días). «Periodo» = /overall?mirrors=false (sin espejos), sumado sobre los días "
           "que devuelve la API (pypistats guarda unos 180).\n",
           "| paquete | último mes | última semana | periodo (sin espejos) | días del periodo | última versión | publicada |",
           "|---|---|---|---|---|---|---|"]
    for p, mes, sem, tot, d0, d1, ver, sub in sorted(filas, key=lambda f: -f[1]):
        out.append(f"| {p} | {mes:,} | {sem:,} | {tot:,} | {d0} → {d1} | {ver} | {sub} |".replace(",", "."))
    out += ["", "⚠️ Starlette es dependencia de FastAPI: sus descargas incluyen todas las de FastAPI. Ninguna descarga es un usuario "
                "(CI, Docker, dependencias).", "",
            "Fuentes: https://pypistats.org/api/packages/<paquete>/recent · https://pypistats.org/api/packages/<paquete>/overall?mirrors=false"
            " · https://pypi.org/pypi/<paquete>/json", "",
            "BigQuery público (bigquery-public-data.pypi.file_downloads): NO usado, sin bq/gcloud ni credenciales en esta máquina.", "",
            "## Stack Overflow Developer Survey 2026 · Web frameworks and technologies (n = 10.281)\n",
            "Copiado de ../pruebas-lenguajes-vs/FUENTES-so2026.md; verificado contra la página el 2026-11-04.\n",
            "| framework | uso | quieren usarlo | admirado |", "|---|---|---|---|",
            "| FastAPI | 18,5 % (1.903 de 10.281) | 13,5 % | 51,3 % |",
            "| Flask | 12,5 % (1.284) | 7,1 % | 38,1 % |",
            "| Django | 11,3 % (1.160) | 8,2 % | 43,8 % |", "",
            "Starlette, Litestar, Sanic y Falcon NO aparecen en la lista de la encuesta.",
            "Uso: https://survey.stackoverflow.co/2026/technology/data/web-framework · "
            "Querido/admirado: https://survey.stackoverflow.co/2026/technology/data/da-webframe", ""]
    (AQUI / "FUENTES-adopcion.md").write_text("\n".join(out), encoding="utf-8")
    print("\n".join(out))
    print(f"[ok] {AQUI / 'FUENTES-adopcion.md'} ({date.today()})")


if __name__ == "__main__":
    main()
