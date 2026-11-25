# -*- coding: utf-8 -*-
"""Mide un Dockerfile: hadolint, `latest`, si construye, tamaño, si corre como root y si arranca y responde «ok».
Reanudable: guarda el resultado al lado del Dockerfile (<nombre>.medida.json) y no repite lo ya medido.

  python medir.py referencia          # las 20 referencias escritas a mano (prueba del banco)
"""
import json
import os
import sys

import banco
from crear_apps import APPS


def medir(app, dockerfile, tag):
    salida = dockerfile + ".medida.json"
    if os.path.exists(salida):
        with open(salida, encoding="utf-8") as f:
            return json.load(f)
    m = {"app": app, "dockerfile": os.path.relpath(dockerfile, banco.AQUI).replace("\\", "/")}
    m["hadolint"] = banco.hadolint(dockerfile)
    bases = banco.imagenes_base(dockerfile)
    m["bases"] = [b for b, _ in bases]
    m["latest"] = any(l for _, l in bases)
    ok, seg, err = banco.construir(app, dockerfile, tag)
    m.update(construye=ok, segundos_build=seg, error_build=err)
    if ok:
        m.update(banco.inspeccionar(tag))
        m["arranca"], m["error_arranque"] = banco.arranca(tag)
        banco.borrar_imagen(tag)
    with open(salida, "w", encoding="utf-8") as f:
        json.dump(m, f, ensure_ascii=False, indent=1)
    return m


if __name__ == "__main__":
    banco.preparar()
    if sys.argv[1] == "referencia":
        for app in APPS:
            m = medir(app, os.path.join(banco.AQUI, "referencia", f"{app}.Dockerfile"), f"v711-ref-{app}")
            print(app, len(m["hadolint"]), m["construye"], round(m.get("bytes", 0) / 1e6), "MB root" if m.get("root") else "MB",
                  m.get("arranca"), m["error_build"][:200], m.get("error_arranque", "")[:200], flush=True)
