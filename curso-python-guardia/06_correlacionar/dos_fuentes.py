# -*- coding: utf-8 -*-
"""Leccion 6 — Correlacionar dos logs: por identificador, no por hora."""
import random
import re
import shutil
import sys
import tempfile
from collections import Counter
from datetime import datetime, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from comun.registro import generar  # noqa: E402

base = Path(tempfile.mkdtemp())
app = generar(base / "app.log", minutos=60)
LINEA = re.compile(r"^(?P<hora>\S+Z) +(?P<nivel>[A-Z]+) +(?P<servidor>\S+) +"
                   r"(?P<peticion>req-\d+) +(?P<ruta>\S+) +(?P<codigo>\d{3}) +(?P<ms>\d+)ms")

# El log del balanceador: la MISMA peticion, con otro formato y otro reloj (va 1,2 s adelantado)
az = random.Random(4)
balanceador = base / "balanceador.log"
filas_app = [m.groupdict() for m in map(LINEA.match, app.read_text(encoding="utf-8").splitlines()) if m]
with balanceador.open("w", encoding="utf-8") as f:
    for fila in filas_app:
        t = datetime.strptime(fila["hora"][:23], "%Y-%m-%dT%H:%M:%S.%f") + timedelta(seconds=1.2)
        espera = int(fila["ms"]) + az.randint(2, 40)
        f.write(f'{t.strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3]}Z lb-01 "{fila["ruta"]}" '
                f'{fila["codigo"]} {espera} id={fila["peticion"]} cliente=10.0.{az.randint(1, 9)}.{az.randint(2, 250)}\n')

print("== 6.1 · La misma peticion, en dos logs ==")
print(f"  app          {app.read_text(encoding='utf-8').splitlines()[0][:76]}")
print(f"  balanceador  {balanceador.read_text(encoding='utf-8').splitlines()[0][:76]}")
print("  Otro formato, otro nombre para el id, y los relojes NO estan igual de sincronizados.")

print()
print("== 6.2 · LA TRAMPA: juntarlos por hora ==")
lb = balanceador.read_text(encoding="utf-8").splitlines()
por_segundo = {}
for f in filas_app:
    por_segundo.setdefault(f["hora"][:19], []).append(f)
media_por_segundo = len(filas_app) / len(por_segundo)
print(f"  en un segundo cualquiera hay {media_por_segundo:.1f} peticiones de media")
ID_LB = re.compile(r"id=(req-\d+)")
aciertos = emparejadas = 0
for l in lb:
    candidatos = por_segundo.get(l[:19])
    if not candidatos:
        continue
    emparejadas += 1
    if candidatos[0]["peticion"] == ID_LB.search(l).group(1):
        aciertos += 1
print(f"  emparejando por segundo: {emparejadas} parejas, y solo {aciertos} son la peticion buena "
      f"({aciertos / emparejadas * 100:.0f}%)")
print("  Ademas los relojes van a 1,2 s de diferencia. Juntar por hora es inventarse parejas.")

print()
print("== 6.3 · Por identificador: un indice y una pasada ==")
ID = re.compile(r"id=(req-\d+)")
indice = {f["peticion"]: f for f in filas_app}          # dict: buscar es inmediato
print(f"  indice con {len(indice)} peticiones de app")
unidas, huerfanas = [], 0
for l in lb:
    m = ID.search(l)
    fila = indice.get(m.group(1)) if m else None
    if fila is None:
        huerfanas += 1
        continue
    espera_lb = int(l.split()[4])
    unidas.append((fila, espera_lb, espera_lb - int(fila["ms"])))
print(f"  unidas: {len(unidas)}   sin pareja: {huerfanas}")

print()
print("== 6.4 · Y ahora la pregunta de la guardia ==")
cola = [d for _, _, d in unidas]
print(f"  diferencia entre lo que mide el balanceador y lo que mide la app:")
print(f"    minima {min(cola)} ms · maxima {max(cola)} ms · media {sum(cola) / len(cola):.1f} ms")
print("  Esa diferencia es el tiempo que la peticion pasa FUERA de tu codigo.")
malas = Counter(f["ruta"] for f, _, _ in unidas if f["codigo"] == "500")
print(f"  rutas con 500 vistas desde el balanceador: {dict(malas.most_common(3))}")
print("  Si el balanceador ve 500 y tu app no los tiene, el problema esta antes de tu app.")

shutil.rmtree(base)
