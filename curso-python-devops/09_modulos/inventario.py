# -*- coding: utf-8 -*-
"""Leccion 9 — Modulo de ejemplo. Este fichero esta pensado para ser IMPORTADO."""

VERSION = "1.0"

_HOSTS = [
    {"nombre": "web-01", "estado": "activo", "cpu": 0.91},
    {"nombre": "web-02", "estado": "parado", "cpu": 0.00},
    {"nombre": "db-01", "estado": "activo", "cpu": 0.42},
]


def todos():
    return list(_HOSTS)


def activos():
    return [h for h in _HOSTS if h["estado"] == "activo"]


def saturados(umbral=0.8):
    return [h for h in _HOSTS if h["cpu"] > umbral]


# ⚠ Esto se ejecuta SOLO si corres este fichero directamente.
# Si lo importas, no corre. Es la diferencia entre una biblioteca y un script.
if __name__ == "__main__":
    print(f"inventario {VERSION}: {len(todos())} hosts, {len(activos())} activos")
