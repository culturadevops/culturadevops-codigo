# -*- coding: utf-8 -*-
"""Leccion 2 — dry-run: un simulacro que no recorre el camino real no simula nada."""
import shutil
import tempfile
from pathlib import Path

base = Path(tempfile.mkdtemp())
(base / "build").mkdir()
(base / "build" / "app.txt").write_text("app v2\n", encoding="utf-8")
(base / "releases").mkdir()


# --- MAL: el dry-run se sale ANTES de calcular nada ---------------------------
def desplegar_mal(version, dry_run):
    if dry_run:
        print(f"  [dry-run] copiaria app.txt a releases/{version}")
        return
    origen = base / "biuld" / "app.txt"          # <- errata: nadie la ha ejecutado nunca
    destino = base / "releases" / version
    destino.mkdir()
    shutil.copy(origen, destino)


print("== 2.1 · LA TRAMPA: el dry-run dice que todo bien ==")
desplegar_mal("v2", dry_run=True)
print("  dry-run OK. Vamos de verdad:")
try:
    desplegar_mal("v2", dry_run=False)
except FileNotFoundError as e:
    print(f"  FileNotFoundError: {Path(e.filename).relative_to(base)}")
print("  El simulacro no paso por la linea con la errata. No simulo nada.")
print(f"  Y encima dejo esto a medias: releases/ = {sorted(p.name for p in (base / 'releases').iterdir())}"
      f", vacia: {not any((base / 'releases' / 'v2').iterdir())}")


# --- BIEN: primero un PLAN (igual en los dos modos), luego se ejecuta o se muestra
def planear(version, carpeta_build):
    origen = base / carpeta_build / "app.txt"
    destino = base / "releases" / version
    if not origen.exists():
        raise SystemExit(f"  plan invalido: no existe {origen.relative_to(base)}")
    if destino.exists():
        raise SystemExit(f"  plan invalido: releases/{version} ya existe")
    return [
        (f"crear releases/{version}", lambda: destino.mkdir()),
        (f"copiar {origen.relative_to(base)} -> releases/{version}",
         lambda: shutil.copy(origen, destino)),
    ]


def desplegar(version, carpeta_build, dry_run):
    plan = planear(version, carpeta_build)
    for descripcion, hacer in plan:
        if dry_run:
            print(f"  [dry-run] {descripcion}")
        else:
            hacer()
            print(f"  [hecho]   {descripcion}")


print()
print("== 2.2 · El plan se calcula igual con y sin dry-run ==")
try:
    desplegar("v2", "biuld", dry_run=True)
except SystemExit as e:
    print(e)
print("  Ahora la errata sale en el SIMULACRO, que es donde tiene que salir.")

print()
print("== 2.3 · Con la ruta buena: simulacro y luego de verdad ==")
try:
    desplegar("v2", "build", dry_run=True)
except SystemExit as e:
    print(e)
print("  El plan tambien caza la basura del intento fallido. La quito y repito:")
shutil.rmtree(base / "releases" / "v2")
desplegar("v2", "build", dry_run=True)
desplegar("v2", "build", dry_run=False)
print(f"  releases/: {sorted(p.name for p in (base / 'releases').iterdir())}")

shutil.rmtree(base)
