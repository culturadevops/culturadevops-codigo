# -*- coding: utf-8 -*-
"""Leccion 11 — La muestra: mirar las primeras mil lineas y sacar conclusiones."""
import re
import shutil
import sys
import tempfile
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from comun.registro import generar  # noqa: E402

base = Path(tempfile.mkdtemp())
log = generar(base / "app.log", minutos=60)
lineas = log.read_text(encoding="utf-8").splitlines()
MS = re.compile(r" (\d+)ms")


def resumen(muestra, nombre):
    niveles = Counter(l.split()[1] for l in muestra)
    lat = [int(m.group(1)) for m in map(MS.search, muestra) if m]
    err = niveles.get("ERROR", 0) / len(muestra) * 100
    print(f"  {nombre:<26} {len(muestra):>6} lineas   {err:5.1f}% errores   "
          f"latencia media {sum(lat) / len(lat):6.0f} ms")


print("== 11.1 · La trampa de las primeras mil ==")
resumen(lineas[:1000], "head -1000")
resumen(lineas, "el fichero entero")
print("  El incidente esta en el minuto 42 de la hora. En las primeras mil lineas")
print("  no ha pasado nada todavia: 'esto esta tranquilo' y a dormir.")

print()
print("== 11.2 · Y la de las ultimas mil ==")
resumen(lineas[-1000:], "tail -1000")
print("  Tampoco: el incidente ya paso. Las dos muestras dicen que todo va bien.")

print()
print("== 11.3 · Una muestra de verdad: repartida ==")
for cada in (2, 10, 50):
    resumen(lineas[::cada], f"1 de cada {cada}")
print("  Repartida por todo el fichero, hasta 1 de cada 50 acierta el porcentaje.")
print("  La muestra vale si es del TODO. Un trozo contiguo no es una muestra:")
print("  es una ventana de tiempo, y en un incidente eso lo cambia todo.")

print()
print("== 11.4 · Lo que casi siempre es mejor: contar entero ==")
import time  # noqa: E402

t0 = time.perf_counter()
n = sum(1 for l in open(log, encoding="utf-8") if " ERROR " in l)
print(f"  contar los {n} errores del fichero entero: {(time.perf_counter() - t0) * 1000:.0f} ms")
print(f"  para {log.stat().st_size / 1024 / 1024:.1f} MB. A las tres de la manana,")
print("  el tiempo no lo gasta la maquina: lo gastas tu decidiendo si fiarte.")

shutil.rmtree(base)
