# -*- coding: utf-8 -*-
"""Pasa cada fuentes/*.html (descargadas con curl, fecha en FUENTES.md) a fuentes/*.txt para citar literal.
Uso: python -I fuentes_a_texto.py   ·   buscar: python -I fuentes_a_texto.py buscar <archivo.txt> <regex>"""
import html
import re
import sys
from pathlib import Path

F = Path(__file__).resolve().parent / "fuentes"
sys.stdout.reconfigure(encoding="utf-8")


def texto(h):
    h = re.sub(r"(?is)<(script|style|noscript|svg)[^>]*>.*?</\1>", " ", h)
    h = re.sub(r"(?i)<br\s*/?>|</(p|div|li|h\d|tr|td|th|section|article)>", "\n", h)
    t = html.unescape(re.sub(r"<[^>]+>", " ", h))
    t = re.sub(r"[ \t ]+", " ", t)
    return "\n".join(l.strip() for l in t.splitlines() if l.strip())


if len(sys.argv) > 3 and sys.argv[1] == "buscar":
    t = (F / sys.argv[2]).read_text(encoding="utf-8")
    for m in re.finditer(sys.argv[3], t, re.I):
        print("…", t[max(0, m.start() - 250):m.end() + 250].replace("\n", " "), "…\n")
else:
    for p in sorted(F.glob("*.html")):
        p.with_suffix(".txt").write_text(texto(p.read_text(encoding="utf-8", errors="replace")), encoding="utf-8")
        print(p.name)
