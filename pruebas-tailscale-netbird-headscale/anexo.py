# -*- coding: utf-8 -*-
"""Anexo del SALIDA.md (2026-10-12): las líneas del config.yaml de Headscale que deciden los DERP.
Se ejecuta aparte de correr.py y AÑADE una sección al final del SALIDA.md.    python anexo.py"""
import re
from pathlib import Path

AQUI = Path(__file__).resolve().parent
cfg = (AQUI / "headscale" / "config.yaml").read_text(encoding="utf-8").splitlines()
i = next(n for n, l in enumerate(cfg) if l.startswith("derp:"))
bloque = []
for l in cfg[i:]:
    if bloque and re.match(r"^\S", l):
        break
    bloque.append(l)
claves = [l for l in bloque if re.search(r"^derp:|^  server:|enabled:|automatically_add|^  urls:|controlplane|stun_listen", l)]
txt = "\n".join(claves)
s = (AQUI / "SALIDA.md").read_text(encoding="utf-8")
s = re.sub(r"\n## 6 · Anexo.*", "", s, flags=re.S)
s += ("\n## 6 · Anexo: dónde se decide el DERP en Headscale\n\n### config.yaml, bloque derp (por defecto)\n\n"
      "`$ grep -A… derp: config.yaml`\n\n```\n" + txt + "\n```\n")
(AQUI / "SALIDA.md").write_text(s, encoding="utf-8")
print(txt)
