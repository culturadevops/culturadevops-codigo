# -*- coding: utf-8 -*-
"""Ronda 0: genera los 25 main.tf con cada IA. Reanudable (salta lo ya generado).

  python generar.py qwen 1 2     # qwen2.5:7b con seed 1 y seed 2 (50 módulos)
  python generar.py claude       # Claude Code -p (25 módulos; la temperatura no se puede fijar)
"""
import json
import pathlib
import sys

from llm import bloques, claude, qwen
from peticiones import PETICIONES, PLANTILLA

AQUI = pathlib.Path(__file__).parent


def main():
    ia = sys.argv[1]
    seeds = [int(s) for s in sys.argv[2:]] or [0]
    for seed in seeds:
        lote = f"{ia}-s{seed}" if ia == "qwen" else ia
        for slug, pedido in PETICIONES:
            d = AQUI / "generado" / lote / "r0" / slug
            if (d / "respuesta.json").exists():
                continue
            prompt = PLANTILLA.format(pedido=pedido)
            r = qwen(prompt, seed) if ia == "qwen" else claude(prompt)
            r["prompt"] = prompt
            d.mkdir(parents=True, exist_ok=True)
            (d / "main.tf").write_text(bloques(r["texto"]), encoding="utf-8")
            (d / "respuesta.json").write_text(json.dumps(r, ensure_ascii=False, indent=1), encoding="utf-8")
            print(lote, slug, r.get("s"), "s", flush=True)


if __name__ == "__main__":
    main()
