# -*- coding: utf-8 -*-
"""Leccion 12 — triaje.py contra la noche del incidente: cinco preguntas de guardia."""
import os
import shutil
import subprocess
import sys
import tempfile
import time
from pathlib import Path

AQUI = Path(__file__).resolve().parent
sys.path.insert(0, str(AQUI.parent))
from comun.registro import generar  # noqa: E402

tmp = Path(tempfile.mkdtemp())
logs = tmp / "logs"
logs.mkdir()
generar(logs / "app.log", minutos=60)                                   # el de esta noche
generar(logs / "app.log.1", minutos=20, semilla=77)                     # el de ayer
generar(logs / "app.log.2.gz", minutos=20, semilla=78, comprimido=True)  # y el anterior
with (logs / "app.log").open("a", encoding="utf-8") as f:
    f.write("Traceback (most recent call last):\n")

print("== los ficheros ==")
for p in sorted(logs.iterdir()):
    print(f"  {p.name:<14} {p.stat().st_size / 1024 / 1024:>5.1f} MB")


def triaje(titulo, *args):
    print()
    print(f"== {titulo} ==")
    print(f"  $ python triaje.py {' '.join(args)}")
    t0 = time.perf_counter()
    r = subprocess.run([sys.executable, str(AQUI / "triaje.py"), *args],
                       capture_output=True, text=True, encoding="utf-8", cwd=logs,
                       env=dict(os.environ, PYTHONIOENCODING="utf-8"))
    for l in (r.stdout + r.stderr).splitlines():
        print(f"  {l}")
    print(f"  [{time.perf_counter() - t0:.1f} s · codigo {r.returncode}]")
    return r.returncode


triaje("1 · La hora entera, que es lo primero que haces", "app.log")
triaje("2 · Solo la ventana del aviso", "app.log", "--desde", "03:10", "--hasta", "03:20")
triaje("3 · Un rato tranquilo: asi se ve cuando NO pasa nada",
       "app.log", "--desde", "02:40", "--hasta", "02:50")
triaje("4 · Todos los ficheros, incluido el .gz", "app.log*")
triaje("5 · Para pegarlo en el ticket", "app.log", "--desde", "03:12", "--hasta", "03:15", "--json")

shutil.rmtree(tmp)
