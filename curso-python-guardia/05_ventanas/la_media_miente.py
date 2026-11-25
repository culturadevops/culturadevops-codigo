# -*- coding: utf-8 -*-
"""Leccion 5 — Ventanas de tiempo: la media de la hora esconde los cuatro minutos malos."""
import shutil
import sys
import tempfile
from collections import Counter
from datetime import datetime, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from comun.registro import generar  # noqa: E402

base = Path(tempfile.mkdtemp())
log = generar(base / "app.log", minutos=60)
lineas = log.read_text(encoding="utf-8").splitlines()
errores = [l for l in lineas if " ERROR " in l]

print("== 5.1 · LA TRAMPA: la media de la hora ==")
print(f"  {len(errores)} errores en 60 minutos -> {len(errores) / 60:.0f} errores por minuto de media")
print("  Con ese numero en el informe, esto parece ruido de fondo.")

por_minuto = Counter(l[11:16] for l in errores)
pico, n_pico = por_minuto.most_common(1)[0]
print()
print("== 5.2 · El mismo log, por minuto ==")
for minuto in sorted(por_minuto):
    barra = "█" * round(por_minuto[minuto] / 25)
    print(f"  {minuto}  {por_minuto[minuto]:>4}  {barra}")
print(f"  pico: {pico} con {n_pico} errores, "
      f"{n_pico / (len(errores) / 60):.0f} veces la media")
print(f"  minutos con algun error: {len(por_minuto)} de 60")

print()
print("== 5.3 · Ventana movil: cuando empieza y cuando acaba ==")
TODOS = [datetime.strptime(l[:23], "%Y-%m-%dT%H:%M:%S.%f") for l in lineas]
ERR = [datetime.strptime(l[:23], "%Y-%m-%dT%H:%M:%S.%f") for l in errores]


def tasa(momentos, t0, ancho=timedelta(minutes=1)):
    return sum(1 for t in momentos if t0 <= t < t0 + ancho)


inicio = min(ERR)
fin = max(ERR)
print(f"  primer ERROR: {inicio.strftime('%H:%M:%S')}   ultimo: {fin.strftime('%H:%M:%S')}")
print(f"  duro {(fin - inicio).seconds // 60} min {(fin - inicio).seconds % 60} s")

print()
print("== 5.4 · Lo que se pone en el parte: el PORCENTAJE, no el numero ==")
peor = 0
for etiqueta, t0 in (("minuto antes", inicio - timedelta(minutes=1)),
                     ("primer minuto malo", inicio),
                     ("minuto de despues", fin)):
    total = tasa(TODOS, t0)
    malas = tasa(ERR, t0)
    peor = max(peor, malas / total * 100)
    print(f"  {etiqueta:<20} {malas:>4} de {total:>4} peticiones fallan "
          f"({malas / total * 100:5.1f}%)")
print(f"  'Suben los errores' no es un dato. '{peor:.0f}% de las peticiones fallan' si.")

shutil.rmtree(base)
