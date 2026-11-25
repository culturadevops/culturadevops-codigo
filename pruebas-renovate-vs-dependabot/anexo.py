# -*- coding: utf-8 -*-
"""Anexo del SALIDA.md (2026-10-12): cómo es una PR de Dependabot (de la salida de dependabot-cli de npm).
AÑADE la sección 5.    python anexo.py"""
import re
from pathlib import Path

import yaml

AQUI = Path(__file__).resolve().parent
d = yaml.safe_load((AQUI / "_dbot-npm_and_yarn.yaml").read_text(encoding="utf-8"))
pr = next(o["expect"]["data"] for o in d["output"] if o.get("type") == "create_pull_request")
txt = "pr-title: " + pr["pr-title"] + "\n\ncommit-message:\n" + pr["commit-message"].strip()
s = (AQUI / "SALIDA.md").read_text(encoding="utf-8")
s = re.sub(r"\n## 5 · Anexo.*", "", s, flags=re.S)
s += "\n## 5 · Anexo: una PR de Dependabot por dentro\n\n### la primera de npm\n\n`$ (salida de dependabot update npm_and_yarn: create_pull_request)`\n\n```\n" + txt + "\n```\n"
(AQUI / "SALIDA.md").write_text(s, encoding="utf-8")
print(txt)
