# -*- coding: utf-8 -*-
"""Leccion 11 — Codigos de salida y logs: el pipeline solo sabe lo que tu script le dice."""
import subprocess
import sys

PY = [sys.executable, "-c"]


def correr(codigo, *args):
    return subprocess.run(PY + [codigo, *args], capture_output=True, text=True)


print("== 11.1 · LA TRAMPA: capturar el error y seguir ==")
MAL = '''
try:
    raise ConnectionError("el registro no contesta")
except Exception as e:
    print(f"ERROR: {e}")
'''
r = correr(MAL)
print(f"  salida: {r.stdout.strip()!r}")
print(f"  codigo de salida: {r.returncode}   <- para el pipeline, todo verde")

BIEN = '''
import sys
try:
    raise ConnectionError("el registro no contesta")
except ConnectionError as e:
    print(f"ERROR: {e}", file=sys.stderr)
    sys.exit(1)
'''
r = correr(BIEN)
print(f"  con sys.exit(1): codigo {r.returncode}   <- el pipeline se para aqui")

print()
print("== 11.2 · LA TRAMPA 2: los mensajes ensucian el resultado ==")
MEZCLADO = '''
print("conectando con el registro...")
print("calculando la siguiente version...")
print("v2.4.1")
'''
r = correr(MEZCLADO)
print(f"  VERSION=$(python siguiente_version.py) -> {r.stdout!r}")
LIMPIO = '''
import logging, sys
logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")   # va a stderr
logging.info("conectando con el registro...")
logging.info("calculando la siguiente version...")
print("v2.4.1")
'''
r = correr(LIMPIO)
print(f"  con logging         -> stdout {r.stdout!r}")
print(f"                         stderr {r.stderr.splitlines()}")
print("  stdout es para el RESULTADO. Lo que se cuenta, a stderr.")

print()
print("== 11.3 · Codigos que significan algo ==")
ARGS = '''
import argparse
p = argparse.ArgumentParser(prog="desplegar.py")
p.add_argument("--version", required=True)
p.parse_args()
'''
r = correr(ARGS)
print(f"  desplegar.py sin --version -> codigo {r.returncode}")
print(f"  {r.stderr.strip().splitlines()[-1]}")
print("  Convencion: 0 bien, 1 fallo, 2 lo llamaste mal. argparse ya usa el 2.")
print("  Si distingues 'fallo y volvi atras' de 'fallo y no pude volver',")
print("  el pipeline puede avisar distinto. Documentalo en el --help.")
