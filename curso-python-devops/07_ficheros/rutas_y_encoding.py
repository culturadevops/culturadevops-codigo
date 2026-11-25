# -*- coding: utf-8 -*-
"""Leccion 7 — Ficheros con pathlib, y la codificacion que te rompe SOLO en Windows.

open() sin encoding usa la codificacion POR OMISION del sistema. En Linux suele ser UTF-8 y
en Windows no. Por eso el script que funciona en tu portatil revienta en el otro, con los
mismos datos.
"""
import tempfile
import locale
from pathlib import Path


def titulo(t):
    print(f"\n{'=' * 62}\n{t}\n{'=' * 62}")


titulo("7.1 · pathlib: rutas que funcionan en los dos sistemas")
p = Path("etc") / "nginx" / "sitios.conf"
print(f"  ruta      {p}")
print(f"  .name     {p.name}")
print(f"  .stem     {p.stem}")
print(f"  .suffix   {p.suffix}")
print(f"  .parent   {p.parent}")
print(f"  .parts    {p.parts}")
print("  La barra correcta la pone pathlib, no tu.")

titulo("7.2 · Preguntar antes de tocar")
tmp = Path(tempfile.mkdtemp(prefix="curso_py_"))
fichero = tmp / "servicios.txt"
print(f"  directorio de pruebas: {tmp}")
print(f"  fichero.exists()  antes -> {fichero.exists()}")
fichero.write_text("web-01 activo\nweb-02 parado\n", encoding="utf-8")
print(f"  fichero.exists()  ahora -> {fichero.exists()}")
print(f"  fichero.stat().st_size  -> {fichero.stat().st_size} bytes")

titulo("7.3 · Leer: entero, o linea a linea")
print("  read_text() entero (bien para ficheros pequenos):")
for linea in fichero.read_text(encoding="utf-8").splitlines():
    print(f"    {linea}")
print("  con `with open(...)` linea a linea (bien para un log de 2 GB):")
with open(fichero, encoding="utf-8") as fh:
    for n, linea in enumerate(fh, 1):
        print(f"    {n}: {linea.rstrip()}")
print("  La diferencia importa: read_text() carga TODO en memoria.")

titulo("7.4 · LA TRAMPA: open() sin encoding")
print(f"  codificacion por omision de este sistema: {locale.getpreferredencoding(False)}")
acentos = tmp / "acentos.txt"
acentos.write_text("configuración añadida\n", encoding="utf-8")
print("  escrito en UTF-8: 'configuración añadida'")
try:
    leido = acentos.read_text(encoding="latin-1")
    print(f"  leido como latin-1: {leido.strip()!r}   <- NO reventó, pero esta MAL")
except UnicodeDecodeError as e:
    print(f"  leido como latin-1: UnicodeDecodeError {e}")
try:
    acentos.read_text(encoding="ascii")
except UnicodeDecodeError as e:
    print(f"  leido como ascii:   UnicodeDecodeError")
    print(f"    {str(e)[:78]}")
print("  Regla: encoding='utf-8' SIEMPRE, al leer y al escribir.")

titulo("7.5 · Recorrer un directorio")
(tmp / "sub").mkdir()
(tmp / "sub" / "otro.conf").write_text("x", encoding="utf-8")
print("  .iterdir()  (solo el primer nivel):")
for h in sorted(tmp.iterdir()):
    print(f"    {'[dir] ' if h.is_dir() else '      '}{h.name}")
print("  .rglob('*.conf')  (recursivo, por patron):")
for h in sorted(tmp.rglob("*.conf")):
    print(f"    {h.relative_to(tmp)}")

titulo("7.6 · Escribir sin dejar el fichero a medias")
destino = tmp / "estado.json"
temporal = destino.with_suffix(".json.tmp")
temporal.write_text('{"estado": "ok"}', encoding="utf-8")
temporal.replace(destino)          # replace es ATOMICO
print(f"  se escribe en {temporal.name} y se renombra a {destino.name}")
print(f"  contenido: {destino.read_text(encoding='utf-8')}")
print("  Si el proceso muere a mitad, el fichero bueno sigue intacto.")
print("  Es lo que hacen por dentro las herramientas serias.")

import shutil
shutil.rmtree(tmp)
print(f"\n  (limpiado {tmp})")

titulo("Resumen")
print("  · pathlib para todo: rutas, existencia, tamano, recorrer")
print("  · encoding='utf-8' explicito SIEMPRE")
print("  · read_text() carga entero; `with open()` va linea a linea")
print("  · escribir a .tmp y .replace() es escritura atomica")
