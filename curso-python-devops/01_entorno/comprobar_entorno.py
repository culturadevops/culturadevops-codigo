# -*- coding: utf-8 -*-
"""Leccion 1 — El interprete, y por que el `python` que corres no siempre es el que crees.

La primera hora perdida de todo el mundo: instalas algo con pip, lo importas, y dice que no
existe. Casi siempre es que pip y python NO son del mismo interprete.
"""
import sys
import os
from pathlib import Path


def titulo(t):
    print(f"\n{'=' * 62}\n{t}\n{'=' * 62}")


titulo("1.1 · Quien esta ejecutando esto")
print(f"  version      {sys.version.split()[0]}")
print(f"  ejecutable   {sys.executable}")
print(f"  plataforma   {sys.platform}")

titulo("1.2 · Estoy dentro de un entorno virtual?")
# sys.prefix es donde vive este interprete; base_prefix es el Python "de verdad".
# Si son distintos, estas dentro de un venv. Es la comprobacion que usa pip.
en_venv = sys.prefix != sys.base_prefix
print(f"  sys.prefix        {sys.prefix}")
print(f"  sys.base_prefix   {sys.base_prefix}")
print(f"  -> en un venv:    {en_venv}")

titulo("1.3 · Donde busca Python lo que importas")
print("  sys.path, EN ORDEN. El primero gana:")
for i, p in enumerate(sys.path[:6]):
    print(f"    {i}. {p or '(el directorio actual)'}")
if len(sys.path) > 6:
    print(f"    ... y {len(sys.path) - 6} mas")

titulo("1.4 · LA TRAMPA: un fichero tuyo puede tapar la biblioteca estandar")
print("  El directorio actual va el PRIMERO en sys.path.")
print("  Si guardas un fichero llamado json.py y haces `import json`,")
print("  Python importa el TUYO. Y el error que ves no habla de tu fichero:")
print("  habla de que a json le falta una funcion que tu no escribiste.")
print()
print("  Comprobacion rapida de donde sale un modulo:")
import json
print(f"    json viene de  ->  {json.__file__}")

titulo("1.5 · Variables de entorno: leerlas SIN que reviente")
# os.environ[...] lanza KeyError si no existe. os.environ.get() devuelve None.
# En un script que corre en un servidor, prefieres un valor por omision a una traza.
print(f"  os.environ.get('PATH') existe: {os.environ.get('PATH') is not None}")
print(f"  os.environ.get('NO_EXISTE_12345'): {os.environ.get('NO_EXISTE_12345')}")
print(f"  con valor por omision: {os.environ.get('NO_EXISTE_12345', 'valor-por-defecto')}")

titulo("Resumen")
print("  · sys.executable te dice QUE python se esta ejecutando")
print("  · sys.prefix != sys.base_prefix te dice si estas en un venv")
print("  · el directorio actual va primero en sys.path: no llames a tus")
print("    ficheros como modulos de la estandar (json.py, os.py, random.py)")
print("  · os.environ.get() con valor por omision, no os.environ[...]")
