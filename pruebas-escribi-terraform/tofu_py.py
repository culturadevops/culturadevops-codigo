# -*- coding: utf-8 -*-
"""tofu_py.py — un Terraform escrito en Python, para el video 218 de cultura-devops.

LA TESIS, y cabe en una resta:

        plan = deseado - actual

Eso es todo lo que hace Terraform, y lo que hace un controlador de Kubernetes. El lenguaje
propio, los proveedores, el grafo de dependencias y el bloqueo del estado son ENVOLTORIO
alrededor de esa resta.

🥇 LO QUE SE APRENDE ESCRIBIENDOLO, y que casi nadie explica:

  **SIN FICHERO DE ESTADO ESTO ES PELIGROSO.** Sin el, "lo que sobra" incluye lo que creo otra
  persona a mano. El estado es la lista de "esto lo hice yo" y es lo UNICO que te autoriza a
  borrar. En este fichero se puede correr con estado y sin el, para verlo.

El "proveedor" son ficheros en un directorio: real, desechable y repetible sin cuenta ni tarjeta.

    python tofu_py.py plan  deseado.json
    python tofu_py.py apply deseado.json
    python tofu_py.py apply deseado.json --sin-estado     # <- el modo peligroso
"""
import argparse
import json
import os
from pathlib import Path

ESTADO = Path("estado.json")


# ────────────────────────────────────────────── el "proveedor": ficheros ──
def leer_actual(dir_):
    """Lo que HAY de verdad ahi fuera. Terraform llama a esto `refresh`."""
    d = Path(dir_)
    d.mkdir(parents=True, exist_ok=True)
    return {p.name: p.read_text(encoding="utf-8") for p in sorted(d.iterdir()) if p.is_file()}


def crear(dir_, nombre, contenido):
    (Path(dir_) / nombre).write_text(contenido, encoding="utf-8")


def borrar(dir_, nombre):
    (Path(dir_) / nombre).unlink(missing_ok=True)


# ──────────────────────────────────────────────────────────── el estado ──
def leer_estado():
    """La lista de «esto lo hice yo». Lo UNICO que autoriza a borrar."""
    if ESTADO.exists():
        return json.loads(ESTADO.read_text(encoding="utf-8"))
    return {"recursos": {}}


def escribir_estado(e):
    ESTADO.write_text(json.dumps(e, indent=2, ensure_ascii=False), encoding="utf-8")


# ────────────────────────────────────────────────────────────── el plan ──
def plan(deseado, actual, estado, sin_estado=False):
    """LA RESTA. Tres listas y ya está: crear, cambiar, destruir.

    ⚠️ AQUI ESTA TODO EL VIDEO. Fijate en `destruir`:

      · CON estado  -> solo se propone borrar lo que YO cree (esta en el estado)
      · SIN estado  -> se propone borrar TODO lo que sobra, lo hiciera quien lo hiciera
    """
    crear_, cambiar, destruir = [], [], []

    for nombre, contenido in deseado.items():
        if nombre not in actual:
            crear_.append(nombre)
        elif actual[nombre] != contenido:
            cambiar.append(nombre)

    mios = set(estado["recursos"]) if not sin_estado else set(actual)
    for nombre in actual:
        if nombre not in deseado and nombre in mios:
            destruir.append(nombre)

    return {"crear": sorted(crear_), "cambiar": sorted(cambiar), "destruir": sorted(destruir)}


def pintar(p):
    for n in p["crear"]:
        print(f"  + crear     {n}")
    for n in p["cambiar"]:
        print(f"  ~ cambiar   {n}")
    for n in p["destruir"]:
        print(f"  - DESTRUIR  {n}")
    if not any(p.values()):
        print("  (sin cambios)")
    print(f"\n  Plan: {len(p['crear'])} a crear, {len(p['cambiar'])} a cambiar, "
          f"{len(p['destruir'])} a destruir.")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("orden", choices=["plan", "apply"])
    ap.add_argument("deseado")
    ap.add_argument("--dir", default="infra")
    ap.add_argument("--sin-estado", action="store_true",
                    help="⛔ el modo peligroso: sin la lista de «esto lo hice yo»")
    a = ap.parse_args()

    deseado = json.loads(Path(a.deseado).read_text(encoding="utf-8"))
    actual = leer_actual(a.dir)
    estado = leer_estado()

    p = plan(deseado, actual, estado, a.sin_estado)
    pintar(p)

    if a.orden == "plan":
        return

    for n in p["crear"] + p["cambiar"]:
        crear(a.dir, n, deseado[n])
        estado["recursos"][n] = {"gestionado": True}
    for n in p["destruir"]:
        borrar(a.dir, n)
        estado["recursos"].pop(n, None)
    escribir_estado(estado)
    print("\n  Aplicado.")


if __name__ == "__main__":
    main()
