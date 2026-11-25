# -*- coding: utf-8 -*-
"""715 · pip frente a uv instalando EL MISMO requirements.txt (56 paquetes, versiones exactas). Dentro del contenedor.

Mismo estado en los dos lados:
- el mismo intérprete base (python oficial 3.14.10) y el mismo tipo de venv (`python -m venv --without-pip`);
- pip 26.2.2 instala con `--python` desde fuera del venv; uv 0.13.6 con `--compile-bytecode`, porque pip compila los .pyc
  por defecto y uv no (sin eso, uv haría menos trabajo). La fila «uv sin compilar» va aparte, como dato;
- frío = caché vacía (baja de PyPI); caliente = venv nuevo con la caché de la vuelta anterior;
- al final se compara la lista instalada (`uv pip freeze`) y el número de .pyc de los dos venvs.
"""
import json
import os
import pathlib
import shutil
import subprocess
import time

REQ = "/banco/requirements.txt"
REPS = 3


def sh(cmd, env=None):
    t0 = time.perf_counter()
    subprocess.run(cmd, check=True, env={**os.environ, **(env or {})}, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)
    return round(time.perf_counter() - t0, 2)


def venv(path):
    shutil.rmtree(path, ignore_errors=True)
    subprocess.run(["python", "-m", "venv", "--without-pip", path], check=True)


def instalar(lado, v, cache):
    if lado == "pip":
        return sh(["python", "-m", "pip", "--python", f"{v}/bin/python", "install", "-q", "--disable-pip-version-check",
                   "--cache-dir", cache, "-r", REQ])
    extra = ["--compile-bytecode"] if lado == "uv" else []
    return sh(["uv", "pip", "install", "-q", "--python", f"{v}/bin/python", *extra, "-r", REQ], {"UV_CACHE_DIR": cache})


def estado(v):
    fr = subprocess.run(["uv", "pip", "freeze", "--python", f"{v}/bin/python"], capture_output=True, text=True, check=True).stdout
    pyc = sum(1 for _ in pathlib.Path(v).rglob("*.pyc"))
    return sorted(fr.split()), pyc


LADOS = ["pip", "uv", "uv sin compilar"]
for rep in range(REPS):
    orden = LADOS if rep % 2 == 0 else LADOS[::-1]
    for lado in orden:
        v, cache = f"/tmp/v-{rep}-{lado.replace(' ', '_')}", f"/tmp/cache-{rep}-{lado.replace(' ', '_')}"
        shutil.rmtree(cache, ignore_errors=True)
        venv(v)
        frio = instalar(lado, v, cache)
        lista, pyc = estado(v)
        venv(v)
        caliente = instalar(lado, v, cache)
        lista2, pyc2 = estado(v)
        print(json.dumps({"lado": lado, "rep": rep, "frio": frio, "caliente": caliente, "paquetes": len(lista),
                          "pyc": pyc, "pyc_caliente": pyc2, "igual_frio_caliente": lista == lista2, "lista": lista}), flush=True)
        shutil.rmtree(v, ignore_errors=True)
        shutil.rmtree(cache, ignore_errors=True)
