# -*- coding: utf-8 -*-
"""Leccion 8 — Marcha atras: se prepara ANTES de desplegar, no cuando ya fallo."""
import os
import shutil
import sqlite3
import tempfile
import time
from pathlib import Path

base = Path(tempfile.mkdtemp())

print("== 8.1 · LA TRAMPA: desplegar encima ==")
app = base / "app"
app.mkdir()
(app / "codigo.txt").write_text("v1\n", encoding="utf-8")
(app / "codigo.txt").write_text("v2 (rota)\n", encoding="utf-8")   # se copia encima
print(f"  la v2 falla. Volver a la v1... app/codigo.txt = {(app / 'codigo.txt').read_text().strip()!r}")
print("  La v1 ya no existe en ningun sitio. Volver atras = volver a construirla.")

print()
print("== 8.2 · Una carpeta por release y un puntero a la actual ==")
releases = base / "releases"
for v in ("v1", "v2", "v3"):
    (releases / v).mkdir(parents=True)
    (releases / v / "codigo.txt").write_text(f"{v}\n", encoding="utf-8")


def apuntar(version):
    """Cambia la actual de golpe (en Linux: ln -sfn releases/v3 actual)."""
    tmp = base / "ACTUAL.tmp"
    tmp.write_text(version, encoding="utf-8")
    os.replace(tmp, base / "ACTUAL")


def actual():
    return (base / "ACTUAL").read_text(encoding="utf-8")


apuntar("v3")
print(f"  releases/ = {sorted(p.name for p in releases.iterdir())}   ACTUAL -> {actual()}")
t0 = time.perf_counter()
apuntar("v2")
print(f"  la v3 falla -> marcha atras: ACTUAL -> {actual()} "
      f"en {(time.perf_counter() - t0) * 1000:.2f} ms")


def limpiar(conservar):
    todas = sorted(p.name for p in releases.iterdir())
    for v in todas[:-conservar]:
        if v != actual():
            shutil.rmtree(releases / v)
    return sorted(p.name for p in releases.iterdir())


print()
print("== 8.3 · LA TRAMPA 2: limpiar de mas ==")
print(f"  conservar 1: queda {limpiar(1)} (ACTUAL -> {actual()})")
print("  Si la v2 tambien falla, ya no hay a donde volver. Conserva 3 o mas.")

print()
print("== 8.4 · LA TRAMPA 3: el codigo vuelve atras. La base de datos, no ==")
db = sqlite3.connect(":memory:")
db.execute("CREATE TABLE servidores (nombre TEXT, ip TEXT)")
db.execute("INSERT INTO servidores VALUES ('web-01', '10.0.0.5')")
consulta_v1 = "SELECT nombre, ip FROM servidores"

db.execute("ALTER TABLE servidores RENAME COLUMN ip TO direccion")   # migracion de la v2
print("  la v2 renombro la columna ip -> direccion. Falla. Marcha atras al codigo v1:")
try:
    db.execute(consulta_v1).fetchall()
except sqlite3.OperationalError as e:
    print(f"  la v1 contra la base nueva: OperationalError: {e}")

db.execute("ALTER TABLE servidores RENAME COLUMN direccion TO ip")
db.execute("ALTER TABLE servidores ADD COLUMN direccion TEXT")      # ampliar, no romper
db.execute("UPDATE servidores SET direccion = ip")
print("  Haciendolo en dos pasos (primero AGREGAR la columna, borrar la vieja en otra release):")
print(f"  la v1 contra la base nueva: {db.execute(consulta_v1).fetchall()}")

shutil.rmtree(base)
