# -*- coding: utf-8 -*-
"""Leccion 4 — Contar: 3.000 errores distintos que en realidad son tres."""
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
lineas = log.read_text(encoding="utf-8").splitlines()
errores = [l for l in lineas if " ERROR " in l]

print("== 4.1 · Los errores de la noche ==")
print(f"  {len(errores)} lineas de ERROR de {len(lineas)} en total")
print(f"  una: {errores[0][60:]}")

print()
print("== 4.2 · LA TRAMPA: contar el mensaje tal cual ==")
tal_cual = Counter(l.split(" ", 4)[4] for l in errores)
print(f"  mensajes DISTINTOS: {len(tal_cual)}")
for msg, n in tal_cual.most_common(3):
    print(f"    {n:>4}  {msg[:62]}")
print("  Cada mensaje lleva el id de la peticion y los milisegundos dentro,")
print("  asi que casi todos son unicos. El 'top' no dice nada.")

NUMEROS = re.compile(r"\d+")
IDS = re.compile(r"\b(req-\w+|[0-9a-f]{8}-[0-9a-f-]{27})\b")
RUTA_ID = re.compile(r"/\d+\b")


def patron(mensaje):
    """Deja el ESQUELETO del mensaje: fuera ids, numeros y rutas con id."""
    m = IDS.sub("<id>", mensaje)
    m = RUTA_ID.sub("/<n>", m)
    return NUMEROS.sub("<n>", m)


print()
print("== 4.3 · Normalizar y CONTAR PATRONES ==")
patrones = Counter(patron(l.split(" ", 4)[4]) for l in errores)
print(f"  patrones distintos: {len(patrones)}")
for p, n in patrones.most_common(5):
    print(f"    {n:>4}  {p[:72]}")

print()
print("== 4.4 · Y ahora cortar por donde duele ==")
por_servidor = Counter(l.split()[2] for l in errores)
print(f"  por servidor: {dict(sorted(por_servidor.items()))}")
print("  Los tres igual: no es una maquina, es algo compartido (la base de datos).")
rutas = Counter(l.split()[4] for l in errores)
print(f"  por ruta:     {dict(rutas.most_common())}")
minutos = Counter(l[11:16] for l in errores)
print(f"  por minuto:   {dict(sorted(minutos.items()))}")
print("  Cuatro minutos exactos. Eso ya es una ventana para mirar los despliegues.")

shutil.rmtree(base)
