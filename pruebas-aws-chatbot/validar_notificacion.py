# -*- coding: utf-8 -*-
"""Valida una notificación personalizada de AWS Chatbot (Amazon Q Developer in chat applications)
contra las reglas de la documentación oficial:
https://docs.aws.amazon.com/chatbot/latest/adminguide/custom-notifs.html

    python validar_notificacion.py archivo.json
"""
import json
import sys

LIMITES = {"title": 250, "description": 8000}
LIMITE_PASO, LIMITE_ETIQUETA = 350, 75


def validar(n):
    errores = []
    if n.get("version") != "1.0":
        errores.append('version debe ser "1.0"')
    if n.get("source") != "custom":
        errores.append('source debe ser "custom"')
    c = n.get("content")
    if not isinstance(c, dict) or not c.get("description"):
        errores.append("content.description es obligatorio")
        c = c if isinstance(c, dict) else {}
    if c.get("textType", "client-markdown") != "client-markdown":
        errores.append('textType solo admite "client-markdown"')
    for campo, tope in LIMITES.items():
        if len(c.get(campo, "")) > tope:
            errores.append(f"{campo}: {len(c[campo])} caracteres (máximo {tope})")
    for i, paso in enumerate(c.get("nextSteps", [])):
        if len(paso) > LIMITE_PASO:
            errores.append(f"nextSteps[{i}]: {len(paso)} caracteres (máximo {LIMITE_PASO})")
    for i, k in enumerate(c.get("keywords", [])):
        if len(k) > LIMITE_ETIQUETA:
            errores.append(f"keywords[{i}]: {len(k)} caracteres (máximo {LIMITE_ETIQUETA})")
    return errores


if __name__ == "__main__":
    for ruta in sys.argv[1:]:
        with open(ruta, encoding="utf-8") as f:
            errores = validar(json.load(f))
        print(f"{ruta}: " + ("OK" if not errores else "RECHAZADA"))
        for e in errores:
            print(f"  - {e}")
