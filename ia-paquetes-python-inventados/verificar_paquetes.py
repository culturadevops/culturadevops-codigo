# -*- coding: utf-8 -*-
"""Defensa: antes de instalar, comprueba que cada paquete de un requirements exista en PyPI y tenga historial.
Solo lee la API pública de PyPI; no descarga ni instala nada. Sale con 1 si algo no pasa.

  python verificar_paquetes.py requirements.txt [--dias 90]
"""
import datetime
import json
import re
import sys
import urllib.error
import urllib.request


def info(nombre):
    url = f"https://pypi.org/pypi/{re.sub(r'[-_.]+', '-', nombre).lower()}/json"
    try:
        with urllib.request.urlopen(urllib.request.Request(url, headers={"User-Agent": "verificar-paquetes"}), timeout=30) as r:
            d = json.load(r)
    except urllib.error.HTTPError as e:
        if e.code == 404:
            return None
        raise
    fechas = sorted(f["upload_time"] for v in d["releases"].values() for f in v)
    return {"versiones": len(d["releases"]), "primera": fechas[0][:10] if fechas else None}


def main():
    dias = int(sys.argv[sys.argv.index("--dias") + 1]) if "--dias" in sys.argv else 90
    hoy = datetime.date.today()
    malos = 0
    for linea in open(sys.argv[1], encoding="utf-8"):
        linea = linea.split("#")[0].strip()
        if not linea or linea.startswith("-"):
            continue
        nombre = re.split(r"[\[<>=!~; ]", linea)[0]
        i = info(nombre)
        if i is None:
            print(f"NO EXISTE   {nombre}")
            malos += 1
        elif not i["primera"] or (hoy - datetime.date.fromisoformat(i["primera"])).days < dias:
            print(f"DEMASIADO NUEVO  {nombre}  (primera versión {i['primera']}, {i['versiones']} versiones)")
            malos += 1
        else:
            print(f"ok          {nombre}  (desde {i['primera']}, {i['versiones']} versiones)")
    sys.exit(1 if malos else 0)


if __name__ == "__main__":
    main()
