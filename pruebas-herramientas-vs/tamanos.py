# -*- coding: utf-8 -*-
"""tamanos.py — los dos tamaños de cada imagen oficial de la serie (no cronometra: no necesita el candado).

`docker image inspect .Size` (lo que sale en las SALIDA.md) es lo que se DESCARGA, comprimido. `docker images` da lo que ocupa
ya desempaquetada en el disco. Las SALIDA dicen «tamaño en disco» para el primero: el bueno es este archivo.

    python tamanos.py   → TAMANOS.md
"""
import subprocess
from datetime import datetime
from pathlib import Path

IMGS = ["nginx:1.30.6-alpine", "caddy:2.11.8-alpine", "traefik:v3.7.17", "haproxy:3.4.7-alpine",
        "postgres:18.6", "mysql:9.7.4", "redis:8.8.4", "valkey/valkey:9.1.3"]


def sh(a):
    return subprocess.run(a, capture_output=True, text=True, encoding="utf-8").stdout.strip()


filas = [f"# Tamaño de las imágenes oficiales ({datetime.now():%Y-%m-%d %H:%M})\n",
         "| imagen | descarga (comprimida, `docker image inspect .Size`) | en disco (`docker images`) |", "|---|---|---|"]
for i in IMGS:
    comp = int(sh(["docker", "image", "inspect", "-f", "{{.Size}}", i])) / 1048576
    disco = sh(["docker", "images", i, "--format", "{{.Size}}"])
    filas.append(f"| `{i}` | " + f"{comp:.1f}".replace(".", ",") + f" MiB | {disco} |")
Path(__file__).with_name("TAMANOS.md").write_text("\n".join(filas) + "\n", encoding="utf-8")
print("\n".join(filas))
