# -*- coding: utf-8 -*-
"""Leccion 3 — Horas: el log esta en UTC y tu incidente lo cuentan en hora local."""
from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo

CDMX = ZoneInfo("America/Mexico_City")
MADRID = ZoneInfo("Europe/Madrid")

linea = "2026-09-22T03:12:04.318Z INFO    web-01 req-004102 /api/pedidos 200 91ms"
print("== 3.1 · La hora del log ==")
print(f"  {linea[:24]}   <- la Z del final: UTC")

ingenua = datetime.strptime(linea[:23], "%Y-%m-%dT%H:%M:%S.%f")
print(f"  strptime sin la Z -> {ingenua}   tzinfo={ingenua.tzinfo}")
print("  Es una fecha INGENUA: no sabe en que zona esta. Y Python la deja pasar.")

print()
print("== 3.2 · LA TRAMPA: comparar una ingenua con una consciente ==")
ahora = datetime(2026, 9, 22, 3, 20, tzinfo=timezone.utc)
try:
    ingenua < ahora
except TypeError as e:
    print(f"  ingenua < consciente -> TypeError: {e}")
print("  Este es el error BUENO: se ve. El malo es cuando las dos son ingenuas")
print("  y una estaba en UTC y la otra en tu hora: restas y sale una diferencia falsa.")

consciente = ingenua.replace(tzinfo=timezone.utc)
print(f"  con tzinfo=UTC     -> {consciente}")
print(f"  ahora - incidente  -> {ahora - consciente}")

print()
print("== 3.3 · La guardia la cuentan en hora local ==")
print(f"  UTC          {consciente}")
print(f"  CDMX         {consciente.astimezone(CDMX)}")
print(f"  Madrid       {consciente.astimezone(MADRID)}")
print("  'Empezo a las 9 y cuarto de la noche' y '03:12Z' son el MISMO instante.")
print("  Guarda y compara siempre en UTC; traduce solo para escribirlo en el parte.")

print()
print("== 3.4 · LA TRAMPA 2: ordenar fechas como texto ==")
horas = ["2026-9-22T03:08:00Z", "2026-09-22T03:09:00Z", "2026-09-22T03:10:00Z"]
print("  La primera viene de otro servicio, que escribe el mes sin cero delante.")
print(f"  ordenadas como texto: {sorted(horas)}")
print("  La mas ANTIGUA queda la ultima: como texto, '2026-9' es mayor que '2026-0'.")
try:
    datetime.fromisoformat(horas[0].replace("Z", "+00:00"))
except ValueError as e:
    print(f"  y fromisoformat ni la acepta -> ValueError: {e}")
como_fecha = sorted(datetime.strptime(h, "%Y-%m-%dT%H:%M:%S%z") for h in horas)
print(f"  strptime si (es mas tolerante) -> {[d.strftime('%H:%M') for d in como_fecha]}")
print("  ISO-8601 con ceros SI se ordena como texto. Sin ceros, no. Convierte y ordena.")

print()
print("== 3.5 · El cambio de hora: una hora que pasa dos veces ==")
raro = datetime(2026, 10, 25, 2, 30, tzinfo=MADRID)
utc1 = raro.replace(fold=0).astimezone(timezone.utc)
utc2 = raro.replace(fold=1).astimezone(timezone.utc)
print(f"  25/10/2026 02:30 en Madrid existe DOS veces:")
print(f"    la primera  -> {utc1}")
print(f"    la segunda  -> {utc2}")
print(f"    diferencia  -> {utc2 - utc1}")
print("  Un log en hora local esa madrugada no se puede ordenar. En UTC no pasa:")
print("  UTC no cambia de hora nunca.")
print(f"  (y la resta entre las dos en local dice {raro.replace(fold=1) - raro.replace(fold=0)})")
