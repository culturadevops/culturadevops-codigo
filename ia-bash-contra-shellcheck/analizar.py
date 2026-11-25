# -*- coding: utf-8 -*-
"""Ejecuta y cuenta todo lo de muestras/ y escribe resultados.json. No llama a ninguna IA."""
import collections
import glob
import json
import os
import re

import banco
from tareas import CLAUDE_IDS, T

AQUI = banco.AQUI
SUPR = re.compile(r"shellcheck\s+disable", re.I)


def rondas(quien, n):
    d = os.path.join(AQUI, "muestras", quien, f"{n:02d}")
    out = []
    k = 0
    while os.path.exists(os.path.join(d, f"r{k}.sh")):
        with open(os.path.join(d, f"r{k}.sc.json"), encoding="utf-8") as f:
            sc = json.load(f)
        with open(os.path.join(d, f"r{k}.sh"), encoding="utf-8") as f:
            txt = f.read()
        out.append({"k": k, "ruta": os.path.join(d, f"r{k}.sh"), "sc": sc, "supr": len(SUPR.findall(txt)),
                    "lineas": txt.count("\n")})
        k += 1
    return out


def main():
    res = {}
    casos = []
    for quien, ids in (("qwen", [t["id"] for t in T]), ("claude", CLAUDE_IDS), ("cruzado", [t["id"] for t in T])):
        for n in ids:
            rs = rondas(quien, n)
            if not rs:
                continue
            res.setdefault(quien, {})[n] = rs
            for r in rs:
                casos.append((f"{quien}-r{r['k']}", n, r["ruta"]))
    ej = banco.ejecutar(casos)
    for quien, por_id in res.items():
        for n, rs in por_id.items():
            for r in rs:
                e = ej[(f"{quien}-r{r['k']}", n)]
                r["control"], r["espacios"] = e["control"], e["espacios"]
                r["shfmt"] = banco.shfmt(r["ruta"])[0]
                r["ruta"] = os.path.relpath(r["ruta"], AQUI).replace("\\", "/")
    with open(os.path.join(AQUI, "resultados.json"), "w", encoding="utf-8") as f:
        json.dump(res, f, ensure_ascii=False, indent=1)
    print("ok", {q: len(v) for q, v in res.items()})


if __name__ == "__main__":
    main()
