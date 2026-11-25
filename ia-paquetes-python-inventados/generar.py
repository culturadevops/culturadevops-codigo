# -*- coding: utf-8 -*-
"""Genera las respuestas del 707. Reanudable. NO instala nada: solo guarda el texto.

  python generar.py qwen 1             # los 100 prompts con qwen2.5:7b, seed 1
  python generar.py qwen 2 3 … --solo c03 n07   # repeticiones de algunos prompts con otras seeds
  python generar.py claude             # la muestra de Claude Code: 1 de cada 4 prompts (25), fijada de antemano
"""
import json
import pathlib
import sys

from llm import claude, qwen
from peticiones import PETICIONES, PLANTILLA

AQUI = pathlib.Path(__file__).parent
MUESTRA_CLAUDE = [p for i, p in enumerate(PETICIONES) if i % 4 == 0]


def main():
    args = sys.argv[1:]
    ia = args.pop(0)
    solo = None
    if "--solo" in args:
        k = args.index("--solo")
        solo, args = set(args[k + 1:]), args[:k]
    seeds = [int(s) for s in args] or [0]
    lista = MUESTRA_CLAUDE if ia == "claude" else PETICIONES
    for seed in seeds:
        lote = f"{ia}-s{seed}" if ia == "qwen" else ia
        for slug, tarea in lista:
            if solo and slug not in solo:
                continue
            f = AQUI / "respuestas" / lote / f"{slug}.json"
            if f.exists():
                continue
            prompt = PLANTILLA.format(tarea=tarea)
            r = qwen(prompt, seed) if ia == "qwen" else claude(prompt)
            r["prompt"] = prompt
            f.parent.mkdir(parents=True, exist_ok=True)
            f.write_text(json.dumps(r, ensure_ascii=False, indent=1), encoding="utf-8")
            print(lote, slug, r.get("s"), "s", flush=True)


if __name__ == "__main__":
    main()
