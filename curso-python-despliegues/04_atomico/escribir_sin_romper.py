# -*- coding: utf-8 -*-
"""Leccion 4 — Escritura atomica: o el archivo viejo, o el nuevo. Nunca la mitad."""
import json
import os
import shutil
import tempfile
from pathlib import Path

base = Path(tempfile.mkdtemp())
conf = base / "config.json"
vieja = {"version": "v1", "replicas": 3, "puerto": 8080}
nueva = {"version": "v2", "replicas": 5, "puerto": 8080, "cache": True}
conf.write_text(json.dumps(vieja), encoding="utf-8")


class Corte(Exception):
    """Simula que el proceso muere a mitad (OOM, reinicio, Ctrl+C)."""


def escribir_mal(ruta, datos):
    texto = json.dumps(datos)
    with open(ruta, "w", encoding="utf-8") as f:      # "w" VACIA el archivo aqui
        f.write(texto[: len(texto) // 2])
        raise Corte()


print("== 4.1 · LA TRAMPA: escribir encima ==")
try:
    escribir_mal(conf, nueva)
except Corte:
    print("  el proceso murio a mitad de escribir")
print(f"  config.json ahora: {conf.read_text(encoding='utf-8')!r}")
try:
    json.loads(conf.read_text(encoding="utf-8"))
except json.JSONDecodeError as e:
    print(f"  la app al arrancar: JSONDecodeError: {e.msg}")
print("  Ya no tienes ni la version vieja ni la nueva.")


def escribir_atomico(ruta, datos, cortar=False):
    ruta = Path(ruta)
    tmp = ruta.with_name(ruta.name + ".tmp")          # MISMA carpeta = mismo disco
    with open(tmp, "w", encoding="utf-8") as f:
        texto = json.dumps(datos)
        if cortar:
            f.write(texto[: len(texto) // 2])
            raise Corte()
        f.write(texto)
        f.flush()
        os.fsync(f.fileno())                           # que llegue al disco
    os.replace(tmp, ruta)                              # el cambio es de golpe


print()
print("== 4.2 · Atomico: temporal al lado y os.replace ==")
conf.write_text(json.dumps(vieja), encoding="utf-8")
try:
    escribir_atomico(conf, nueva, cortar=True)
except Corte:
    print("  el proceso murio a mitad de escribir... el TEMPORAL")
print(f"  config.json sigue: {json.loads(conf.read_text(encoding='utf-8'))}")
escribir_atomico(conf, nueva)
print(f"  sin corte:         {json.loads(conf.read_text(encoding='utf-8'))}")
print(f"  .tmp que quedan: {sorted(p.name for p in base.glob('*.tmp'))}")
print("  (el del corte lo piso la escritura buena; si nadie vuelve a escribir,")
print("   queda ahi: limpialo al arrancar)")
print("  os.replace es atomico dentro del MISMO sistema de archivos.")
print("  Por eso el temporal va al lado, no en /tmp.")

shutil.rmtree(base)
