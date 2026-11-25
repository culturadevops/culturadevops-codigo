# 715 · Arranque de una CLI que importa boto3 arriba, con import normal y con `lazy import` (PEP 810, Python 3.15).
# Lo único que cambia entre los dos archivos es la palabra `lazy`. 21 ejecuciones de `--version`, mediana en ms.
import json
import statistics
import subprocess
import sys
import time


def medir(args, n=21):
    subprocess.run([sys.executable, *args], capture_output=True, check=True)  # calienta la caché de disco
    ts = []
    for _ in range(n):
        t0 = time.perf_counter()
        subprocess.run([sys.executable, *args], capture_output=True, check=True)
        ts.append((time.perf_counter() - t0) * 1000)
    return round(statistics.median(ts), 1)


for nombre, args in (("python -c pass", ["-c", "pass"]), ("import boto3", ["cli_normal.py", "--version"]),
                     ("lazy import boto3", ["cli_lazy.py", "--version"]),
                     ("import boto3 + -X lazy_imports=all", ["-X", "lazy_imports=all", "cli_normal.py", "--version"])):
    salida = subprocess.run([sys.executable, *args], capture_output=True, text=True)
    print(json.dumps({"caso": nombre, "ms": medir(args) if salida.returncode == 0 else None,
                      "salida": (salida.stdout + salida.stderr).strip()[-200:]}), flush=True)
