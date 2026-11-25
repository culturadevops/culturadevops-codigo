# -*- coding: utf-8 -*-
"""Leccion 7 — Percentiles: la media dice que todo va bien mientras el 1% se cae."""
import re
import shutil
import statistics
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from comun.registro import generar  # noqa: E402

base = Path(tempfile.mkdtemp())
log = generar(base / "app.log", minutos=60)
MS = re.compile(r" (\d+)ms")
# Una hora NORMAL: dejamos fuera los cuatro minutos del incidente, que ya conocemos.
lineas = [l for l in log.read_text(encoding="utf-8").splitlines() if not l[11:16].startswith("03:1")]
lat = [int(m.group(1)) for m in map(MS.search, lineas) if m]

print("== 7.1 · Las latencias de una hora SIN incidente ==")
print(f"  {len(lat)} peticiones, ninguna de los cuatro minutos malos")
print(f"  media    {statistics.mean(lat):7.1f} ms")
print(f"  mediana  {statistics.median(lat):7.1f} ms")
print("  Con esa media, el panel esta en verde y nadie llama a nadie.")

print()
print("== 7.2 · Los percentiles cuentan otra cosa ==")
orden = sorted(lat)


def pct(datos, p):
    """El valor por debajo del cual esta el p% de las peticiones."""
    return datos[min(len(datos) - 1, int(len(datos) * p / 100))]


for p in (50, 90, 95, 99, 99.9):
    print(f"  p{p:<5} {pct(orden, p):>6} ms")
print(f"  maximo {orden[-1]:>6} ms")
print(f"  El p99 es {pct(orden, 99) / statistics.mean(lat):.1f} veces la media.")

print()
print("== 7.3 · Cuanta gente es ese 1% ==")
lentas = sum(1 for x in lat if x > 1000)
print(f"  peticiones de mas de 1 s: {lentas} ({lentas / len(lat) * 100:.1f}%)")
print(f"  en una hora normal, eso son {lentas} personas esperando mas de un segundo.")
print("  Y ninguna aparece como error: son 200, con su latencia escondida en la media.")

print()
print("== 7.4 · LA TRAMPA: promediar percentiles ==")
print("  Ahora con la hora ENTERA, incidente incluido, que es lo que ve tu panel.")
todas, por_minuto = [], {}
for l in log.read_text(encoding="utf-8").splitlines():
    m = MS.search(l)
    if not m:
        continue
    todas.append(int(m.group(1)))
    por_minuto.setdefault(l[11:16], []).append(int(m.group(1)))
p95_minuto = [pct(sorted(v), 95) for v in por_minuto.values()]
print(f"  p95 de cada minuto, y luego su media: {statistics.mean(p95_minuto):.0f} ms")
print(f"  p95 de verdad, sobre las {len(todas)} peticiones: {pct(sorted(todas), 95)} ms")
print("  Un percentil no se puede promediar: hay que recalcularlo sobre los datos.")
print("  Por eso los paneles que guardan 'el p95 por minuto' mienten al juntar la hora.")

print()
print("== 7.5 · quantiles de la biblioteca estandar ==")
q = statistics.quantiles(lat, n=100, method="inclusive")
print(f"  statistics.quantiles(lat, n=100)[94] -> {q[94]:.0f} ms  (p95)")
print(f"  statistics.quantiles(lat, n=100)[98] -> {q[98]:.0f} ms  (p99)")
print("  Interpola entre dos valores, asi que puede no coincidir con el dato exacto.")

shutil.rmtree(base)
