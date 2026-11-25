# -*- coding: utf-8 -*-
"""Genera el log de la noche del incidente. Siempre el mismo: la semilla esta fija.

    from comun.registro import generar, INCIDENTE
    ruta = generar(carpeta / "app.log", minutos=60)

El incidente: a las 03:12 UTC la base de datos empieza a agotar su pool de conexiones.
Durante 4 minutos casi todo falla, y la latencia se dispara.
"""
import gzip
import random
from datetime import datetime, timedelta, timezone

INICIO = datetime(2026, 9, 22, 2, 30, tzinfo=timezone.utc)
INCIDENTE = datetime(2026, 9, 22, 3, 12, tzinfo=timezone.utc)
FIN_INCIDENTE = INCIDENTE + timedelta(minutes=4)

RUTAS = ["/api/pedidos", "/api/pedidos/{id}", "/api/usuarios/{id}", "/salud", "/api/carrito"]
SERVICIOS = ["web-01", "web-02", "web-03"]


def _lineas(minutos, semilla):
    az = random.Random(semilla)
    t = INICIO
    fin = INICIO + timedelta(minutes=minutos)
    n = 0
    while t < fin:
        n += 1
        dentro = INCIDENTE <= t < FIN_INCIDENTE
        srv = az.choice(SERVICIOS)
        ruta = az.choice(RUTAS)
        pid = f"req-{n:06d}"
        if dentro and az.random() < 0.72:
            ms = az.randint(1800, 4200)
            yield (t, "ERROR", srv, pid,
                   f'{ruta} 500 {ms}ms error="no se pudo obtener conexion del pool '
                   f'(esperando 5000ms) id={pid}"')
        elif az.random() < 0.012:
            ms = az.randint(200, 900)
            yield (t, "WARNING", srv, pid, f"{ruta} 404 {ms}ms")
        elif not dentro and az.random() < 0.015:
            ms = az.randint(900, 3000)          # consulta lenta: la cola de siempre
            yield (t, "INFO", srv, pid, f"{ruta} 200 {ms}ms")
        else:
            ms = az.randint(40, 260) if not dentro else az.randint(300, 1500)
            yield (t, "INFO", srv, pid, f"{ruta} 200 {ms}ms")
        t += timedelta(milliseconds=az.randint(60, 240) if not dentro else az.randint(20, 90))


def formatear(fila):
    t, nivel, srv, pid, resto = fila
    return f"{t.strftime('%Y-%m-%dT%H:%M:%S.%f')[:-3]}Z {nivel:<7} {srv} {pid} {resto}"


def generar(ruta, minutos=60, semilla=20260922, comprimido=False):
    lineas = (formatear(f) + "\n" for f in _lineas(minutos, semilla))
    abrir = gzip.open if comprimido else open
    with abrir(ruta, "wt", encoding="utf-8") as f:
        f.writelines(lineas)
    return ruta


def cuantas(ruta):
    with open(ruta, encoding="utf-8") as f:
        return sum(1 for _ in f)
