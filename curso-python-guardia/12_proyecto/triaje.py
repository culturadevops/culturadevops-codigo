# -*- coding: utf-8 -*-
"""triaje.py — el script que abres cuando suena el teléfono.

    python triaje.py /var/log/app.log* --desde 03:00 --hasta 03:30
    python triaje.py app.log --json          # para pegarlo en el ticket

Lee logs de texto y comprimidos, cuenta lo que descarta, agrupa los errores por PATRON,
saca los percentiles de verdad y dice en que minuto empezo. Sale con 1 si encuentra algo.
"""
import argparse
import gzip
import json
import re
import statistics
import sys
from collections import Counter
from pathlib import Path

LINEA = re.compile(
    r"^(?P<hora>\d{4}-\d{2}-\d{2}T(?P<hm>\d{2}:\d{2}):\d{2}\.\d+Z) +(?P<nivel>[A-Z]+) +"
    r"(?P<servidor>\S+) +(?P<peticion>\S+) +(?P<ruta>\S+) +(?P<codigo>\d{3}) +(?P<ms>\d+)ms"
    r"(?P<resto>.*)$")
NUMEROS = re.compile(r"\d+")
IDS = re.compile(r"\b(req-\w+|[0-9a-f]{8}-[0-9a-f-]{27})\b")


def patron(texto):
    return NUMEROS.sub("<n>", IDS.sub("<id>", texto))


def orden_de_rotacion(p):
    trozos = p.name.replace(".gz", "").split(".")
    return int(trozos[-1]) if trozos[-1].isdigit() else 0


def abrir(p):
    return gzip.open(p, "rt", encoding="utf-8", errors="replace") if p.suffix == ".gz" \
        else open(p, encoding="utf-8", errors="replace")


def lineas_de(rutas):
    for p in sorted(rutas, key=orden_de_rotacion, reverse=True):
        with abrir(p) as f:
            yield from f


def pct(ordenados, p):
    return ordenados[min(len(ordenados) - 1, int(len(ordenados) * p / 100))]


def analizar(rutas, desde, hasta):
    r = {"lineas": 0, "descartadas": 0, "muestra_descartada": None, "peticiones": 0,
         "errores": 0, "por_minuto": Counter(), "err_por_minuto": Counter(),
         "patrones": Counter(), "por_servidor": Counter(), "por_ruta": Counter(), "ms": []}
    for l in lineas_de(rutas):
        r["lineas"] += 1
        m = LINEA.match(l)
        if not m:
            r["descartadas"] += 1
            if r["muestra_descartada"] is None:
                r["muestra_descartada"] = l.strip()[:60]
            continue
        hm = m["hm"]
        if (desde and hm < desde) or (hasta and hm > hasta):
            continue
        r["peticiones"] += 1
        r["por_minuto"][hm] += 1
        r["ms"].append(int(m["ms"]))
        if m["nivel"] in ("ERROR", "CRITICAL") or m["codigo"].startswith("5"):
            r["errores"] += 1
            r["err_por_minuto"][hm] += 1
            r["patrones"][patron(m["resto"].strip() or m["ruta"])] += 1
            r["por_servidor"][m["servidor"]] += 1
            r["por_ruta"][m["ruta"]] += 1
    return r


def informe(r, umbral):
    if not r["peticiones"]:
        print("no hay ninguna peticion en esa ventana", file=sys.stderr)
        return {}, 2
    orden = sorted(r["ms"])
    peor = max(r["err_por_minuto"].items(), key=lambda kv: kv[1], default=(None, 0))
    minutos_malos = sorted(m for m, n in r["err_por_minuto"].items()
                           if n / max(1, r["por_minuto"][m]) * 100 >= umbral)
    datos = {
        "lineas": r["lineas"],
        "descartadas": r["descartadas"],
        "peticiones": r["peticiones"],
        "errores": r["errores"],
        "porcentaje_error": round(r["errores"] / r["peticiones"] * 100, 2),
        "p50_ms": pct(orden, 50), "p95_ms": pct(orden, 95), "p99_ms": pct(orden, 99),
        "peor_minuto": peor[0], "errores_en_ese_minuto": peor[1],
        "ventana": [minutos_malos[0], minutos_malos[-1]] if minutos_malos else None,
        "patrones": r["patrones"].most_common(3),
        "servidores": dict(r["por_servidor"].most_common()),
        "rutas": dict(r["por_ruta"].most_common(3)),
    }
    return datos, (1 if datos["porcentaje_error"] >= umbral else 0)


def escribir(d, r):
    print(f"  lineas leidas   {d['lineas']}  (descartadas {d['descartadas']}"
          f"{': ' + r['muestra_descartada'] if r['muestra_descartada'] else ''})")
    print(f"  peticiones      {d['peticiones']}")
    print(f"  errores         {d['errores']}  ({d['porcentaje_error']}%)")
    print(f"  latencia        p50 {d['p50_ms']} ms · p95 {d['p95_ms']} ms · p99 {d['p99_ms']} ms")
    if d["ventana"]:
        print(f"  ventana mala    {d['ventana'][0]} -> {d['ventana'][1]} "
              f"(peor: {d['peor_minuto']} con {d['errores_en_ese_minuto']})")
        print(f"  por servidor    {d['servidores']}")
        print(f"  rutas           {d['rutas']}")
        print("  patrones de error mas repetidos:")
        for p, n in d["patrones"]:
            print(f"    {n:>5}  {p[:64]}")
    else:
        print("  sin minutos por encima del umbral")


def main(argv=None):
    ap = argparse.ArgumentParser(prog="triaje.py", description=__doc__.split("\n")[0])
    ap.add_argument("logs", nargs="+")
    ap.add_argument("--desde", help="HH:MM (UTC, como el log)")
    ap.add_argument("--hasta", help="HH:MM (UTC, como el log)")
    ap.add_argument("--umbral", type=float, default=5.0, help="%% de error que ya es un incidente")
    ap.add_argument("--json", action="store_true", help="salida para pegar en el ticket")
    a = ap.parse_args(argv)

    rutas = []
    for patr in a.logs:                      # la shell de Windows no expande *
        p = Path(patr)
        rutas += sorted(p.parent.glob(p.name)) if "*" in p.name else [p]
    faltan = [str(p) for p in rutas if not p.exists()]
    if not rutas or faltan:
        print(f"no encuentro: {faltan or a.logs}", file=sys.stderr)
        return 2

    r = analizar(rutas, a.desde, a.hasta)
    d, codigo = informe(r, a.umbral)
    if not d:
        return codigo
    if a.json:
        print(json.dumps(d, indent=2))
    else:
        print(f"== triaje de {len(rutas)} fichero(s) "
              f"[{a.desde or 'inicio'} -> {a.hasta or 'fin'}] ==")
        escribir(d, r)
        print(f"  -> codigo de salida {codigo}")
    return codigo


if __name__ == "__main__":
    sys.exit(main())
