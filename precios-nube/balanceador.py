# -*- coding: utf-8 -*-
"""Banco de precios: el balanceador de carga HTTP (capa 7) en 4 nubes, de fuentes OFICIALES (sin cuenta).
  · AWS Application Load Balancer: lista pública AWSELB us-east-1 (0,0225/h + 0,008 por LCU-hora).
    aws.amazon.com/elasticloadbalancing/pricing: 1 LCU = 1 GB por hora procesado (destinos EC2), entre otras dimensiones;
    se cobra la dimensión más alta.
  · Azure Application Gateway v2 (Basic y Standard): Retail Prices API eastus (fijo por hora + 0,008 por unidad de capacidad).
    learn.microsoft.com (understanding-pricing): 1 CU = 1 GB por hora (2,22 Mbps); la hora parcial se cobra entera.
  · Google External Application Load Balancer: cloud.google.com/vpc/network-pricing (primeras 5 reglas 0,025/h, datos
    procesados 0,008/GiB de entrada y 0,008/GiB de salida).
  · Oracle Flexible Load Balancer: API pública de precios (base: 744 h/mes gratis, después 0,0113/h; ancho de banda: 7.440
    Mbps-hora gratis, después 0,0001 por Mbps-hora); su lista: «No separate charges for any data handled».
MODELO: un balanceador, 730 h; «GB procesados» = ida y vuelta; el tráfico es la dimensión dominante (en AWS y Azure podría
dominar otra, como conexiones nuevas). Oracle: ancho de banda reservado = 3 veces el promedio, redondeado a 10 Mbps.
    python balanceador.py   -> SALIDA-balanceador.md
"""
import csv
import html
import json
import math
import re
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

AQUI = Path(__file__).parent
CACHE = AQUI / "cache"
CACHE.mkdir(exist_ok=True)
H = 730
OUT = []


def bajar(url, nombre):
    p = CACHE / nombre
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/130.0"})
    p.write_bytes(urllib.request.urlopen(req, timeout=300).read())
    return p


def aws():
    p = bajar("https://pricing.us-east-1.amazonaws.com/offers/v1.0/aws/AWSELB/current/us-east-1/index.csv", "elb.csv")
    f = open(p, encoding="utf-8")
    cab = [next(f) for _ in range(5)]
    pub = next(l for l in cab if "Publication Date" in l).split(",")[1].strip().strip('"')
    filas = list(csv.DictReader(f))
    hora = next(float(r["PricePerUnit"]) for r in filas if r["PriceDescription"].startswith("$0.0225 per Application LoadBalancer-hour"))
    lcu = next(float(r["PricePerUnit"]) for r in filas if r["PriceDescription"].startswith("$0.008 per used Application load balancer capacity unit-hour"))
    return pub, hora, lcu


def azure():
    url = "https://prices.azure.com/api/retail/prices?$filter=" + urllib.parse.quote(
        "serviceName eq 'Application Gateway' and armRegionName eq 'eastus' and priceType eq 'Consumption'")
    it = json.load(urllib.request.urlopen(url, timeout=120))["Items"]
    g = lambda prod, med: next(i["retailPrice"] for i in it if i["productName"] == prod and i["meterName"] == med)
    return {"basic_fijo": g("Application Gateway Basic v2", "Basic Fixed Cost"),
            "basic_cu": g("Application Gateway Basic v2", "Basic Capacity Units"),
            "std_fijo": g("Application Gateway Standard v2", "Standard Fixed Cost"),
            "std_cu": g("Application Gateway Standard v2", "Standard Capacity Units")}


def google():
    s = bajar("https://cloud.google.com/vpc/network-pricing", "gcpnet.html").read_text(encoding="utf-8")
    t = re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", " ", s)))
    m = re.search(r"First 5 forwarding rules \$([0-9.]+) / 1 hour Per additional forwarding rule \$([0-9.]+) / 1 hour "
                  r"Inbound data processed by load balancer \$([0-9.]+) / 1 gibibyte Outbound data processed by load balancer \$([0-9.]+)", t)
    return tuple(map(float, m.groups()))


def oracle():
    p = bajar("https://apexapps.oracle.com/pls/apex/cetools/api/v1/products/?currencyCode=USD", "oracle.json")
    items = {i["partNumber"]: i["currencyCodeLocalizations"][0]["prices"] for i in json.loads(p.read_text(encoding="utf-8"))["items"]}
    base, bw = items["B93030"], items["B93031"]
    return {"base_gratis_h": next(x["rangeMax"] for x in base if x["value"] == 0), "base_h": next(x["value"] for x in base if x["value"] > 0),
            "bw_gratis": next(x["rangeMax"] for x in bw if x["value"] == 0), "bw": next(x["value"] for x in bw if x["value"] > 0)}


def main():
    pub, a_h, a_lcu = aws()
    z = azure()
    g_regla, g_regla_extra, g_in, g_out = google()
    o = oracle()
    OUT.append(f"# SALIDA — el balanceador de carga HTTP en 4 nubes\n\nGenerado {datetime.now(timezone.utc):%Y-%m-%d %H:%M} UTC con "
               f"`python balanceador.py`. Un balanceador, {H} h. Precios de lista en USD, sin impuestos.\n")
    OUT.append("## Las tarifas\n\n```")
    OUT.append(f"AWS ALB              {a_h}/h + {a_lcu} por LCU-hora (1 LCU = 1 GB/h procesado, entre otras)   (lista us-east-1 {pub})")
    OUT.append(f"Azure App GW Basic v2 {z['basic_fijo']}/h + {z['basic_cu']} por CU-hora (1 CU = 1 GB/h; hora parcial = entera)")
    OUT.append(f"Azure App GW Std v2   {z['std_fijo']}/h + {z['std_cu']} por CU-hora")
    OUT.append(f"Google App LB        primeras 5 reglas {g_regla}/h (+{g_regla_extra}/h cada una más) + {g_in}/GiB entrada + {g_out}/GiB salida")
    OUT.append(f"Oracle Flexible LB   base: {o['base_gratis_h']:.0f} h/mes gratis, después {o['base_h']}/h · ancho de banda: "
               f"{o['bw_gratis']:,.0f} Mbps-hora gratis, después {o['bw']}/Mbps-hora · sin cobro por datos")
    OUT.append("```\n")
    OUT.append("## Sin tráfico: lo que cuesta solo tenerlo encendido\n\n```")
    for n, c in sorted([("AWS ALB", a_h * H), ("Azure App GW Basic v2", z["basic_fijo"] * H), ("Azure App GW Standard v2", z["std_fijo"] * H),
                        ("Google App LB", g_regla * H), ("Oracle Flexible LB (el primero)", max(0, H - o["base_gratis_h"]) * o["base_h"])],
                       key=lambda x: x[1]):
        OUT.append(f"{n:<34} {c:>8.2f} USD/mes")
    OUT.append("```\n")

    def costes(gb_mes):
        gbh = gb_mes / H
        mbps = gb_mes * 8000 / (H * 3600)                       # promedio en Mbps (1 GB = 8.000 Mb)
        reservado = max(10, math.ceil(3 * mbps / 10) * 10)
        cu = max(1, math.ceil(gbh))
        return [("AWS ALB", a_h * H + a_lcu * gbh * H),
                ("Azure App GW Basic v2", z["basic_fijo"] * H + z["basic_cu"] * cu * H),
                ("Azure App GW Standard v2", z["std_fijo"] * H + z["std_cu"] * cu * H),
                ("Google App LB", g_regla * H + gb_mes * g_out),          # entrada + salida = gb_mes en total
                (f"Oracle Flexible LB ({reservado} Mbps)", max(0, H - o["base_gratis_h"]) * o["base_h"]
                 + max(0, reservado * H - o["bw_gratis"]) * o["bw"])]

    for gb in (100, 1000, 10000, 50000):
        OUT.append(f"## {gb:,} GB procesados al mes\n\n```")
        for n, c in sorted(costes(gb), key=lambda x: x[1]):
            OUT.append(f"{n:<34} {c:>8.2f} USD/mes")
        OUT.append("```\n")
    OUT.append("## Tres balanceadores (un entorno de pruebas, otro de staging y producción), sin apenas tráfico\n\n```")
    for n, c in sorted([("AWS ALB", 3 * a_h * H), ("Azure App GW Basic v2", 3 * z["basic_fijo"] * H), ("Google App LB", 3 * g_regla * H),
                        ("Oracle Flexible LB (3 × 10 Mbps)", 2 * H * o["base_h"] + max(0, H - o["base_gratis_h"]) * o["base_h"]
                         + max(0, 3 * 10 * H - o["bw_gratis"]) * o["bw"])], key=lambda x: x[1]):
        OUT.append(f"{n:<34} {c:>8.2f} USD/mes")
    OUT.append("```\n")
    # ── capa 4 (balanceador de red): NLB de AWS, Load Balancer Standard de Azure, Google (mismas reglas y datos) y Oracle NLB
    f = open(CACHE / "elb.csv", encoding="utf-8")
    [next(f) for _ in range(5)]
    filas = list(csv.DictReader(f))
    nlb_h = next(float(r["PricePerUnit"]) for r in filas if r["PriceDescription"].startswith("$0.0225 per Network LoadBalancer-hour"))
    nlcu = next(float(r["PricePerUnit"]) for r in filas if r["PriceDescription"].startswith("$0.006 per used Network load balancer capacity unit-hour"))
    lbz = json.load(urllib.request.urlopen("https://prices.azure.com/api/retail/prices?$filter=" + urllib.parse.quote(
        "serviceName eq 'Load Balancer' and skuName eq 'Standard' and priceType eq 'Consumption'"), timeout=120))["Items"]
    lbz_h = next(i["retailPrice"] for i in lbz if i["meterName"] == "Standard Included LB Rules and Outbound Rules")
    lbz_gb = next(i["retailPrice"] for i in lbz if i["meterName"] == "Standard Data Processed")
    s = (CACHE / "ocinet.html").read_text(encoding="utf-8", errors="replace")
    t = re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", " ", re.sub(r"<script.*?</script>|<style.*?</style>", "", s, flags=re.S))))
    onlb = re.search(r"Flexible Network Load Balancer (\S+)", t).group(1)
    OUT.append("## Capa 4 (balanceador de red): las tarifas\n\n```")
    OUT.append(f"AWS NLB          {nlb_h}/h + {nlcu} por NLCU-hora (1 NLCU = 1 GB/h, 800 conexiones nuevas/s o 100.000 activas)")
    OUT.append(f"Azure LB Std     {lbz_h}/h (primeras 5 reglas) + {lbz_gb}/GB procesado")
    OUT.append(f"Google           mismas tarifas: {g_regla}/h + {g_in}/GiB entrada y {g_out}/GiB salida")
    OUT.append(f"Oracle NLB       «Flexible Network Load Balancer {onlb}» en su lista de precios")
    OUT.append("```\n")
    for gb in (1000, 10000):
        OUT.append(f"## Capa 4, {gb:,} GB al mes\n\n```")
        for n, c in sorted([("AWS NLB", nlb_h * H + nlcu * gb), ("Azure Load Balancer Standard", lbz_h * H + lbz_gb * gb),
                            ("Google (passthrough)", g_regla * H + g_out * gb), ("Oracle NLB", 0.0 if onlb == "Free" else float("nan"))],
                           key=lambda x: x[1]):
            OUT.append(f"{n:<34} {c:>8.2f} USD/mes")
        OUT.append("```\n")
    (AQUI / "SALIDA-balanceador.md").write_text("\n".join(OUT), encoding="utf-8")
    print("\n".join(OUT))


if __name__ == "__main__":
    main()
