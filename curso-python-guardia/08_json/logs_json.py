# -*- coding: utf-8 -*-
"""Leccion 8 — Logs en JSON: una linea rota no puede tirar el analisis entero."""
import json
import shutil
import tempfile
from collections import Counter
from pathlib import Path

base = Path(tempfile.mkdtemp())
log = base / "app.jsonl"
buenas = [
    {"ts": "2026-09-22T03:11:58Z", "nivel": "INFO", "ruta": "/api/pedidos", "ms": 88, "codigo": 200},
    {"ts": "2026-09-22T03:12:01Z", "nivel": "ERROR", "ruta": "/api/pedidos", "ms": 3211,
     "codigo": 500, "error": "pool agotado"},
    {"ts": "2026-09-22T03:12:02Z", "nivel": "INFO", "ruta": "/salud", "codigo": 200},
]
with log.open("w", encoding="utf-8") as f:
    f.write(json.dumps(buenas[0]) + "\n")
    f.write(json.dumps(buenas[1]) + "\n")
    f.write('{"ts": "2026-09-22T03:12:01Z", "nivel": "ERROR", "ru')     # se corto el disco
    f.write("\n")
    f.write("Traceback (most recent call last):\n")                      # una traza suelta
    f.write(json.dumps(buenas[2]) + "\n")

print("== 8.1 · El fichero de esta noche (JSON por linea) ==")
for i, l in enumerate(log.read_text(encoding="utf-8").splitlines(), 1):
    print(f"  {i}: {l[:70]}")

print()
print("== 8.2 · LA TRAMPA: json.loads sin red ==")
try:
    for l in log.read_text(encoding="utf-8").splitlines():
        json.loads(l)
except json.JSONDecodeError as e:
    print(f"  JSONDecodeError en la linea 3: {e.msg}")
print("  Tres de la manana, el script se muere, y no sabes si iba por el principio")
print("  o por el final del fichero.")

print()
print("== 8.3 · LA TRAMPA 2: el except que se lo traga todo ==")
vistos = 0
for l in log.read_text(encoding="utf-8").splitlines():
    try:
        json.loads(l)
        vistos += 1
    except Exception:
        pass
print(f"  lineas leidas: {vistos} de 5. Y el script no dijo NADA.")
print("  Callar los errores es peor que reventar: el informe sale con menos datos")
print("  y con la misma cara de seguridad.")

print()
print("== 8.4 · Bien: se salta, se CUENTA y se guarda una muestra ==")


def leer_json(ruta):
    malas, muestra = 0, []
    filas = []
    for n, l in enumerate(ruta.read_text(encoding="utf-8").splitlines(), 1):
        l = l.strip()
        if not l:
            continue
        try:
            filas.append(json.loads(l))
        except json.JSONDecodeError as e:
            malas += 1
            if len(muestra) < 2:
                muestra.append((n, e.msg, l[:40]))
    return filas, malas, muestra


filas, malas, muestra = leer_json(log)
print(f"  filas buenas: {len(filas)}   rotas: {malas}")
for n, msg, texto in muestra:
    print(f"    linea {n}: {msg}  ->  {texto}")
print(f"  {malas / (len(filas) + malas) * 100:.0f}% del fichero no se pudo leer. Eso va en el informe.")

print()
print("== 8.5 · Y la clave que a veces no esta ==")
print(f"  filas sin 'ms': {sum(1 for f in filas if 'ms' not in f)}")
try:
    sum(f["ms"] for f in filas)
except KeyError as e:
    print(f"  sumar f['ms'] -> KeyError: {e}")
total = sum(f.get("ms", 0) for f in filas)
con_ms = [f for f in filas if "ms" in f]
print(f"  con .get('ms', 0): {total} ms ... repartido entre {len(filas)} filas")
print(f"  pero la media de verdad es sobre las {len(con_ms)} que SI la tienen: "
      f"{total / len(con_ms):.0f} ms")
print("  Poner 0 donde no hay dato no es un arreglo: es inventarse una medicion.")
print(f"  niveles: {dict(Counter(f['nivel'] for f in filas))}")

shutil.rmtree(base)
