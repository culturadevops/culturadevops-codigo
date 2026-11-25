# -*- coding: utf-8 -*-
"""Banco de precios: el NAT Gateway en 4 nubes, sacado de las fuentes OFICIALES (sin cuenta).
  · AWS: lista pública AmazonEC2 us-east-1 (NAT: por hora + por GB procesado) y AmazonVPC (IPv4 pública por hora).
  · Azure: Retail Prices API — NAT Gateway (Global, Standard) y Standard IPv4 Static Public IP en eastus.
  · Google Cloud NAT: página oficial cloud.google.com/nat/pricing (por VM hasta 32, por GiB, por IP).
  · Oracle: lista de precios oficial (oracle.com/cloud/price-list) — no tiene línea para el NAT gateway; salida a internet
    gratis los primeros 10 TB/mes desde Norteamérica.
Escenarios: 3 máquinas privadas, 1 IP, y 100 GB · 1 TB · 5 TB al mes pasando por el NAT. Mes = 730 h.
    python nat.py   -> SALIDA-nat.md
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
H = 730
OUT = []


def bajar(url, nombre, refrescar=True):
    p = CACHE / nombre
    if refrescar or not p.exists():
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/130.0"})
        p.write_bytes(urllib.request.urlopen(req, timeout=600).read())
    return p


def aws():
    p = bajar("https://pricing.us-east-1.amazonaws.com/offers/v1.0/aws/AmazonEC2/current/us-east-1/index.csv", "ec2.csv")
    f = open(p, encoding="utf-8")
    cab = [next(f) for _ in range(5)]
    pub = next(l for l in cab if "Publication Date" in l).split(",")[1].strip().strip('"')
    hora = gb = None
    for r in csv.DictReader(f):
        d = r["PriceDescription"]
        if d == "$0.045 per NAT Gateway Hour" or (r["Unit"] == "Hrs" and "per NAT Gateway Hour" in d):
            hora = float(r["PricePerUnit"])
        if r["Unit"] == "GB" and d.startswith("$") and "per GB Data Processed by NAT Gateways" in d and "Provisioned" not in d:
            gb = float(r["PricePerUnit"])
    v = bajar("https://pricing.us-east-1.amazonaws.com/offers/v1.0/aws/AmazonVPC/current/us-east-1/index.csv", "vpc.csv")
    ip = next(float(r["PricePerUnit"]) for r in csv.DictReader(l for i, l in enumerate(open(v, encoding="utf-8")) if i >= 5)
              if "per In-use public IPv4 address per hour" in r["PriceDescription"])
    return pub, hora, gb, ip


def azure():
    def q(f):
        url = "https://prices.azure.com/api/retail/prices?$filter=" + urllib.parse.quote(f)
        rows = []
        while url:
            d = json.load(urllib.request.urlopen(url, timeout=120))
            rows += d["Items"]
            url = d.get("NextPageLink")
        return rows
    nat = q("serviceName eq 'NAT Gateway' and armRegionName eq 'Global' and skuName eq 'Standard'")
    hora = next(i["retailPrice"] for i in nat if i["meterName"] == "Standard Gateway")
    gb = next(i["retailPrice"] for i in nat if i["meterName"] == "Standard Data Processed")
    ip = next(i["retailPrice"] for i in q("serviceName eq 'Virtual Network' and armRegionName eq 'eastus' and "
                                          "meterName eq 'Standard IPv4 Static Public IP'"))
    return hora, gb, ip


def google():
    s = bajar("https://cloud.google.com/nat/pricing", "gcpnat.html").read_text(encoding="utf-8")
    t = re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", " ", s)))
    m = re.search(r"Up to 32 VM instances \$([0-9.]+) \* the number of VM instances that are using the gateway \$([0-9.]+) \$([0-9.]+) "
                  r"More than 32 VM instances \$([0-9.]+)", t)
    por_vm, gb, ip, tope = map(float, m.groups())
    return por_vm, gb, ip, tope


def oracle():
    s = bajar("https://www.oracle.com/cloud/networking/pricing/", "ocinet.html").read_text(encoding="utf-8", errors="replace")
    t = re.sub(r"<script.*?</script>|<style.*?</style>", "", s, flags=re.S)
    t = re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", " ", t)))
    nat = len(re.findall(r"\bNAT\b", t))
    gratis = "Outbound Data Transfer - Originating in North America, Europe, and UK - First 10 TB / Month Free" in t
    return nat, gratis


def main():
    pub, ah, ag, aip = aws()
    zh, zg, zip_ = azure()
    gvm, gg, gip, gtope = google()
    onat, ogratis = oracle()
    OUT.append(f"# SALIDA — el NAT Gateway en 4 nubes\n\nGenerado {datetime.now(timezone.utc):%Y-%m-%d %H:%M} UTC con `python nat.py`. "
               f"Mes = {H} h. Precios de lista en USD, sin impuestos.\n")
    OUT.append("## Las tarifas\n\n```")
    OUT.append(f"AWS     NAT {ah}/h + {ag}/GB procesado + IPv4 pública {aip}/h   (lista EC2 us-east-1 publicada {pub})")
    OUT.append(f"Azure   NAT {zh}/h + {zg}/GB procesado + IP Standard {zip_}/h   (Retail Prices API)")
    OUT.append(f"Google  {gvm}/h por máquina (hasta 32; desde 33: {gtope}/h fijo) + {gg}/GiB + IP {gip}/h   (cloud.google.com/nat/pricing)")
    OUT.append(f"Oracle  menciones de «NAT» en su lista de precios: {onat} · salida a internet 10 TB/mes gratis: {'sí' if ogratis else 'no'}")
    OUT.append("```\n")
    vms = 3
    for gbmes in (100, 1000, 5000):
        filas = [("AWS", ah * H, ag * gbmes, aip * H), ("Azure", zh * H, zg * gbmes, zip_ * H),
                 ("Google", (gvm * vms if vms <= 32 else gtope) * H, gg * gbmes, gip * H), ("Oracle", 0.0, 0.0, 0.0)]
        OUT.append(f"## {vms} máquinas privadas, 1 IP, {gbmes} GB al mes por el NAT\n\n```\n{'nube':<8} {'pasarela':>9} {'datos':>9} {'IP':>7} {'TOTAL/mes':>10}")
        for n, p, d, i in sorted(filas, key=lambda x: sum(x[1:])):
            OUT.append(f"{n:<8} {p:>9.2f} {d:>9.2f} {i:>7.2f} {p + d + i:>10.2f}")
        OUT.append("```\n")
    OUT.append("## Google con muchas máquinas: el cobro por máquina tiene tope\n\n```")
    for n in (1, 3, 10, 32, 33, 100):
        OUT.append(f"{n:>3} máquinas → pasarela {(gvm * n if n <= 32 else gtope) * H:>6.2f} USD/mes")
    OUT.append(f"AWS y Azure, cualquier número de máquinas → {ah * H:.2f} USD/mes por pasarela\n```\n")
    # ── en AWS: NAT con ancho de banda reservado, y un NAT hecho con una máquina pequeña (de la misma lista EC2)
    f = open(CACHE / "ec2.csv", encoding="utf-8")
    [next(f) for _ in range(5)]
    gbps = nano = None
    for r in csv.DictReader(f):
        if r["Unit"] == "Gbps-hrs" and "NAT Gateways with Provisioned Bandwidth" in r["PriceDescription"]:
            gbps = float(r["PricePerUnit"])
        if (r.get("Instance Type") == "t4g.nano" and r["TermType"] == "OnDemand" and r.get("Operating System") == "Linux"
                and r.get("Tenancy") == "Shared" and r.get("Pre Installed S/W") == "NA" and r.get("CapacityStatus") == "Used"):
            nano = float(r["PricePerUnit"])
    f = open(CACHE / "ec2.csv", encoding="utf-8")
    [next(f) for _ in range(5)]
    tipos = sorted({(r["usageType"], r["PriceDescription"][:62]) for r in csv.DictReader(f) if "NAT Gateway" in r["PriceDescription"]})
    OUT.append("## AWS: cómo se llama cada cobro del NAT en la factura (usageType)\n\n```")
    OUT.extend(f"{u:<32} {d}" for u, d in tipos)
    OUT.append("```\n")
    OUT.append("## AWS: NAT con ancho de banda reservado (0 USD por GB procesado)\n\n```")
    OUT.append(f"{gbps} USD por Gbps-hora → 1 Gbps reservado: {gbps * H:.2f} USD/mes")
    OUT.append(f"punto de equilibrio con el NAT normal: {gbps * H / ag:,.0f} GB al mes ({gbps * H / ag / 1000:.1f} TB)\n```\n")
    OUT.append("## AWS: un NAT hecho con una máquina t4g.nano (la mantienes tú)\n\n```")
    OUT.append(f"t4g.nano Linux a demanda {nano}/h → {nano * H:.2f} USD/mes + IPv4 {aip * H:.2f} = {(nano + aip) * H:.2f} USD/mes, sin cobro por GB procesado")
    for gbmes in (100, 1000, 5000):
        OUT.append(f"{gbmes:>5} GB/mes → NAT gestionado {ah * H + ag * gbmes + aip * H:>7.2f} · máquina propia {(nano + aip) * H:>6.2f} USD/mes")
    OUT.append("```\n")
    (AQUI / "SALIDA-nat.md").write_text("\n".join(OUT), encoding="utf-8")
    print("\n".join(OUT))


if __name__ == "__main__":
    main()
