# -*- coding: utf-8 -*-
"""Precios de la LISTA PÚBLICA de AWS (sin cuenta ni credenciales), para los vídeos 692 y 693 de cultura-devops.

Descarga cada CSV de pricing.us-east-1.amazonaws.com en streaming, se queda solo con las filas que usan los vídeos y las
guarda en `precios/<oferta>-<región>.json` con su fecha de publicación. Mismo método que el curso FinOps.

    python lista.py            -> baja (o reusa) los filtros de precios/
    python lista.py --refrescar

⚠️ Son precios de LISTA bajo demanda. La factura real lleva impuestos y créditos: todo importe es «precio × uso».
"""
import csv
import io
import json
import sys
import urllib.request
from pathlib import Path

AQUI = Path(__file__).resolve().parent
PRECIOS = AQUI / "precios"
PRECIOS.mkdir(exist_ok=True)
BASE = "https://pricing.us-east-1.amazonaws.com/offers/v1.0/aws"
H = 730  # horas de un mes medio (365 × 24 / 12)

MAQUINAS = ["t3.micro", "t3.small", "t4g.micro", "t4g.small", "c7i-flex.large", "m7i-flex.large"]


def _ec2(r):
    ut = r["usageType"]
    if r["TermType"] != "OnDemand":
        return False
    if "BoxUsage:" in ut:
        return (r["Instance Type"] in MAQUINAS and r["Operating System"] == "Linux" and r["Tenancy"] == "Shared"
                and r["Pre Installed S/W"] == "NA" and r["CapacityStatus"] == "Used" and r["operation"] == "RunInstances")
    return ut.split("-", 1)[-1] in ("NatGateway-Hours", "NatGateway-Bytes") or ut.endswith(
        ("EBS:VolumeUsage.gp3", "EBS:SnapshotUsage")) or ut in ("NatGateway-Hours", "NatGateway-Bytes")


def _vpc(r):
    return "PublicIPv4" in r["usageType"] and r["TermType"] == "OnDemand"


def _rds(r):
    if r["TermType"] != "OnDemand" or r["Database Engine"] != "PostgreSQL" or r["Deployment Option"] != "Single-AZ":
        return False
    if r["Product Family"] == "Database Instance":
        return r["Instance Type"] in ("db.t4g.micro", "db.t3.micro")
    return r["Product Family"] == "Database Storage" and r["Volume Type"] in ("General Purpose", "General Purpose-GP3")


def _elb(r):
    return r["Product Family"] == "Load Balancer-Application" and r["usageType"] in ("LoadBalancerUsage", "LCUUsage") \
        and r["Location Type"] == "AWS Region"


def _s3(r):
    return r.get("Volume Type") == "Standard" and r["Unit"] == "GB-Mo" and r["StartingRange"] == "0" \
        and r["TermType"] == "OnDemand" and r["Location Type"] == "AWS Region"


def _lambda(r):
    return r["TermType"] == "OnDemand" and r["usageType"].split("-", 1)[-1] in ("Request", "Lambda-GB-Second") \
        or r["usageType"] in ("Request", "Lambda-GB-Second")


def _dt(r):
    return r["Transfer Type"] == "AWS Outbound" and r["To Location Type"] == "Other" and r["Unit"] == "GB" \
        and r["From Location Type"] == "AWS Region"


FILTROS = {"AmazonEC2": _ec2, "AmazonVPC": _vpc, "AmazonRDS": _rds, "AWSELB": _elb, "AmazonS3": _s3,
           "AWSLambda": _lambda, "AWSDataTransfer": _dt}


def bajar(oferta, region="us-east-1", refrescar=False):
    destino = PRECIOS / f"{oferta}-{region}.json"
    if destino.exists() and not refrescar:
        return json.loads(destino.read_text(encoding="utf-8"))
    url = f"{BASE}/{oferta}/current/{region}/index.csv"
    print(f"  bajando {url}", flush=True)
    resp = urllib.request.urlopen(urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"}), timeout=900)
    txt = io.TextIOWrapper(resp, encoding="utf-8", newline="")
    cab = [next(txt) for _ in range(5)]
    pub = next(l for l in cab if "Publication Date" in l).split(",")[1].strip().strip('"')
    filtro, filas, n = FILTROS[oferta], [], 0
    cols = None
    for r in csv.DictReader(txt):
        n += 1
        cols = cols or list(r)
        if filtro(r):
            filas.append({k: v for k, v in r.items() if v})
    d = {"fuente": url, "publicacion": pub, "filas_leidas": n, "filas": filas}
    destino.write_text(json.dumps(d, ensure_ascii=False, indent=0), encoding="utf-8")
    return d


def uno(d, **cond):
    """La única fila que cumple las condiciones (columna=valor, o columna__fin=sufijo, o columna__tiene=texto)."""
    def ok(r):
        for k, v in cond.items():
            col, _, op = k.partition("__")
            col = col.replace("_", " ") if col not in r else col
            x = r.get(col, "")
            if op == "fin" and not x.endswith(v) or op == "tiene" and v not in x or not op and x != v:
                return False
        return True
    hay = [r for r in d["filas"] if ok(r)]
    assert len({r["PricePerUnit"] for r in hay}) == 1, f"{cond}: {len(hay)} filas, precios {[r['PricePerUnit'] for r in hay]}"
    return float(hay[0]["PricePerUnit"]), hay[0]["PriceDescription"]


def usd(x, dec=2):
    return f"{x:,.{dec}f} USD"


if __name__ == "__main__":
    ref = "--refrescar" in sys.argv
    for of in FILTROS:
        d = bajar(of, refrescar=ref)
        print(of, d["publicacion"], len(d["filas"]), "filas")
    for reg in ("sa-east-1", "mx-central-1"):
        for of in ("AmazonEC2", "AmazonS3"):
            d = bajar(of, reg, refrescar=ref)
            print(of, reg, d["publicacion"], len(d["filas"]), "filas")
