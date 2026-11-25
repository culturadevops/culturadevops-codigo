# -*- coding: utf-8 -*-
"""Puntúa los hallazgos de cualquier escáner contra la verdad de referencia de app/ (ver LEEME.md).

Cada archivo de app/ marca sus casos con un comentario «V1:», «V2:», «V3:», «S1:» o «S2:». Un hallazgo cae en el caso cuyo
marcador es el último que aparece antes de su línea, dentro del mismo archivo. Después se mira de qué TIPO es:
  · SQL (inyección SQL) cuenta para V1, V3 (aciertos) y para S1, S2 (falsos positivos);
  · CMD (inyección de comandos) cuenta para V2.
Lo demás —XSS, cabeceras, límites de peticiones, imports, recursos sin cerrar— va a «otros avisos»: no se esconde, se cuenta aparte.
"""
import re
from pathlib import Path

APP = Path(__file__).parent / "app"
LENGUAJES = ["php", "python", "go", "java", "node"]
ESPERADO = {"V1": "SQL", "V2": "CMD", "V3": "SQL", "S1": "SQL", "S2": "SQL"}
# Reglas cuyo texto no dice «comando» pero que señalan la línea que ejecuta el comando.
# java:S4036 (SonarQube): «buscar comandos en el PATH es sensible»; salta en Runtime.exec, la línea de V2.
REGLA_A_TIPO = {"java:S4036": "CMD"}
_SQL = re.compile(r"sql|query|cwe-89", re.I)
_CMD = re.compile(r"command|exec|shell|subprocess|child.?process|cwe-78", re.I)


def tipo(regla, texto=""):
    if regla in REGLA_A_TIPO:
        return REGLA_A_TIPO[regla]
    t = f"{regla} {texto}"
    if _SQL.search(t):
        return "SQL"
    if _CMD.search(t):
        return "CMD"
    return "OTRO"


def _lenguaje(ruta):
    partes = Path(str(ruta).replace("\\", "/")).parts
    for p in partes:
        if p in LENGUAJES:
            return p
    return None


def _marcadores(lenguaje, nombre):
    archivo = next(APP.joinpath(lenguaje).rglob(nombre), None)
    if archivo is None:
        return []
    marcas = []
    for i, linea in enumerate(archivo.read_text(encoding="utf-8").splitlines(), 1):
        m = re.search(r"(?://|#)\s*(V1|V2|V3|S1|S2):", linea)
        if m:
            marcas.append((i, m.group(1)))
    return marcas


def caso(ruta, linea):
    lang = _lenguaje(ruta)
    if lang is None:
        return None, None
    marcas = _marcadores(lang, Path(str(ruta).replace("\\", "/")).name)
    actual = None
    for n, c in marcas:
        if n <= linea:
            actual = c
    return lang, actual


def puntuar(hallazgos, lenguajes=None):
    """hallazgos: lista de (ruta, línea, regla, texto). Devuelve {lenguaje: {"V1": bool, ..., "fp": [...], "otros": n}}."""
    lenguajes = lenguajes or LENGUAJES
    res = {l: {"V1": False, "V2": False, "V3": False, "fp": set(), "otros": 0, "total": 0} for l in lenguajes}
    for ruta, linea, regla, texto in hallazgos:
        lang, c = caso(ruta, int(linea or 0))
        if lang not in res:
            continue
        res[lang]["total"] += 1
        t = tipo(regla, texto)
        if c and t == ESPERADO[c]:
            if c.startswith("V"):
                res[lang][c] = True
            else:
                res[lang]["fp"].add(c)
        else:
            res[lang]["otros"] += 1
    return res


def fila(r):
    v = "".join("✔" if r[c] else "✘" for c in ("V1", "V2", "V3"))
    fp = ",".join(sorted(r["fp"])) or "—"
    return f"{v} · aciertos {sum(r[c] for c in ('V1', 'V2', 'V3'))}/3 · falsos positivos: {fp} · otros avisos: {r['otros']}"
