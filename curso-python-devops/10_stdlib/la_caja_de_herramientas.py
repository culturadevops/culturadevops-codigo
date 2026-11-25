# -*- coding: utf-8 -*-
"""Leccion 10 — La biblioteca estandar que de verdad usas en DevOps.

subprocess, json, datetime y logging cubren el 90% de lo que escribe alguien de sistemas.
Y subprocess trae el fallo de seguridad mas repetido del oficio: shell=True.
"""
import json
import logging
import subprocess
import sys
from datetime import datetime, timezone, timedelta


def titulo(t):
    print(f"\n{'=' * 62}\n{t}\n{'=' * 62}")


titulo("10.1 · subprocess: llamar a un comando y MIRAR el resultado")
r = subprocess.run([sys.executable, "-c", "print('hola desde otro proceso')"],
                   capture_output=True, text=True)
print(f"  returncode  {r.returncode}")
print(f"  stdout      {r.stdout.strip()!r}")
print(f"  stderr      {r.stderr.strip()!r}")

r_mal = subprocess.run([sys.executable, "-c", "import sys; sys.exit(3)"],
                       capture_output=True, text=True)
print(f"  un comando que falla -> returncode {r_mal.returncode}")
print("  ⚠ subprocess.run NO lanza excepcion si el comando falla.")
print("    O miras .returncode, o pasas check=True:")
try:
    subprocess.run([sys.executable, "-c", "import sys; sys.exit(3)"], check=True,
                   capture_output=True)
except subprocess.CalledProcessError as e:
    print(f"    con check=True -> CalledProcessError, returncode {e.returncode}")

titulo("10.2 · LA TRAMPA DE SEGURIDAD: shell=True")
print("  Esto, con un nombre que viene de fuera:")
print("      subprocess.run(f'ping {host}', shell=True)")
print("  y host = 'a.com; rm -rf /'  ejecuta LAS DOS cosas.")
print("  La forma segura es pasar una LISTA, sin shell:")
print("      subprocess.run(['ping', host])")
print("  Sin shell no hay interprete que parta por el punto y coma:")
print("  el nombre entero llega como UN argumento, aunque tenga ; o |.")

titulo("10.3 · json: leer y escribir configuracion")
datos = {"servicio": "api", "replicas": 3, "puertos": [80, 443], "activo": True}
texto = json.dumps(datos, indent=2, ensure_ascii=False)
print("  json.dumps(..., indent=2):")
for linea in texto.splitlines():
    print(f"    {linea}")
vuelta = json.loads(texto)
print(f"  json.loads() devuelve un dict: {vuelta['servicio']}, {vuelta['replicas']} replicas")
print("  ⚠ ensure_ascii=False para que los acentos salgan legibles y no como \\uXXXX")
try:
    json.loads("{esto no es json}")
except json.JSONDecodeError as e:
    print(f"  json malo -> JSONDecodeError: linea {e.lineno}, columna {e.colno}")

titulo("10.4 · datetime: siempre con zona horaria")
ahora_mal = datetime.now()
ahora_bien = datetime.now(timezone.utc)
print(f"  datetime.now()             {ahora_mal}   <- 'ingenuo', sin zona")
print(f"  datetime.now(timezone.utc) {ahora_bien}   <- consciente")
print(f"  para un log o un nombre de fichero: {ahora_bien.strftime('%Y-%m-%dT%H:%M:%SZ')}")
hace_una_hora = ahora_bien - timedelta(hours=1)
print(f"  hace una hora: {hace_una_hora.strftime('%H:%M:%S')}  (restar da un timedelta)")
print("  ⚠ Restar un datetime con zona y otro sin zona lanza TypeError.")
try:
    ahora_bien - ahora_mal
except TypeError as e:
    print(f"    {e}")

titulo("10.5 · logging: en vez de print()")
log = logging.getLogger("curso")
log.setLevel(logging.DEBUG)
h = logging.StreamHandler(sys.stdout)
h.setFormatter(logging.Formatter("    %(asctime)s %(levelname)-8s %(message)s",
                                 datefmt="%H:%M:%S"))
log.addHandler(h)
log.debug("detalle que solo quieres depurando")
log.info("arranque correcto")
log.warning("el disco va al 85%%")
log.error("no pude conectar con db-01")
print("  Ventajas sobre print(): nivel, hora, y puedes APAGAR los de abajo")
print("  sin tocar el codigo. Los errores van a stderr si usas basicConfig.")

titulo("Resumen")
print("  · subprocess.run(LISTA), nunca shell=True con datos de fuera")
print("  · run() no falla solo: mira returncode o pon check=True")
print("  · json.dumps(..., ensure_ascii=False) para acentos legibles")
print("  · datetime SIEMPRE con timezone.utc")
print("  · logging en vez de print: niveles, hora y se puede apagar")
