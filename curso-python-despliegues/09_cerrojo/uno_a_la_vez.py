# -*- coding: utf-8 -*-
"""Leccion 9 — Cerrojo: dos despliegues a la vez se pisan."""
import os
import shutil
import subprocess
import sys
import tempfile
import time
from pathlib import Path

base = Path(tempfile.mkdtemp())
contador = base / "numero_de_release"

# Un "despliegue" en miniatura: lee el ultimo numero, prepara (tarda), escribe el siguiente.
DESPLIEGUE = r'''
import os, sys, time
from pathlib import Path
base, con_cerrojo = Path(sys.argv[1]), sys.argv[2] == "si"
cerrojo = base / "desplegar.lock"
if con_cerrojo:
    try:
        fd = os.open(cerrojo, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
        os.write(fd, str(os.getpid()).encode()); os.close(fd)
    except FileExistsError:
        print(f"  pid {os.getpid()}: ya hay un despliegue en curso (pid {cerrojo.read_text()}). Salgo.")
        sys.exit(75)
try:
    n = int((base / "numero_de_release").read_text())
    time.sleep(0.5)                                   # construir, copiar...
    (base / "numero_de_release").write_text(str(n + 1))
    print(f"  pid {os.getpid()}: desplegada la release {n + 1}")
finally:
    if con_cerrojo:
        cerrojo.unlink()
'''


def dos_a_la_vez(con_cerrojo):
    contador.write_text("41")
    procs = [subprocess.Popen([sys.executable, "-c", DESPLIEGUE, str(base), con_cerrojo],
                              stdout=subprocess.PIPE, text=True) for _ in range(2)]
    for p in procs:
        salida, _ = p.communicate()
        print(salida.rstrip())
    return contador.read_text(), [p.returncode for p in procs]


print("== 9.1 · LA TRAMPA: dos despliegues lanzados a la vez ==")
final, codigos = dos_a_la_vez("no")
print(f"  empezamos en 41, se desplegaron 2 -> el contador dice {final}")
print("  Los dos leyeron 41. Los dos escribieron 42. Uno se perdio.")

print()
print("== 9.2 · Con cerrojo (os.O_CREAT | os.O_EXCL) ==")
final, codigos = dos_a_la_vez("si")
print(f"  contador: {final}   codigos de salida: {sorted(codigos)}")
print("  O_EXCL crea el archivo solo si NO existe, en una sola operacion.")
print("  Comprobar con exists() y luego crearlo deja un hueco entre las dos.")

print()
print("== 9.3 · LA TRAMPA 2: el cerrojo huerfano ==")
cerrojo = base / "desplegar.lock"
cerrojo.write_text("999999")
os.utime(cerrojo, (time.time() - 3 * 3600,) * 2)
print("  un despliegue murio hace 3 horas sin borrar su cerrojo.")
final, codigos = dos_a_la_vez("si")
print(f"  y desde entonces nadie despliega: contador {final}, codigos {codigos}")

CADUCA = 30 * 60


def tomar_cerrojo(ruta):
    try:
        fd = os.open(ruta, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
    except FileExistsError:
        edad = time.time() - ruta.stat().st_mtime
        if edad < CADUCA:
            raise
        print(f"  cerrojo de hace {edad / 3600:.0f} h > {CADUCA // 60} min: lo doy por muerto y lo retiro")
        ruta.unlink()
        fd = os.open(ruta, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
    os.write(fd, str(os.getpid()).encode())
    os.close(fd)


tomar_cerrojo(cerrojo)
print(f"  cerrojo tomado por este proceso: {int(cerrojo.read_text()) == os.getpid()}")
print("  El plazo tiene que ser mas largo que el despliegue mas lento que tengas.")

shutil.rmtree(base)
