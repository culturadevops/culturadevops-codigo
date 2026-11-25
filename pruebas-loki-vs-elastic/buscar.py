#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""buscar.py — LAS DOS clases de búsqueda, en los dos motores. Vídeo 229.

⚠️ El rango de tiempo sale de `base.txt`, que escribe `ingerir.py`: las fechas del corpus se
desplazan al ingerir porque Loki no acepta registros de hace más de una semana.

⛔ Se miden las dos a propósito, y esto es lo que hace honesto al vídeo:
   A) por ETIQUETA    servicio=pagos y nivel=ERROR   → Loki debería ir bien: eso SÍ lo indexa
   B) por CONTENIDO   una frase que sale 10 veces    → Elasticsearch debería ir bien: Loki no
                                                        indexa el texto, así que le toca leerlo
Enseñar solo una de las dos sería propaganda.
"""
import time

import requests

LOKI = "http://loki:3100/loki/api/v1/query_range"
ES = "http://elastic:9200/registros/_search"
AGUJA = "pago rechazado por el banco emisor"
BASE = int(open("/w/base.txt").read().strip())   # el mismo desplazamiento que uso al ingerir
DESDE, HASTA = BASE - 60, BASE + 200000 + 60


def crono(f, veces=3):
    """Se mide 3 veces y se queda la MEJOR: la primera incluye calentar cachés."""
    mejor, res = None, None
    for _ in range(veces):
        t = time.time()
        res = f()
        d = time.time() - t
        mejor = d if mejor is None else min(mejor, d)
    return mejor * 1000, res


print("A · POR ETIQUETA — servicio=pagos, nivel=ERROR")


def es_etiqueta():
    r = requests.post(ES, json={"size": 0, "query": {"bool": {"filter": [
        {"term": {"servicio": "pagos"}}, {"term": {"nivel": "ERROR"}}]}}}, timeout=120)
    return r.json()["hits"]["total"]["value"]


def loki_etiqueta():
    r = requests.get(LOKI, params={
        "query": '{servicio="pagos", nivel="ERROR"}',
        "start": DESDE * 10**9, "end": HASTA * 10**9, "limit": 5000}, timeout=120)
    d = r.json().get("data", {}).get("result", [])
    return sum(len(s.get("values", [])) for s in d)


ms, n = crono(es_etiqueta)
print(f"   Elasticsearch  {ms:8.1f} ms   {n} coincidencias")
ms, n = crono(loki_etiqueta)
print(f"   Loki           {ms:8.1f} ms   {n} coincidencias (tope 5000)")

print()
print(f"B · POR CONTENIDO — la frase «{AGUJA}» (sale 10 veces)")


def es_contenido():
    r = requests.post(ES, json={"size": 0, "query": {
        "match_phrase": {"mensaje": AGUJA}}}, timeout=300)
    return r.json()["hits"]["total"]["value"]


def loki_contenido():
    r = requests.get(LOKI, params={
        "query": '{servicio=~".+"} |= "' + AGUJA + '"',
        "start": DESDE * 10**9, "end": HASTA * 10**9, "limit": 100}, timeout=300)
    d = r.json().get("data", {}).get("result", [])
    return sum(len(s.get("values", [])) for s in d)


ms, n = crono(es_contenido)
print(f"   Elasticsearch  {ms:8.1f} ms   {n} coincidencias")
ms, n = crono(loki_contenido)
print(f"   Loki           {ms:8.1f} ms   {n} coincidencias")

# ══════════════════════════════════════════════════════════════════════════
# ⛔ LA COMPROBACIÓN QUE FALTABA. En dos corridas anteriores Loki se quedó con parte del corpus
#    (primero por fechas viejas, después por el límite de ritmo) y los números salían igual, solo
#    que MENTÍAN. Si los dos motores no tienen lo mismo, esto para y no hay vídeo.
# ══════════════════════════════════════════════════════════════════════════
print()
print("C · ¿TIENEN LOS DOS EL MISMO CORPUS?")
# ⚠️ `track_total_hits`: sin esto Elasticsearch tope el total en 10.000 y mi propia
#    comprobación daba un falso negativo. El motor estaba bien; el que contaba mal era yo.
es_total = requests.post(ES, json={"size": 0, "track_total_hits": True,
                                   "query": {"match_all": {}}},
                         timeout=120).json()["hits"]["total"]["value"]
r = requests.get("http://loki:3100/loki/api/v1/query", params={
    "query": 'sum(count_over_time({servicio=~".+"}[60h]))',
    "time": HASTA * 10**9}, timeout=300).json()
lo_total = int(float(r["data"]["result"][0]["value"][1])) if r.get("data", {}).get("result") else 0
print(f"   Elasticsearch: {es_total} documentos")
print(f"   Loki:          {lo_total} lineas")
if es_total != lo_total:
    print(f"   ⛔ NO COINCIDEN. La comparación no vale: falta corpus en uno de los dos.")
    raise SystemExit(1)
print("   ✅ los dos tienen lo mismo: la comparación vale")
