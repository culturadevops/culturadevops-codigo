# -*- coding: utf-8 -*-
"""715 · ruff frente a flake8 + isort, y ty frente a mypy, sobre el MISMO código. Dentro del contenedor (--cpus 2).

Código del linter: la biblioteca estándar de Python 3.14.10 de la imagen (Lib sin site-packages ni test).
Reglas: flake8 7.5.0 por defecto (pycodestyle + pyflakes + mccabe apagado) + isort 9.0.2 --check-only;
ruff 0.17.3 con --select E,W,F,I --preview (pycodestyle, pyflakes, isort) y línea de 79 como flake8.
Los dos usan 2 hilos o procesos: flake8 -j 2, isort --jobs 2, RAYON_NUM_THREADS=2 para ruff y ty. Sin caché (ruff --no-cache).
Tipos: el código fuente de rich 15.0.0 (sdist), con sus dependencias instaladas; mypy 2.4.1 en frío (sin caché) frente a ty 0.0.95.
"""
import json
import os
import pathlib
import re
import shutil
import subprocess
import time

T = "/tmp/tools/bin"
ENV = {**os.environ, "RAYON_NUM_THREADS": "2"}
REPS = 3


def correr(cmd, cwd=None):
    t0 = time.perf_counter()
    r = subprocess.run(cmd, capture_output=True, text=True, env=ENV, cwd=cwd)
    return round(time.perf_counter() - t0, 2), r.stdout + r.stderr


def preparar():
    subprocess.run(["uv", "venv", "-q", "/tmp/tools", "--python", "python"], check=True)
    subprocess.run(["uv", "pip", "install", "-q", "--python", f"{T}/python", "ruff==0.17.3", "flake8==7.5.0", "isort==9.0.2",
                    "mypy==2.4.1", "ty==0.0.95", "rich==15.0.0"], check=True)
    lib = pathlib.Path(subprocess.check_output(["python", "-c", "import sysconfig;print(sysconfig.get_paths()['stdlib'])"], text=True).strip())
    shutil.copytree(lib, "/tmp/code", ignore=shutil.ignore_patterns("site-packages", "test", "__pycache__", "lib-dynload"))
    subprocess.run(["python", "-m", "pip", "download", "-q", "--no-deps", "--no-binary", ":all:",
                    "rich==15.0.0", "-d", "/tmp/sd"], check=True)
    sd = next(pathlib.Path("/tmp/sd").glob("rich-*.tar.gz"))
    shutil.unpack_archive(sd, "/tmp/sd")
    return next(pathlib.Path("/tmp/sd").glob("rich-15.0.0"))


def main():
    rich = preparar()
    py = list(pathlib.Path("/tmp/code").rglob("*.py"))
    lineas = sum(len(p.read_bytes().splitlines()) for p in py)
    rpy = list((rich / "rich").rglob("*.py"))
    print(json.dumps({"info": "codigo", "archivos": len(py), "lineas": lineas, "rich_archivos": len(rpy),
                      "rich_lineas": sum(len(p.read_bytes().splitlines()) for p in rpy)}), flush=True)
    casos = {
        "flake8": [f"{T}/flake8", "-j", "2", "/tmp/code"],
        "isort": [f"{T}/isort", "--check-only", "--jobs", "2", "/tmp/code"],
        "ruff": [f"{T}/ruff", "check", "--no-cache", "--preview", "--select", "E,W,F,I", "--line-length", "79",
                 "--output-format", "concise", "/tmp/code"],
        "mypy": [f"{T}/mypy", "--cache-dir", "/dev/null", "--python-executable", f"{T}/python", "rich"],
        "ty": [f"{T}/ty", "check", "--python", "/tmp/tools", "--output-format", "concise", "rich"],
    }
    for rep in range(REPS):
        orden = list(casos) if rep % 2 == 0 else list(casos)[::-1]
        for k in orden:
            seg, salida = correr(casos[k], cwd=str(rich) if k in ("mypy", "ty") else None)
            hall = salida.strip().splitlines()
            print(json.dumps({"caso": k, "rep": rep, "seg": seg, "lineas_salida": len(hall), "cola": hall[-3:],
                              "version": "", "muestra": hall[:3]}), flush=True)
    for k, cmd in (("ruff", "--version"), ("flake8", "--version"), ("isort", "--version"), ("mypy", "--version"), ("ty", "--version")):
        v = [l.strip() for l in correr([f"{T}/{k}", cmd])[1].splitlines() if re.search(r"\d+\.\d+", l)][:1]
        print(json.dumps({"info": "version", "caso": k, "v": v}), flush=True)


if __name__ == "__main__":
    main()
