#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""generar.py — el corpus de registros que se mete en LOS DOS. Vídeo 229.

⛔ LA REGLA: el mismo corpus, byte a byte, en Loki y en Elasticsearch. Si cambian los datos, la
comparación no vale nada. Por eso se genera una vez, con semilla fija, y se guarda en un fichero.

Son registros realistas de una aplicación web: fecha, nivel, servicio, ruta, código, latencia y un
mensaje. Lo que tendría cualquiera.
"""
import json
import random
import sys

N = int(sys.argv[1]) if len(sys.argv) > 1 else 200_000
random.seed(42)

SERVICIOS = ["api", "web", "pagos", "auth", "cola"]
RUTAS = ["/", "/login", "/api/pedidos", "/api/pedidos/{id}", "/salud", "/estatico"]
NIVELES = ["INFO"] * 90 + ["WARN"] * 7 + ["ERROR"] * 3

# ⚠️ La aguja en el pajar: una cadena que aparece MUY pocas veces, para medir la búsqueda por
# CONTENIDO. Si buscas algo que sale en todas las líneas no estás midiendo el índice.
AGUJA = "pago rechazado por el banco emisor"

with open("registros.jsonl", "w", encoding="utf-8") as f:
    for i in range(N):
        nivel = random.choice(NIVELES)
        serv = random.choice(SERVICIOS)
        ruta = random.choice(RUTAS)
        cod = 500 if nivel == "ERROR" else (404 if nivel == "WARN" else 200)
        # la aguja sale en ~1 de cada 20.000 líneas
        msg = AGUJA if (i % 20_000 == 7) else f"peticion atendida id={i} usuario={i % 5000}"
        f.write(json.dumps({
            "ts": 1757000000 + i,
            "nivel": nivel,
            "servicio": serv,
            "ruta": ruta,
            "codigo": cod,
            "latencia_ms": round(random.uniform(1, 400), 1),
            "mensaje": msg,
        }, ensure_ascii=False) + "\n")

print(f"{N} lineas escritas en registros.jsonl")
