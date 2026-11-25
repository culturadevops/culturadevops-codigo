# -*- coding: utf-8 -*-
"""Banco de precios: Postgres gestionado en 4 nubes (2 vCPU, 8 GB, 100 GB SSD), sacado de las fuentes OFICIALES.
  · AWS RDS: lista pública de precios (pricing.us-east-1.amazonaws.com, AmazonRDS us-east-1, CSV), db.m6i.large.
  · Azure Database for PostgreSQL Flexible Server: Retail Prices API (prices.azure.com), eastus, D2ds v5 (2 vCore).
  · Google Cloud SQL Enterprise: página oficial cloud.google.com/sql/pricing (región por defecto: Iowa, us-central1).
  · OCI Database with PostgreSQL: API pública de precios de Oracle (apexapps.oracle.com/.../cetools/api/v1/products).
Sin cuenta en ninguna nube. Un mes = 730 horas (la convención de las calculadoras).
    python postgres.py   -> SALIDA-postgres.md
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
GB = 100
OUT = []


def bajar(url, nombre):
    p = CACHE / nombre
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    p.write_bytes(urllib.request.urlopen(req, timeout=300).read())
    return p


def aws():
    p = bajar("https://pricing.us-east-1.amazonaws.com/offers/v1.0/aws/AmazonRDS/current/us-east-1/index.csv", "rds.csv")
    f = open(p, encoding="utf-8")
    cab = [next(f) for _ in range(5)]
    pub = next(l for l in cab if "Publication Date" in l).split(",")[1].strip().strip('"')
    r = {}
    for row in csv.DictReader(f):
        if row.get("Database Engine") != "PostgreSQL":
            continue
        if row.get("Instance Type") == "db.m6i.large" and row["Unit"] == "Hrs":
            k = (row["Deployment Option"], row["TermType"], row["LeaseContractLength"], row["PurchaseOption"])
            r[k] = float(row["PricePerUnit"])
        if row.get("Volume Type") == "General Purpose-GP3" and row["Unit"] == "GB-Mo" and row.get("Product Family") == "Database Storage":
            r[("gp3", row["Deployment Option"])] = float(row["PricePerUnit"])
    return pub, {
        "hora": r[("Single-AZ", "OnDemand", "", "")], "hora_ha": r[("Multi-AZ", "OnDemand", "", "")],
        "hora_1a": r[("Single-AZ", "Reserved", "1yr", "No Upfront")],
        "gb": r[("gp3", "Single-AZ")], "gb_ha": r[("gp3", "Multi-AZ")]}


def azure():
    def q(f):
        url = "https://prices.azure.com/api/retail/prices?$filter=" + urllib.parse.quote(f)
        rows = []
        while url:
            d = json.load(urllib.request.urlopen(url, timeout=120))
            rows += d["Items"]
            url = d.get("NextPageLink")
        return rows
    comp = q("armRegionName eq 'eastus' and productName eq 'Azure Database for PostgreSQL Flexible Server General Purpose Ddsv5 Series Compute'")
    hora = next(i["retailPrice"] for i in comp if i["skuName"] == "2 vCore" and i["type"] == "Consumption")
    res1 = next(i["retailPrice"] for i in comp if i["type"] == "Reservation" and i.get("reservationTerm") == "1 Year")
    alm = q("armRegionName eq 'eastus' and productName eq 'Azure Database for PostgreSQL Flex Server Storage' and skuName eq 'Storage'")
    gb = next(i["retailPrice"] for i in alm if i["type"] == "Consumption")
    # la reserva viene por vCore y por todo el plazo: a hora, ÷ 8.760 h (365 días)
    return {"hora": hora, "hora_ha": hora * 2, "hora_1a": 2 * res1 / 8760, "gb": gb, "gb_ha": gb * 2}


def google():
    p = bajar("https://cloud.google.com/sql/pricing", "cloudsql.html")
    s = p.read_text(encoding="utf-8")
    region = re.search(r'jsname="Fb0Bif">([^<]+)<', s).group(1)
    t = re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", " ", s)))
    num = r"\$([0-9.]+) / 1 (?:hour|gibibyte hour)"
    m = re.search(r"vCPUs " + num + " " + num + " " + num + r" Memory " + num + " " + num + " " + num +
                  r" HA vCPUs " + num + " " + num + " " + num + r" HA Memory " + num, t)
    v, v1, v3, mem, mem1, mem3, hv, hv1, hv3, hmem = map(float, m.groups())
    ssd = [float(x) for x in re.findall(r"SSD storage capacity \$([0-9.]+) / 1 gibibyte hour", t)]
    return region, {"hora": 2 * v + 8 * mem, "hora_ha": 2 * hv + 8 * hmem, "hora_1a": 2 * v1 + 8 * mem1,
                    "gb": ssd[0] * H, "gb_ha": max(ssd) * H, "v": v, "mem": mem}


def oracle():
    p = bajar("https://apexapps.oracle.com/pls/apex/cetools/api/v1/products/?currencyCode=USD", "oracle.json")
    d = {i["partNumber"]: i["currencyCodeLocalizations"][0]["prices"][0]["value"] for i in json.loads(p.read_text(encoding="utf-8"))["items"]}
    fee, ocpu, mem, opt, blk = d["B99060"], d["B97384"], d["B97385"], d["B99062"], d["B91961"]
    # 1 OCPU = 2 vCPU. Su página: «se suma una tarifa a tu cómputo y almacenamiento estándar».
    hora = fee + ocpu + 8 * mem
    return {"hora": hora, "hora_ha": 2 * hora, "hora_1a": None, "gb": opt + blk, "gb_ha": opt + blk,
            "partes": (fee, ocpu, mem, opt, blk)}


def main():
    pub, a = aws()
    z = azure()
    reg, g = google()
    o = oracle()
    OUT.append(f"# SALIDA — Postgres gestionado en 4 nubes\n\nGenerado {datetime.now(timezone.utc):%Y-%m-%d %H:%M} UTC con "
               f"`python postgres.py`. 2 vCPU, 8 GB, {GB} GB SSD; mes = {H} h. Precios de lista en USD, sin impuestos.\n")
    OUT.append("## Fuentes y región\n")
    OUT.append(f"- AWS RDS · us-east-1 (Virginia) · db.m6i.large · lista oficial publicada {pub}")
    OUT.append("- Azure PostgreSQL Flexible · eastus (Virginia) · General Purpose D2ds v5 · Retail Prices API")
    OUT.append(f"- Google Cloud SQL Enterprise · {reg} (región por defecto de su página) · 2 vCPU + 8 GiB")
    fee, ocpu, mem, opt, blk = o["partes"]
    OUT.append(f"- Oracle OCI Database with PostgreSQL · 1 OCPU (= 2 vCPU) + 8 GB · API de precios. Partes: tarifa PostgreSQL "
               f"{fee}/OCPU-h + cómputo E5 {ocpu}/OCPU-h + memoria {mem}/GB-h; almacenamiento optimizado {opt} + bloque {blk} USD/GB-mes\n")

    def fila(n, x, ha=False):
        h = x["hora_ha"] if ha else x["hora"]
        gbm = x["gb_ha"] if ha else x["gb"]
        return n, h, h * H, gbm * GB, h * H + gbm * GB

    for titulo, ha in (("Un servidor (sin alta disponibilidad)", False), ("Con alta disponibilidad (réplica en espera)", True)):
        OUT.append(f"## {titulo}\n\n```\n{'nube':<8} {'USD/hora':>9} {'cómputo/mes':>12} {'disco/mes':>10} {'TOTAL/mes':>10}")
        filas = sorted((fila(n, x, ha) for n, x in (("AWS", a), ("Azure", z), ("Google", g), ("Oracle", o))), key=lambda f: f[4])
        for n, h, c, d, t in filas:
            OUT.append(f"{n:<8} {h:>9.4f} {c:>12.2f} {d:>10.2f} {t:>10.2f}")
        caros = [f[0] for f in filas if round(f[4], 2) == round(filas[-1][4], 2)]
        OUT.append(f"```\nmás barato: {filas[0][0]} · más caro: {' y '.join(caros)}{' (empate)' if len(caros) > 1 else ''} · "
                   f"diferencia {filas[-1][4] - filas[0][4]:.2f} USD/mes ({(filas[-1][4] / filas[0][4] - 1) * 100:.0f} % más)\n")
    OUT.append("## Con compromiso de 1 año (solo el cómputo, por hora)\n\n```")
    OUT.append(f"AWS     reserva 1 año sin pago inicial      {a['hora_1a']:.4f}  (a demanda {a['hora']:.4f}, -{(1 - a['hora_1a'] / a['hora']) * 100:.0f} %)")
    OUT.append(f"Azure   reserva 1 año (por vCore, ÷8.760 h) {z['hora_1a']:.4f}  (a demanda {z['hora']:.4f}, -{(1 - z['hora_1a'] / z['hora']) * 100:.0f} %)")
    OUT.append(f"Google  compromiso de uso 1 año             {g['hora_1a']:.4f}  (a demanda {g['hora']:.4f}, -{(1 - g['hora_1a'] / g['hora']) * 100:.0f} %)")
    OUT.append("Oracle  sin precio de compromiso en la API  —\n```\n")
    OUT.append("## Total al mes con compromiso de 1 año (un servidor, cómputo + disco; Oracle a demanda)\n\n```")
    tot = sorted(((n, (x["hora_1a"] or x["hora"]) * H + x["gb"] * GB) for n, x in (("AWS", a), ("Azure", z), ("Google", g), ("Oracle", o))),
                 key=lambda f: f[1])
    for n, t in tot:
        OUT.append(f"{n:<8} {t:>8.2f}")
    OUT.append("```\n")
    # ── un segundo tamaño: 4 vCPU, 16 GB y 500 GB de disco (base de datos con más datos)
    f = open(CACHE / "rds.csv", encoding="utf-8")
    [next(f) for _ in range(5)]
    aws_xl = next(float(r["PricePerUnit"]) for r in csv.DictReader(f)
                  if r.get("Instance Type") == "db.m6i.xlarge" and r.get("Database Engine") == "PostgreSQL"
                  and r["Unit"] == "Hrs" and r["TermType"] == "OnDemand" and r["Deployment Option"] == "Single-AZ")
    comp = json.load(urllib.request.urlopen("https://prices.azure.com/api/retail/prices?$filter=" + urllib.parse.quote(
        "armRegionName eq 'eastus' and productName eq 'Azure Database for PostgreSQL Flexible Server General Purpose Ddsv5 Series Compute' "
        "and skuName eq '4 vCore' and priceType eq 'Consumption'"), timeout=120))["Items"]
    az_4 = comp[0]["retailPrice"]
    fee, ocpu, mem, opt, blk = o["partes"]
    G2 = 500
    grande = [("AWS · db.m6i.xlarge", aws_xl, a["gb"]), ("Azure · D4ds v5 (4 vCore)", az_4, z["gb"]),
              ("Google · 4 vCPU + 16 GiB", 4 * g["v"] + 16 * g["mem"], g["gb"]), ("Oracle · 2 OCPU + 16 GB", 2 * (fee + ocpu) + 16 * mem, opt + blk)]
    OUT.append(f"## Otro tamaño: 4 vCPU, 16 GB y {G2} GB de disco (un servidor, a demanda)\n\n```\n"
               f"{'nube':<28} {'USD/hora':>9} {'cómputo/mes':>12} {'disco/mes':>10} {'TOTAL/mes':>10}")
    for n, h, gb in sorted(grande, key=lambda x: x[1] * H + x[2] * G2):
        OUT.append(f"{n:<28} {h:>9.4f} {h * H:>12.2f} {gb * G2:>10.2f} {h * H + gb * G2:>10.2f}")
    OUT.append("```\n")
    # ── las formas de reservar en AWS (db.m6i.large, Single-AZ): pago inicial + por hora
    f = open(CACHE / "rds.csv", encoding="utf-8")
    [next(f) for _ in range(5)]
    res = {}
    for r in csv.DictReader(f):
        if (r.get("Instance Type") == "db.m6i.large" and r.get("Database Engine") == "PostgreSQL" and r["Deployment Option"] == "Single-AZ"
                and r["TermType"] == "Reserved"):
            k = (r["LeaseContractLength"], r["PurchaseOption"])
            res.setdefault(k, [0.0, 0.0])[0 if r["Unit"] == "Quantity" else 1] = float(r["PricePerUnit"])
    OUT.append("## AWS: las formas de reservar db.m6i.large (pago inicial + por hora → equivale a)\n\n```")
    for (plazo, forma), (ini, hora) in sorted(res.items()):
        horas = 8760 * (1 if plazo == "1yr" else 3)
        OUT.append(f"{plazo} {forma:<16} inicial {ini:>7.0f} USD + {hora:.4f}/h  → {(ini + hora * horas) / horas * H:>7.2f} USD/mes")
    OUT.append(f"a demanda                                         → {a['hora'] * H:>7.2f} USD/mes\n```\n")
    # ── el cobro por usar una versión vieja de Postgres en RDS (Extended Support)
    f = open(CACHE / "rds.csv", encoding="utf-8")
    [next(f) for _ in range(5)]
    ext = {}
    for r in csv.DictReader(f):
        if r.get("Extended Support Pricing Year") and r.get("Database Engine") == "PostgreSQL":
            ext.setdefault((r["Extended Support Pricing Year"], float(r["PricePerUnit"])), set()).add(r["Engine Major Version"])
    OUT.append("## AWS RDS Extended Support (Postgres que ya no tiene soporte normal)\n\n```")
    for (anio, precio), vers in sorted(ext.items()):
        OUT.append(f"{anio:<15} {precio:.2f} USD por vCPU-hora · versiones {', '.join(sorted(vers, key=int))} "
                   f"→ 2 vCPU: {precio * 2 * H:.2f} USD/mes extra")
    OUT.append(f"el servidor db.m6i.large a demanda: {a['hora'] * H:.2f} USD/mes\n```\n")
    (AQUI / "SALIDA-postgres.md").write_text("\n".join(OUT), encoding="utf-8")
    print("\n".join(OUT))


if __name__ == "__main__":
    main()
