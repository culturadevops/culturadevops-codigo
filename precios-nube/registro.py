# -*- coding: utf-8 -*-
"""Banco de precios: el registro de imágenes de contenedor en 4 nubes, de fuentes OFICIALES (sin cuenta).
  · AWS ECR: lista pública AmazonECR us-east-1 (almacenamiento por GB-mes).
  · Azure Container Registry: Retail Prices API eastus (Basic, Standard y Premium por día + GB extra) y
    learn.microsoft.com (container-registry-skus): almacenamiento incluido 10, 100 y 500 GiB.
  · Google Artifact Registry: página oficial cloud.google.com/artifact-registry/pricing (0,5 GB gratis, después por GiB).
  · Oracle OCI Registry: lista de precios oficial — «Container Image Storage: Same as Object Storage - Standard»;
    Object Storage estándar en la API (franja gratis y precio por GB-mes).
Escenarios: 5, 50, 500 y 2.000 GB guardados. Mes = 730 h; un día = 1/30,4 del mes para los planes diarios de Azure.
    python registro.py   -> SALIDA-registro.md
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
DIAS = 730 / 24
OUT = []


def bajar(url, nombre):
    p = CACHE / nombre
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/130.0"})
    p.write_bytes(urllib.request.urlopen(req, timeout=300).read())
    return p


def aws():
    p = bajar("https://pricing.us-east-1.amazonaws.com/offers/v1.0/aws/AmazonECR/current/us-east-1/index.csv", "ecr.csv")
    f = open(p, encoding="utf-8")
    cab = [next(f) for _ in range(5)]
    pub = next(l for l in cab if "Publication Date" in l).split(",")[1].strip().strip('"')
    gb = next(float(r["PricePerUnit"]) for r in csv.DictReader(f) if r["PriceDescription"] == "$0.10 per GB-month of data storage")
    return pub, gb


def azure():
    url = "https://prices.azure.com/api/retail/prices?$filter=" + urllib.parse.quote(
        "serviceName eq 'Container Registry' and armRegionName eq 'eastus' and priceType eq 'Consumption'")
    it = json.load(urllib.request.urlopen(url, timeout=120))["Items"]
    dia = {s: next(i["retailPrice"] for i in it if i["meterName"] == f"{s} Registry Unit") for s in ("Basic", "Standard", "Premium")}
    global Z_REPLICA
    Z_REPLICA = next(i["retailPrice"] for i in it if i["meterName"] == "Premium Registry Replication Unit")
    gb = next(i["retailPrice"] for i in it if i["skuName"] == "Basic" and i["meterName"] == "Data Stored")
    incluido = {"Basic": 10, "Standard": 100, "Premium": 500}          # learn.microsoft.com, container-registry-skus
    return dia, gb, incluido


def google():
    s = bajar("https://cloud.google.com/artifact-registry/pricing", "gcpar.html").read_text(encoding="utf-8")
    t = re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", " ", s)))
    m = re.search(r"Artifact Registry Storage 0 gibibyte month to ([0-9.]+) gibibyte month \$0\.00 \(Free\).*?and above \$([0-9.]+) / 1 gibibyte hour", t)
    return float(m.group(1)), float(m.group(2)) * 730


def oracle():
    s = bajar("https://www.oracle.com/cloud/networking/pricing/", "ocinet.html").read_text(encoding="utf-8", errors="replace")
    t = re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", " ", re.sub(r"<script.*?</script>|<style.*?</style>", "", s, flags=re.S))))
    regla = re.search(r"Container Image Storage (Same as [^G]+?) Gigabyte", t).group(1).strip()
    p = bajar("https://apexapps.oracle.com/pls/apex/cetools/api/v1/products/?currencyCode=USD", "oracle.json")
    fr = next(i for i in json.loads(p.read_text(encoding="utf-8"))["items"] if i["partNumber"] == "B91628")["currencyCodeLocalizations"][0]["prices"]
    return regla, next(x["rangeMax"] for x in fr if x["value"] == 0), next(x["value"] for x in fr if x["value"] > 0)


def main():
    pub, a_gb = aws()
    z_dia, z_gb, z_inc = azure()
    g_gratis, g_gb = google()
    o_regla, o_gratis, o_gb = oracle()
    OUT.append(f"# SALIDA — el registro de imágenes de contenedor en 4 nubes\n\nGenerado {datetime.now(timezone.utc):%Y-%m-%d %H:%M} UTC con "
               "`python registro.py`. Precios de lista en USD, sin impuestos. Solo almacenamiento; descargar en la misma región se trata "
               "aparte (ver el vídeo).\n")
    OUT.append("## Las tarifas\n\n```")
    OUT.append(f"AWS ECR            {a_gb} por GB al mes   (lista us-east-1 {pub})")
    OUT.append("Azure ACR          " + " · ".join(f"{s} {z_dia[s]}/día ({z_dia[s] * DIAS:.2f}/mes) con {z_inc[s]} GiB" for s in z_dia) +
               f" · GB extra {z_gb}/mes")
    OUT.append(f"                   réplica en otra región (Premium): {Z_REPLICA}/día ({Z_REPLICA * DIAS:.2f}/mes)")
    OUT.append(f"Google Artifact R. {g_gratis} GB gratis, después {g_gb:.4f} por GiB al mes")
    OUT.append(f"Oracle OCIR        «Container Image Storage: {o_regla}» → {o_gratis:.0f} GB gratis, después {o_gb} por GB al mes")
    OUT.append("```\n")
    for gb in (5, 50, 500, 2000):
        filas = [("AWS ECR", gb * a_gb)]
        for s in ("Basic", "Standard", "Premium"):
            filas.append((f"Azure ACR {s}", z_dia[s] * DIAS + max(0, gb - z_inc[s]) * z_gb))
        filas += [("Google Artifact Registry", max(0, gb - g_gratis) * g_gb), ("Oracle OCIR", max(0, gb - o_gratis) * o_gb)]
        OUT.append(f"## {gb:,} GB de imágenes guardadas\n\n```")
        for n, c in sorted(filas, key=lambda x: x[1]):
            OUT.append(f"{n:<28} {c:>8.2f} USD/mes")
        OUT.append("```\n")
    # ── lo que de verdad la dispara: imágenes que se acumulan, 20 builds al día de 300 MB, sin limpieza
    OUT.append("## Sin limpieza: 20 builds al día de 300 MB (6 GB al día), lo guardado y lo que cuesta ese mes\n\n```")
    for mes in (1, 3, 6, 12):
        gb = 6 * 30 * mes
        az_std = z_dia["Standard"] * DIAS + max(0, gb - z_inc["Standard"]) * z_gb
        OUT.append(f"mes {mes:>2}: {gb:>5,} GB → AWS {gb * a_gb:>7.2f} · Google {max(0, gb - g_gratis) * g_gb:>7.2f} · "
                   f"Azure Standard {az_std:>7.2f} · Oracle {max(0, gb - o_gratis) * o_gb:>6.2f} USD")
    OUT.append("con limpieza (solo las últimas 10 imágenes, 3 GB): AWS "
               f"{3 * a_gb:.2f} · Google {max(0, 3 - g_gratis) * g_gb:.2f} · Azure Basic {z_dia['Basic'] * DIAS:.2f} · Oracle 0.00 USD")
    OUT.append("```\n")
    # ── escanear las imágenes en busca de vulnerabilidades: 20 builds al día = 600 imágenes nuevas al mes
    f = open(bajar("https://pricing.us-east-1.amazonaws.com/offers/v1.0/aws/AmazonInspectorV2/current/us-east-1/index.csv", "insp.csv"),
             encoding="utf-8")
    [next(f) for _ in range(5)]
    ins = list(csv.DictReader(f))
    ins_ini = next(float(r["PricePerUnit"]) for r in ins if "for container-image-initial-scan in" in r["PriceDescription"])
    ins_re = next(float(r["PricePerUnit"]) for r in ins if "for container-image-re-scan in" in r["PriceDescription"])
    t = re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", " ", bajar("https://cloud.google.com/artifact-analysis/pricing", "gcpaa.html")
                                                    .read_text(encoding="utf-8"))))
    g_scan = float(re.search(r"automatic vulnerability scanning feature.*?the price is \$([0-9.]+) per scan", t).group(1))
    g_defecto = "container scanning, which is enabled by default on new container-based repositories" in t
    s = (CACHE / "ocinet.html").read_text(encoding="utf-8", errors="replace")
    to = re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", " ", re.sub(r"<script.*?</script>|<style.*?</style>", "", s, flags=re.S))))
    o_vss = re.search(r"Oracle Cloud Infrastructure Vulnerability Scanning Service (\S+)", to).group(1)
    OUT.append("## Escanear vulnerabilidades: 600 imágenes nuevas al mes (20 builds al día)\n\n```")
    OUT.append(f"Google Artifact Analysis  {g_scan}/escaneo · activado por defecto en repositorios nuevos: {'sí' if g_defecto else 'no'} "
               f"→ {600 * g_scan:.2f} USD/mes")
    OUT.append(f"AWS Inspector (ECR)       {ins_ini}/primer escaneo + {ins_re}/re-escaneo → {600 * ins_ini:.2f} USD/mes + re-escaneos")
    OUT.append(f"Oracle VSS                «Vulnerability Scanning Service {o_vss}»")
    OUT.append("```\n")
    (AQUI / "SALIDA-registro.md").write_text("\n".join(OUT), encoding="utf-8")
    print("\n".join(OUT))


if __name__ == "__main__":
    main()
