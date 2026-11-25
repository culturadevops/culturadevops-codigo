# -*- coding: utf-8 -*-
"""Leccion 1 — Leer el log sin cargarlo entero: el script que mata a la maquina."""
import shutil
import sys
import tempfile
import time
import tracemalloc
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from comun.registro import generar  # noqa: E402

base = Path(tempfile.mkdtemp())
log = generar(base / "app.log", minutos=90)
tam = log.stat().st_size
with open(log, encoding="utf-8") as f:
    total = sum(1 for _ in f)
print("== 1.1 · El log de esta noche ==")
print(f"  app.log   {total} lineas   {tam / 1024 / 1024:.1f} MB")
print("  (en produccion son gigas; aqui basta con esto para ver la diferencia)")


def tamano(b):
    return f"{b / 1024 / 1024:.1f} MB" if b >= 1024 * 1024 else f"{b / 1024:.0f} KB"


def medir(nombre, fn):
    tracemalloc.start()
    t0 = time.perf_counter()
    r = fn()
    dur = time.perf_counter() - t0
    _, pico = tracemalloc.get_traced_memory()
    tracemalloc.stop()
    print(f"  {nombre:<28} {r} errores   pico {tamano(pico):>8}   {dur:.2f} s")
    return pico


print()
print("== 1.2 · LA TRAMPA: read() y readlines() ==")
p1 = medir("f.read().splitlines()", lambda: sum(
    1 for l in open(log, encoding="utf-8").read().splitlines() if " ERROR " in l))
p2 = medir("f.readlines()", lambda: sum(
    1 for l in open(log, encoding="utf-8").readlines() if " ERROR " in l))


def por_lineas():
    with open(log, encoding="utf-8") as f:
        return sum(1 for l in f if " ERROR " in l)


p3 = medir("for linea in f (perezoso)", por_lineas)
print(f"  El resultado es el mismo. La memoria, {p1 / p3:.0f} veces mas.")
print("  Un fichero abierto YA es un iterador de lineas: no hace falta leerlo entero.")

print()
print("== 1.3 · Y encadenar generadores no gasta memoria ==")


def leer(ruta):
    with open(ruta, encoding="utf-8") as f:
        yield from f


def solo(lineas, texto):
    return (l for l in lineas if texto in l)


def campo(lineas, n):
    return (l.split()[n] for l in lineas)


tracemalloc.start()
from collections import Counter  # noqa: E402

cuenta = Counter(campo(solo(leer(log), " ERROR "), 2))
_, pico = tracemalloc.get_traced_memory()
tracemalloc.stop()
print(f"  errores por servidor: {dict(sorted(cuenta.items()))}")
print(f"  pico de memoria: {pico / 1024:.0f} KB para un log de {tam / 1024 / 1024:.1f} MB")
print("  Cada generador pasa UNA linea al siguiente. Nunca hay una lista entera.")

shutil.rmtree(base)
