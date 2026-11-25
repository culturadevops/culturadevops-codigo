# -*- coding: utf-8 -*-
"""715 · Recorre la matriz de hilos DENTRO del contenedor (lo lanza ejecutar_todo.py con --cpus 2 y --cpus 4).

Lados: py-gil (CPython 3.14.10 normal), py-t (3.14.10t, sin GIL) y py-t con PYTHON_GIL=1 (el mismo binario, GIL forzado).
Orden intercalado por repetición para que ningún lado se lleve siempre la máquina «fresca».
"""
import json
import os
import subprocess
import sys

LADOS = [("3.14 con GIL", "py-gil", {}), ("3.14t sin GIL", "py-t", {}), ("3.14t con PYTHON_GIL=1", "py-t", {"PYTHON_GIL": "1"})]
REPS = 3

for rep in range(REPS):
    for modo in ("primos", "json"):
        for hilos in (1, 2, 4):
            orden = LADOS if rep % 2 == 0 else LADOS[::-1]
            for nombre, exe, env in orden:
                r = subprocess.run([exe, "hilos.py", modo, str(hilos)], capture_output=True, text=True,
                                   env={**os.environ, **env}, check=True)
                d = json.loads(r.stdout)
                d.update(lado=nombre, rep=rep, cpus=sys.argv[1])
                print(json.dumps(d), flush=True)
