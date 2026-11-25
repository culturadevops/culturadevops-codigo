# -*- coding: utf-8 -*-
"""desplegar.py — el curso entero en un script de verdad.

    python desplegar.py --version v2 --origen build/v2 --base /srv/tienda \\
                        --url http://127.0.0.1:8080/salud [--dry-run]

Codigos de salida:
    0   desplegada (o ya lo estaba: sin cambios)
    1   fallo, y se volvio a la version anterior
    2   llamada mal (argparse)
    3   fallo, y NO se pudo volver atras: hay que mirar a mano
    75  ya hay otro despliegue en curso
"""
import argparse
import json
import logging
import os
import shutil
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

log = logging.getLogger("desplegar")


class Ocupado(Exception):
    pass


# --- cerrojo (leccion 9) ---------------------------------------------------------
def tomar_cerrojo(ruta, caduca=30 * 60):
    try:
        fd = os.open(ruta, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
    except FileExistsError:
        edad = time.time() - ruta.stat().st_mtime
        if edad < caduca:
            raise Ocupado(f"hay otro despliegue en curso desde hace {edad:.0f} s ({ruta.name})")
        log.warning("cerrojo de hace %.0f min: lo doy por muerto", edad / 60)
        ruta.unlink()
        fd = os.open(ruta, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
    os.write(fd, json.dumps({"pid": os.getpid()}).encode())
    os.close(fd)


# --- puntero atomico (lecciones 4 y 8) --------------------------------------------
def leer_actual(base):
    try:
        return (base / "ACTUAL").read_text(encoding="utf-8").strip()
    except FileNotFoundError:
        return None


def apuntar(base, version):
    tmp = base / "ACTUAL.tmp"
    tmp.write_text(version, encoding="utf-8")
    os.replace(tmp, base / "ACTUAL")


# --- salud con plazo total (lecciones 6 y 7) ---------------------------------------
def esperar_version(url, esperada, plazo, cada=0.2):
    limite = time.monotonic() + plazo
    ultimo = None
    while time.monotonic() < limite:
        try:
            with urllib.request.urlopen(url, timeout=1) as r:
                cuerpo = json.loads(r.read())
                ultimo = f"{r.status} {cuerpo}"
                if cuerpo.get("version") == esperada:
                    return True, ultimo
        except urllib.error.HTTPError as e:
            ultimo = f"{e.code}"
        except OSError as e:
            ultimo = type(e).__name__
        time.sleep(cada)
    return False, ultimo


# --- el plan: igual con y sin --dry-run (leccion 2) ---------------------------------
def planear(a):
    origen, base = Path(a.origen), Path(a.base)
    if not (origen / "app.json").exists():
        raise SystemExit(f"plan invalido: {origen / 'app.json'} no existe")
    return origen, base, base / "releases" / a.version


def desplegar(a):
    origen, base, destino = planear(a)
    anterior = leer_actual(base)

    if anterior == a.version and destino.exists():          # idempotente (leccion 3)
        log.info("%s ya es la version actual: sin cambios", a.version)
        return 0

    pasos = []
    if not destino.exists():
        pasos.append(f"copiar {origen.name} -> releases/{a.version}")
    pasos += [f"ACTUAL: {anterior} -> {a.version}",
              f"esperar {a.version} en /salud (plazo {a.plazo:g} s)"]
    if a.dry_run:
        for p in pasos:
            print(f"[dry-run] {p}")
        return 0

    if not destino.exists():
        parcial = destino.with_name(destino.name + ".parcial")
        shutil.rmtree(parcial, ignore_errors=True)           # restos de un intento roto
        shutil.copytree(origen, parcial)
        os.replace(parcial, destino)                           # la carpeta aparece entera
        log.info("copiada releases/%s", a.version)

    apuntar(base, a.version)
    log.info("ACTUAL -> %s", a.version)
    ok, ultimo = esperar_version(a.url, a.version, a.plazo)
    if ok:
        log.info("%s contesta sana", a.version)
        limpiar(base, a.conservar, protegidas={a.version, anterior})
        return 0

    log.error("%s no contesta sana en %g s (ultimo: %s)", a.version, a.plazo, ultimo)
    if anterior is None:
        log.critical("no hay version anterior a la que volver")
        return 3
    apuntar(base, anterior)                                    # marcha atras (leccion 8)
    fallida = destino.with_name(destino.name + ".fallida")
    shutil.rmtree(fallida, ignore_errors=True)
    os.replace(destino, fallida)                               # se guarda para mirarla, no para volver
    log.info("releases/%s -> releases/%s", a.version, fallida.name)
    ok, ultimo = esperar_version(a.url, anterior, a.plazo)
    if ok:
        log.warning("marcha atras: ACTUAL -> %s, y contesta sana", anterior)
        return 1
    log.critical("marcha atras a %s y TAMPOCO contesta (ultimo: %s)", anterior, ultimo)
    return 3


def limpiar(base, conservar, protegidas):
    releases = sorted((p for p in (base / "releases").iterdir()
                       if p.is_dir() and not p.name.endswith((".parcial", ".fallida"))),
                      key=lambda p: p.stat().st_mtime)
    for p in releases[:-conservar]:
        if p.name not in protegidas:
            shutil.rmtree(p)
            log.info("limpieza: borrada releases/%s", p.name)


def main(argv=None):
    ap = argparse.ArgumentParser(prog="desplegar.py", description=__doc__.split("\n")[0])
    ap.add_argument("--version", required=True)
    ap.add_argument("--origen", required=True)
    ap.add_argument("--base", required=True)
    ap.add_argument("--url", required=True)
    ap.add_argument("--plazo", type=float, default=10)
    ap.add_argument("--conservar", type=int, default=3)
    ap.add_argument("--dry-run", action="store_true")
    a = ap.parse_args(argv)
    logging.basicConfig(level=logging.INFO, format="%(levelname)-8s %(message)s")  # a stderr (leccion 11)

    base = Path(a.base)
    if a.dry_run:                                              # el simulacro no toca nada
        return desplegar(a)
    (base / "releases").mkdir(parents=True, exist_ok=True)
    cerrojo = base / "desplegar.lock"
    try:
        tomar_cerrojo(cerrojo)
    except Ocupado as e:
        log.error("%s", e)
        return 75
    try:
        return desplegar(a)
    finally:
        cerrojo.unlink(missing_ok=True)


if __name__ == "__main__":
    sys.exit(main())
