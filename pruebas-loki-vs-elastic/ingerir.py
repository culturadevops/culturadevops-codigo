#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""ingerir.py — mete el MISMO corpus en Loki y en Elasticsearch, y cronometra cada uno.

⚠️ Se manda en lotes en los dos, porque línea a línea mediría la latencia de red, no el motor.

⛔ DOS COSAS QUE ME COSTARON UNA CORRIDA ENTERA Y VAN EN EL VÍDEO:

 1. **Loki rechaza los registros viejos.** Mi corpus tenía fechas de 2025 y Loki contestaba
    `400 · timestamp too old ... oldest acceptable timestamp is ...` a TODOS los envíos. Por
    defecto no acepta nada de hace más de una semana. Aquí las fechas se desplazan a las últimas
    horas, y el desplazamiento se guarda en `base.txt` para que la búsqueda mire el mismo rango.

 2. **Yo no miraba el código de respuesta.** Los 400 pasaron callados y la medición decía que
    Loki ocupaba 8 KB con 200.000 líneas. Ahora se comprueba cada envío y se para al primer fallo.

⛔ LA DIFERENCIA QUE ES LA TESIS DEL VÍDEO:
  · a Elasticsearch le mandas un documento con TODOS sus campos, y él los indexa todos.
  · a Loki le mandas ETIQUETAS (pocas, de valores pocos) y una LÍNEA de texto. Solo indexa las
    etiquetas: la línea la guarda comprimida y no la mira.
"""
import json
import sys
import time

import requests

LOKI = "http://loki:3100/loki/api/v1/push"
ES = "http://elastic:9200"
LOTE = 5000
ORIGEN = 1757000000  # el ts base que trae el corpus


def leer():
    with open("/w/registros.jsonl", encoding="utf-8") as f:
        for linea in f:
            yield json.loads(linea)


# Las fechas se desplazan para que la última sea "ahora": Loki no acepta nada de hace más de
# una semana, y el corpus tiene fechas fijas para ser reproducible.
BASE = int(time.time()) - 200_000
with open("/w/base.txt", "w") as f:
    f.write(str(BASE))
print(f"fechas desplazadas: base={BASE} (últimas 55 h)")


def morir(r, que):
    if r.status_code >= 300:
        print(f"[X] {que} -> {r.status_code} {r.text[:300]}")
        sys.exit(1)


# ── Elasticsearch ────────────────────────────────────────────────────────────
requests.delete(f"{ES}/registros", timeout=60)
# ⚠️ El mapeo importa: por defecto una cadena se indexa como texto analizado Y como palabra
# clave exacta en `.keyword`. Buscar por término exacto sobre el campo analizado devuelve CERO,
# y también me costó una corrida. Aquí se declara explícito para que se vea en el vídeo.
requests.put(f"{ES}/registros", json={
    "settings": {"number_of_replicas": 0},
    "mappings": {"properties": {
        "servicio": {"type": "keyword"},
        "nivel": {"type": "keyword"},
        "ruta": {"type": "keyword"},
        "codigo": {"type": "integer"},
        "latencia_ms": {"type": "float"},
        "ts": {"type": "long"},
        "mensaje": {"type": "text"},
    }}}, timeout=60)

t0 = time.time()
buf, n = [], 0
for r in leer():
    r["ts"] = BASE + (r["ts"] - ORIGEN)
    buf.append('{"index":{}}')
    buf.append(json.dumps(r, ensure_ascii=False))
    if len(buf) >= LOTE * 2:
        resp = requests.post(f"{ES}/registros/_bulk", data=("\n".join(buf) + "\n").encode(),
                             headers={"Content-Type": "application/x-ndjson"}, timeout=300)
        morir(resp, "bulk de Elasticsearch")
        n += len(buf) // 2
        buf = []
if buf:
    resp = requests.post(f"{ES}/registros/_bulk", data=("\n".join(buf) + "\n").encode(),
                         headers={"Content-Type": "application/x-ndjson"}, timeout=300)
    morir(resp, "bulk de Elasticsearch")
    n += len(buf) // 2
requests.post(f"{ES}/registros/_refresh", timeout=120)
tes = time.time() - t0
print(f"Elasticsearch: {n} documentos en {tes:.1f} s")

# ── Loki ─────────────────────────────────────────────────────────────────────
# Las etiquetas son POCAS y de valores POCOS: servicio y nivel. Meter aquí el id de usuario sería
# la explosión de cardinalidad del vídeo 221.
t0 = time.time()
flujos, n = {}, 0
ses = requests.Session()


def volcar(fl):
    if not fl:
        return
    cuerpo = {"streams": [
        {"stream": {"servicio": k[0], "nivel": k[1]}, "values": v} for k, v in fl.items()]}
    morir(ses.post(LOKI, json=cuerpo, timeout=300), "push de Loki")


for r in leer():
    ts = BASE + (r["ts"] - ORIGEN)
    r["ts"] = ts
    k = (r["servicio"], r["nivel"])
    flujos.setdefault(k, []).append([str(ts * 1_000_000_000), json.dumps(r, ensure_ascii=False)])
    n += 1
    if n % LOTE == 0:
        volcar(flujos)
        flujos = {}
volcar(flujos)
tlo = time.time() - t0
print(f"Loki:          {n} lineas en {tlo:.1f} s")
print()
print(f"   ingesta: Elasticsearch {tes:.1f} s  ·  Loki {tlo:.1f} s")
