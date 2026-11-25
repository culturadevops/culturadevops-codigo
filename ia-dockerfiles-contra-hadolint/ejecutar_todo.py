# -*- coding: utf-8 -*-
"""Regenera todo el 711 y deja Docker limpio (builder, red, contenedores e imágenes v711-*).
Reanudable: no vuelve a pedir nada a ninguna IA ni a medir lo que ya tiene su .medida.json.
Para repetir desde cero, mueve muestras/ y referencia/*.medida.json a _ARCHIVO/.

  python ejecutar_todo.py
"""
import os
import subprocess
import sys

AQUI = os.path.dirname(os.path.abspath(__file__))


def py(*a):
    subprocess.run([sys.executable, *a], cwd=AQUI, check=True, env={**os.environ, "PYTHONUTF8": "1"})


if __name__ == "__main__":
    try:
        py("crear_apps.py")          # los lockfiles ya están; para regenerarlos: crear_apps.py --locks
        py("medir.py", "referencia")
        py("generar.py", "qwen")
        py("generar.py", "claude")
        py("analizar.py")
        py("resumen.py")
        py("diagnostico.py")
        py("revision_minima.py")
    finally:
        sys.path.insert(0, AQUI)
        import banco
        banco.limpiar()
        print("docker limpio:", banco.docker(["images", "--filter", "reference=v711-*", "-q"]).stdout.split() or "sin imágenes v711-*")
