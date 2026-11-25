# -*- coding: utf-8 -*-
"""Leccion 2 — Partir la linea: lo que se descarta en silencio es lo que te falta."""
import re
import shutil
import sys
import tempfile
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from comun.registro import generar  # noqa: E402

base = Path(tempfile.mkdtemp())
log = generar(base / "app.log", minutos=60)

# Dos lineas que TAMBIEN estan en el log de verdad y no tienen ese formato:
extra = [
    "Traceback (most recent call last):",
    '  File "/srv/app/pool.py", line 88, in obtener',
    "TimeoutError: pool agotado",
    "2026-09-22T03:14:02.511Z INFO    web-02 req-004410 /api/pedidos 200 91ms",
]
with open(log, "a", encoding="utf-8") as f:
    f.write("\n".join(extra) + "\n")

lineas = log.read_text(encoding="utf-8").splitlines()
print("== 2.1 · Una linea del log ==")
print(f"  {lineas[0]}")

print()
print("== 2.2 · LA TRAMPA: partir por espacios y coger posiciones ==")
raros = 0
niveles = Counter()
for l in lineas:
    trozos = l.split()
    try:
        niveles[trozos[1]] += 1
    except IndexError:
        raros += 1
print(f"  niveles contados: {dict(niveles.most_common(6))}")
print("  Los tres ultimos NO son niveles: son trozos del traceback y de la ruta del")
print("  fichero, contados como si lo fueran.")
print(f"  lineas sin segundo trozo: {raros}")
print("  Nadie dijo nada. Los numeros del informe ya estan mal.")

LINEA = re.compile(
    r"^(?P<hora>\S+Z) +(?P<nivel>[A-Z]+) +(?P<servidor>\S+) +(?P<peticion>req-\d+) +"
    r"(?P<ruta>\S+) +(?P<codigo>\d{3}) +(?P<ms>\d+)ms")

print()
print("== 2.3 · Con una expresion regular con nombres, y CONTANDO lo que no casa ==")
casan, no_casan, ejemplos = 0, 0, []
niveles = Counter()
for l in lineas:
    m = LINEA.match(l)
    if not m:
        no_casan += 1
        if len(ejemplos) < 2:
            ejemplos.append(l)
        continue
    casan += 1
    niveles[m["nivel"]] += 1
print(f"  casan: {casan}   NO casan: {no_casan}")
for e in ejemplos:
    print(f"    sin parsear -> {e[:58]}")
print(f"  niveles de verdad: {dict(niveles.most_common())}")
print(f"  un ejemplo entero: {LINEA.match(lineas[0]).groupdict()}")

print()
print("== 2.4 · Por que importa contar los descartes ==")
print(f"  {no_casan} de {len(lineas)} lineas ({no_casan / len(lineas) * 100:.2f}%) no encajan.")
print("  Si ese porcentaje sube de golpe, el formato cambio o hay trazas nuevas:")
print("  o sea, es una senal del incidente, no ruido que se tira.")

shutil.rmtree(base)
