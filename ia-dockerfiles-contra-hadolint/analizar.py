# -*- coding: utf-8 -*-
"""Mide la ronda 0 y la última ronda de cada Dockerfile de muestras/ (construye, tamaño, root, latest, arranca) y escribe
resultados.json. Las rondas intermedias solo pasan por hadolint. Criterio fijado antes de mirar resultados. No llama a ninguna IA."""
import json
import os
import re
import sys

import banco
from crear_apps import APPS
from medir import medir

AQUI = banco.AQUI
SUPR = re.compile(r"hadolint\s+ignore", re.I)


def main(quienes):
    banco.preparar()
    res = {}
    for quien in quienes:
        for app in APPS:
            d = os.path.join(AQUI, "muestras", quien, app)
            k = 0
            rondas = []
            while os.path.exists(os.path.join(d, f"r{k}.Dockerfile")):
                with open(os.path.join(d, f"r{k}.Dockerfile"), encoding="utf-8") as f:
                    txt = f.read()
                with open(os.path.join(d, f"r{k}.hadolint.json"), encoding="utf-8") as f:
                    h = json.load(f)
                rondas.append({"k": k, "hadolint": h, "supr": len(SUPR.findall(txt))})
                k += 1
            if not rondas:
                continue
            for r in {0, len(rondas) - 1}:
                m = medir(app, os.path.join(d, f"r{r}.Dockerfile"), f"v711-{quien}-{app}-r{r}")
                rondas[r]["medida"] = m
                print(quien, app, f"r{r}", len(m["hadolint"]), m["construye"], m.get("disco_mb"), m.get("root"),
                      m["latest"], m.get("arranca"), flush=True)
            res.setdefault(quien, {})[app] = rondas
    with open(os.path.join(AQUI, "resultados.json"), "w", encoding="utf-8") as f:
        json.dump(res, f, ensure_ascii=False, indent=1)


if __name__ == "__main__":
    main(sys.argv[1:] or ["claude", "qwen"])
