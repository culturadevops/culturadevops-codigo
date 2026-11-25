# -*- coding: utf-8 -*-
"""Leccion 9 — Logs rotados y comprimidos: el orden del nombre no es el orden del tiempo."""
import gzip
import shutil
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from comun.registro import generar  # noqa: E402

base = Path(tempfile.mkdtemp())
# Lo que hay de verdad en /var/log: el actual, el de ayer, y los viejos comprimidos.
generar(base / "app.log", minutos=50, semilla=1)   # el actual llega hasta el incidente
generar(base / "app.log.1", minutos=10, semilla=2)
for n in (2, 3, 10, 11):
    generar(base / f"app.log.{n}.gz", minutos=10, semilla=n, comprimido=True)

print("== 9.1 · Lo que hay en la carpeta ==")
for p in sorted(base.iterdir()):
    print(f"  {p.name:<16} {p.stat().st_size / 1024:>7.1f} KB")

print()
print("== 9.2 · LA TRAMPA: ordenar por nombre ==")
print(f"  sorted():  {[p.name for p in sorted(base.iterdir())]}")
print("  app.log.10 queda ANTES de app.log.2: es orden de texto, no de numero.")
print("  Y app.log, el actual, queda el primero cuando es el ULTIMO en el tiempo.")


def orden_de_rotacion(p):
    """app.log -> 0 · app.log.1 -> 1 · app.log.2.gz -> 2 ..."""
    trozos = p.name.replace(".gz", "").split(".")
    return int(trozos[-1]) if trozos[-1].isdigit() else 0


ordenados = sorted(base.iterdir(), key=orden_de_rotacion, reverse=True)
print(f"  del mas viejo al mas nuevo: {[p.name for p in ordenados]}")

print()
print("== 9.3 · Abrir .gz sin descomprimir a disco ==")


def abrir(p):
    return gzip.open(p, "rt", encoding="utf-8") if p.suffix == ".gz" else open(p, encoding="utf-8")


total = 0
for p in ordenados:
    with abrir(p) as f:
        n = sum(1 for _ in f)
    total += n
    print(f"  {p.name:<16} {n:>6} lineas")
print(f"  total: {total} lineas de {len(ordenados)} ficheros, sin descomprimir nada a disco")

print()
print("== 9.4 · Una sola secuencia de lineas ==")


def todas_las_lineas(carpeta):
    for p in sorted(carpeta.iterdir(), key=orden_de_rotacion, reverse=True):
        with abrir(p) as f:
            yield from f


primeras = [l[:24] for _, l in zip(range(2), todas_las_lineas(base))]
print(f"  primera linea leida: {primeras[0]}  (del fichero mas viejo)")
errores = sum(1 for l in todas_las_lineas(base) if " ERROR " in l)
print(f"  errores en TODA la rotacion: {errores}")
print("  Un generador que encadena ficheros: el resto del analisis no se entera")
print("  de si venian comprimidos, rotados o de un solo fichero.")

print()
print("== 9.5 · El detalle que muerde: el comprimido no se puede recorrer al reves ==")
p = base / "app.log.2.gz"
print(f"  {p.name}: {p.stat().st_size / 1024:.1f} KB comprimido")
with gzip.open(p, "rt", encoding="utf-8") as f:
    descomprimido = len(f.read())
print(f"  descomprimido son {descomprimido / 1024:.1f} KB: {descomprimido / p.stat().st_size:.1f} veces mas")
print("  Para ver el final de un .gz hay que descomprimirlo entero. No hay atajo.")

shutil.rmtree(base)
