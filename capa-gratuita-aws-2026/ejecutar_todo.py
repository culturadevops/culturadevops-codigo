# -*- coding: utf-8 -*-
"""Regenera SALIDA.md del vídeo 692: precios de la lista pública (calculo.py) + demos contra moto (correr.py → SALIDA-moto.md).

    python ejecutar_todo.py               (reusa los filtros de precios/)
    python ejecutar_todo.py --refrescar   (vuelve a bajar la lista de precios)
"""
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

AQUI = Path(__file__).resolve().parent
env_py = [sys.executable, "-X", "utf8"]
if "--refrescar" in sys.argv:
    subprocess.run(env_py + ["lista.py", "--refrescar"], cwd=AQUI, check=True)
calc = subprocess.run(env_py + ["calculo.py"], cwd=AQUI, capture_output=True, text=True, encoding="utf-8", check=True).stdout
subprocess.run(env_py + ["correr.py"], cwd=AQUI, check=True, stdout=subprocess.DEVNULL)
moto = (AQUI / "SALIDA-moto.md").read_text(encoding="utf-8")
txt = [f"# SALIDA — vídeo 692 · La capa gratuita de AWS en 2026", "",
       "Generado por `python ejecutar_todo.py`. **No se edita a mano.** Importes: precio de lista × uso (estimación).", "",
       f"- fecha: {datetime.now(timezone.utc):%Y-%m-%d %H:%M} UTC", "", "## Precios (calculo.py)", "", "```", calc.rstrip(), "```",
       "", "## Demos contra moto (correr.py)", "", moto.split("\n", 1)[1]]
(AQUI / "SALIDA.md").write_text("\n".join(txt) + "\n", encoding="utf-8")
print("-> SALIDA.md")
