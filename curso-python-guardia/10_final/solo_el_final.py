# -*- coding: utf-8 -*-
"""Leccion 10 — Ver el final de un log enorme sin leerlo entero."""
import io
import shutil
import sys
import tempfile
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from comun.registro import generar  # noqa: E402

base = Path(tempfile.mkdtemp())
log = generar(base / "app.log", minutos=600)
tam = log.stat().st_size
print("== 10.1 · El log de la semana ==")
print(f"  app.log   {tam / 1024 / 1024:.1f} MB")
print("  (en la maquina de verdad seran gigas; la idea es la misma)")


def ultimas_leyendo_todo(ruta, n):
    with open(ruta, encoding="utf-8") as f:
        return f.read().splitlines()[-n:]


def ultimas_con_deque(ruta, n):
    from collections import deque
    with open(ruta, encoding="utf-8") as f:
        return list(deque(f, maxlen=n))


def ultimas_con_seek(ruta, n, trozo=64 * 1024):
    """Lee el fichero desde el final, a trozos, hasta tener n lineas."""
    with open(ruta, "rb") as f:
        f.seek(0, io.SEEK_END)
        fin = f.tell()
        datos = b""
        while fin > 0 and datos.count(b"\n") <= n:
            salto = min(trozo, fin)
            fin -= salto
            f.seek(fin)
            datos = f.read(salto) + datos
    return datos.decode("utf-8").splitlines()[-n:]


print()
print("== 10.2 · Tres formas de ver las ultimas 20 lineas ==")
for nombre, fn in (("read().splitlines()[-20:]", ultimas_leyendo_todo),
                   ("deque(f, maxlen=20)", ultimas_con_deque),
                   ("seek desde el final", ultimas_con_seek)):
    t0 = time.perf_counter()
    ultimas = fn(log, 20)
    dur = time.perf_counter() - t0
    print(f"  {nombre:<28} {dur * 1000:7.1f} ms   {len(ultimas)} lineas")
print(f"  Las tres dan lo mismo. Las dos primeras LEEN LOS {tam / 1024 / 1024:.1f} MB para eso.")
print("  El seek lee 64 KB. Y la diferencia crece con el tamano del fichero.")

print()
print("== 10.3 · La ultima linea, que es lo que miras primero ==")
print(f"  {ultimas_con_seek(log, 1)[0][:78]}")

print()
print("== 10.4 · Lo mismo para 'que paso entre las 03:10 y las 03:20' ==")
t0 = time.perf_counter()
dentro = 0
with open(log, encoding="utf-8") as f:
    for l in f:
        if l[11:16] < "03:10":
            continue
        if l[11:16] > "03:20":
            break                        # el log esta ORDENADO: no hay que seguir
        dentro += 1
print(f"  {dentro} lineas en la ventana, en {(time.perf_counter() - t0) * 1000:.0f} ms")
print("  El break es el truco: en un log ordenado, pasada la ventana no hay nada mas.")
print("  Sin el break, esto recorre el fichero entero para nada.")

shutil.rmtree(base)
