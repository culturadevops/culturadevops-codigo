# -*- coding: utf-8 -*-
"""Leccion 10 — Configuracion y secretos: lo que falta tiene que gritar, lo secreto callarse."""
import os
import shlex
from dataclasses import dataclass, field
from pathlib import PurePosixPath

for v in ("ENTORNO", "DESTINO", "TOKEN_REGISTRO"):
    os.environ.pop(v, None)
os.environ["ENTORNO"] = "produccion"

print("== 10.1 · LA TRAMPA: get() con un valor por omision vacio ==")
destino = os.environ.get("DESTINO", "")
ruta = PurePosixPath("/srv") / destino / "app"
print(f"  DESTINO no esta definida -> ruta = {ruta}")
print("  El despliegue no falla: copia en /srv/app, que es de OTRA aplicacion.")
print("  (y si esa ruta acaba en un borrado, borra lo que no era)")

print()
print("== 10.2 · Lo obligatorio se pide, y se piden TODOS de una vez ==")


def requerir(*nombres):
    faltan = [n for n in nombres if not os.environ.get(n)]
    if faltan:
        raise SystemExit(f"  faltan variables: {', '.join(faltan)}. No despliego nada.")
    return [os.environ[n] for n in nombres]


try:
    requerir("ENTORNO", "DESTINO", "TOKEN_REGISTRO")
except SystemExit as e:
    print(e)
print("  Una por una, arreglarias DESTINO, lanzarias, y fallaria por TOKEN_REGISTRO.")

os.environ["DESTINO"] = "tienda"
os.environ["TOKEN_REGISTRO"] = "ghp_R3aLm3nt3S3cr3t0"
entorno, destino, token = requerir("ENTORNO", "DESTINO", "TOKEN_REGISTRO")

print()
print("== 10.3 · LA TRAMPA 2: el secreto se escapa en el log ==")
comando = ["docker", "login", "registro.interno", "--username", "ci", "--password", token]
print(f"  log: ejecutando {shlex.join(comando)}")

OCULTAR = ("--password", "--token")


def para_el_log(cmd):
    limpio, tapar = [], False
    for parte in cmd:
        limpio.append("***" if tapar else parte)
        tapar = parte in OCULTAR
    return shlex.join(limpio)


print(f"  log: ejecutando {para_el_log(comando)}")
print("  Mejor aun: que el secreto no vaya en la linea de comandos (se ve en ps).")
print("  docker login lo acepta por la entrada estandar: --password-stdin.")

print()
print("== 10.4 · LA TRAMPA 3: imprimir el objeto de configuracion ==")


@dataclass
class ConfigMal:
    entorno: str
    token: str


@dataclass
class Config:
    entorno: str
    token: str = field(repr=False)


print(f"  print(config) -> {ConfigMal(entorno, token)}")
print(f"  con repr=False -> {Config(entorno, token)}")
print("  Un print() de depuracion olvidado acaba en el log del pipeline, que lee todo el equipo.")
