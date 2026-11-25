# -*- coding: utf-8 -*-
"""Banco de precios: guardar los registros (logs) de tus aplicaciones en 4 nubes, de fuentes OFICIALES (sin cuenta).
  · AWS CloudWatch Logs: lista pública AmazonCloudWatch us-east-1 (ingesta Standard e Infrequent Access, almacenamiento,
    consultas de Logs Insights). La lista no trae franja gratis; la capa gratuita de AWS es un programa aparte y no se cuenta.
  · Azure Log Analytics: Retail Prices API eastus (Analytics Logs: los primeros 5 GB gratis por la franja «tier 5»;
    retención). learn.microsoft.com/azure/azure-monitor/logs/cost-logs: la ingesta «Includes 31 days of analytics retention».
  · Google Cloud Logging: página oficial cloud.google.com/stackdriver/pricing (0,50/GiB, primeros 50 GiB/proyecto/mes,
    30 días incluidos, 0,01/GiB-mes después).
  · Oracle OCI Logging: API pública de precios (solo cobra almacenamiento: 0-10 GB gratis, después 0,05/GB-mes).
Escenarios: 1 GB al día y 10 GB al día; 30 y 90 días de retención. Mes = 30 días de ingesta. GB y GiB se tratan igual.
    python logs.py   -> SALIDA-logs.md
"""
import csv
import html
import json
import re
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

AQUI = Path(__file__).parent
CACHE = AQUI / "cache"
CACHE.mkdir(exist_ok=True)
OUT = []


def bajar(url, nombre):
    p = CACHE / nombre
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/130.0"})
    p.write_bytes(urllib.request.urlopen(req, timeout=300).read())
    return p


def aws():
    p = bajar("https://pricing.us-east-1.amazonaws.com/offers/v1.0/aws/AmazonCloudWatch/current/us-east-1/index.csv", "cw.csv")
    f = open(p, encoding="utf-8")
    cab = [next(f) for _ in range(5)]
    pub = next(l for l in cab if "Publication Date" in l).split(",")[1].strip().strip('"')
    r = {}
    for row in csv.DictReader(f):
        d = row["PriceDescription"]
        if "custom log data ingested in Standard log class" in d:
            r["std"] = float(row["PricePerUnit"])
        if "custom log data ingested in Infrequent Access log class" in d:
            r["ia"] = float(row["PricePerUnit"])
        if "per GB-mo of log storage" in d:
            r["alm"] = float(row["PricePerUnit"])
        if "per GB log data scanned by CloudWatch Logs Insights" in d:
            r["consulta"] = float(row["PricePerUnit"])
    return pub, r


def azure():
    url = "https://prices.azure.com/api/retail/prices?$filter=" + urllib.parse.quote(
        "serviceName eq 'Log Analytics' and armRegionName eq 'eastus' and skuName eq 'Analytics Logs' and priceType eq 'Consumption'")
    items = json.load(urllib.request.urlopen(url, timeout=120))["Items"]
    ing = [i for i in items if i["meterName"] == "Analytics Logs Data Ingestion"]
    gratis = max(i["tierMinimumUnits"] for i in ing)
    precio = next(i["retailPrice"] for i in ing if i["tierMinimumUnits"] == gratis)
    ret = next(i["retailPrice"] for i in items if i["meterName"] == "Analytics Logs Data Retention")
    otros = json.load(urllib.request.urlopen("https://prices.azure.com/api/retail/prices?$filter=" + urllib.parse.quote(
        "serviceName eq 'Azure Monitor' and armRegionName eq 'eastus' and priceType eq 'Consumption' and "
        "(meterName eq 'Basic Logs Data Ingestion' or meterName eq 'Auxiliary Logs Data Ingestion')"), timeout=120))["Items"]
    basic = next(i["retailPrice"] for i in otros if i["meterName"] == "Basic Logs Data Ingestion")
    aux = next(i["retailPrice"] for i in otros if i["meterName"] == "Auxiliary Logs Data Ingestion")
    return {"gratis": gratis, "ing": precio, "ret": ret, "incluidos": 31, "basic": basic, "aux": aux}


def google():
    s = bajar("https://cloud.google.com/stackdriver/pricing", "gcplog.html").read_text(encoding="utf-8")
    t = re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", " ", s)))
    i = t.find("Cloud Logging pricing summary")
    seg = t[i:i + 1500]
    ing = float(re.search(r"Logging storage\* except for vended network logs\. \$([0-9.]+)/GiB", seg).group(1))
    gratis = float(re.search(r"First ([0-9]+) GiB/project/month", seg).group(1))
    incluidos = int(re.search(r"includes up to ([0-9]+) days of storage", seg).group(1))
    ret = float(re.search(r"Logging retention\S* \$([0-9.]+) per GiB per month", seg).group(1))
    return {"gratis": gratis, "ing": ing, "ret": ret, "incluidos": incluidos}


def oracle():
    p = bajar("https://apexapps.oracle.com/pls/apex/cetools/api/v1/products/?currencyCode=USD", "oracle.json")
    it = next(i for i in json.loads(p.read_text(encoding="utf-8"))["items"] if i["partNumber"] == "B92593")
    franjas = it["currencyCodeLocalizations"][0]["prices"]
    gratis = next(x["rangeMax"] for x in franjas if x["value"] == 0)
    precio = next(x["value"] for x in franjas if x["value"] > 0)
    return {"gratis": gratis, "alm": precio, "nombre": it["displayName"]}


def main():
    pub, a = aws()
    z, g, o = azure(), google(), oracle()
    OUT.append(f"# SALIDA — los registros (logs) en 4 nubes\n\nGenerado {datetime.now(timezone.utc):%Y-%m-%d %H:%M} UTC con "
               "`python logs.py`. Precios de lista en USD, sin impuestos. Mes = 30 días de ingesta.\n")
    OUT.append("## Las tarifas\n\n```")
    OUT.append(f"AWS     ingesta Standard {a['std']}/GB · Infrequent Access {a['ia']}/GB · almacenamiento {a['alm']}/GB-mes · "
               f"Logs Insights {a['consulta']}/GB leído   (lista us-east-1 publicada {pub}; sin franja gratis en la lista)")
    OUT.append(f"Azure   ingesta {z['ing']}/GB (primeros {z['gratis']:.0f} GB gratis) · {z['incluidos']} días incluidos · "
               f"retención después {z['ret']}/GB-mes   (Retail Prices API)")
    OUT.append(f"        planes más baratos: Basic Logs {z['basic']}/GB · Auxiliary Logs {z['aux']}/GB de ingesta (consultas aparte, por GB leído)")
    OUT.append(f"Google  ingesta {g['ing']}/GiB (primeros {g['gratis']:.0f} GiB por proyecto gratis) · {g['incluidos']} días incluidos · "
               f"retención después {g['ret']}/GiB-mes   (cloud.google.com/stackdriver/pricing)")
    OUT.append(f"Oracle  ingesta: sin cobro en la API · «{o['nombre']}» 0 USD hasta {o['gratis']} GB, después {o['alm']}/GB-mes")
    OUT.append("```\n")

    def costes(gb_dia, dias):
        ing = gb_dia * 30                      # lo que entra en un mes
        guardado = gb_dia * dias               # lo que está guardado en régimen estable
        aw = ing * a["std"] + guardado * a["alm"]
        aw_ia = ing * a["ia"] + guardado * a["alm"]
        az = max(0, ing - z["gratis"]) * z["ing"] + max(0, gb_dia * (dias - z["incluidos"])) * z["ret"]
        gg = max(0, ing - g["gratis"]) * g["ing"] + max(0, gb_dia * (dias - g["incluidos"])) * g["ret"]
        oo = max(0, guardado - o["gratis"]) * o["alm"]
        filas = [("AWS", aw), ("AWS (Infrequent Access)", aw_ia), ("Azure (Analytics)", az), ("Google", gg), ("Oracle", oo)]
        if dias == 30:   # Basic y Auxiliary: solo la ingesta; su retención larga no se calcula aquí
            filas += [("Azure (Basic, solo ingesta)", ing * z["basic"]), ("Azure (Auxiliary, solo ingesta)", ing * z["aux"])]
        return filas

    for gb_dia in (1, 10, 50):
        for dias in (30, 90):
            OUT.append(f"## {gb_dia} GB al día ({gb_dia * 30} GB/mes), {dias} días guardados\n\n```")
            for n, c in sorted(costes(gb_dia, dias), key=lambda x: x[1]):
                OUT.append(f"{n:<32} {c:>9.2f} USD/mes")
            OUT.append("```\n")
    OUT.append("## AWS: lo que cuesta leerlos con Logs Insights\n\n```")
    for leidos in (10, 300, 3000):
        OUT.append(f"consultas que leen {leidos:>5} GB al mes → {leidos * a['consulta']:.2f} USD")
    OUT.append("```\n")
    # ── el ahorro de mandar menos (AWS, 30 días): 10 GB/día → la mitad, y además en acceso poco frecuente
    OUT.append("## AWS, 30 días: lo que ahorras mandando menos\n\n```")
    for etiqueta, gbd, clase in (("10 GB/día, Standard", 10, "std"), ("5 GB/día (la mitad), Standard", 5, "std"),
                                 ("5 GB/día, Infrequent Access", 5, "ia")):
        c = gbd * 30 * a[clase] + gbd * 30 * a["alm"]
        OUT.append(f"{etiqueta:<32} {c:>8.2f} USD/mes")
    OUT.append("```\n")
    # ── los registros que generan los propios servicios de AWS («vended»): por tramos
    f = open(CACHE / "cw.csv", encoding="utf-8")
    [next(f) for _ in range(5)]
    tramos = sorted({(float(r["StartingRange"] or 0), float(r["PricePerUnit"]), r["PriceDescription"].split(" of vended")[0])
                     for r in csv.DictReader(f) if "of vended log data ingested to CloudWatch logs per month" in r["PriceDescription"]})
    OUT.append("## AWS: registros que generan sus propios servicios (vended), por tramos\n\n```")
    OUT.extend(d for _, _, d in tramos)
    OUT.append("```\n")
    t = re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", " ", (CACHE / "gcplog.html").read_text(encoding="utf-8"))))
    req = re.search(r"_Required log bucket, which has a fixed retention period of ([0-9]+) days", t)
    gratis_req = "There are no storage charges for logs stored in the Required log bucket" in t
    OUT.append("## Google: el bucket _Required\n\n```")
    OUT.append(f"retención fija: {req.group(1)} días · sin cobro de almacenamiento: {'sí' if gratis_req else 'no'}")
    OUT.append("```\n")
    (AQUI / "SALIDA-logs.md").write_text("\n".join(OUT), encoding="utf-8")
    print("\n".join(OUT))


if __name__ == "__main__":
    main()
