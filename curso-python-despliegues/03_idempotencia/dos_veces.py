# -*- coding: utf-8 -*-
"""Leccion 3 — Idempotencia: el despliegue se va a ejecutar dos veces. Siempre."""
import shutil
import tempfile
from pathlib import Path

base = Path(tempfile.mkdtemp())
conf = base / "app.conf"
conf.write_text("puerto=8080\n", encoding="utf-8")

print("== 3.1 · LA TRAMPA: anadir una linea ==")


def activar_cache_mal():
    with conf.open("a", encoding="utf-8") as f:
        f.write("cache=on\n")


activar_cache_mal()
activar_cache_mal()      # el pipeline reintento el paso
print(f"  tras 2 ejecuciones, 'cache=on' aparece {conf.read_text().count('cache=on')} veces:")
for linea in conf.read_text(encoding="utf-8").splitlines():
    print(f"    {linea}")

print()
print("== 3.2 · Idempotente: 'que quede asi', no 'haz esto' ==")
conf.write_text("puerto=8080\n", encoding="utf-8")


def asegurar_linea(ruta, clave, valor):
    """Deja clave=valor en el archivo. Devuelve True si tuvo que cambiar algo."""
    lineas = ruta.read_text(encoding="utf-8").splitlines()
    nueva = f"{clave}={valor}"
    if nueva in lineas:
        return False
    lineas = [l for l in lineas if not l.startswith(clave + "=")] + [nueva]
    ruta.write_text("\n".join(lineas) + "\n", encoding="utf-8")
    return True


for vez in (1, 2, 3):
    cambio = asegurar_linea(conf, "cache", "on")
    print(f"  ejecucion {vez}: {'cambiado' if cambio else 'sin cambios'}")
print(f"  'cache=on' aparece {conf.read_text().count('cache=on')} vez")
cambio = asegurar_linea(conf, "cache", "off")
print(f"  y si piden cache=off: {'cambiado' if cambio else 'sin cambios'} -> "
      f"{conf.read_text(encoding='utf-8').splitlines()}")
print("  Decir 'cambiado / sin cambios' es lo que hace Ansible. Y es lo que te deja")
print("  saber si el segundo despliegue toco algo.")

print()
print("== 3.3 · La otra cara: crear lo que ya existe ==")
(base / "logs").mkdir()
try:
    (base / "logs").mkdir()
except FileExistsError:
    print("  mkdir() la segunda vez -> FileExistsError: el reintento revienta")
(base / "logs").mkdir(parents=True, exist_ok=True)
print("  mkdir(exist_ok=True) la segunda vez -> nada. Idempotente.")

shutil.rmtree(base)
