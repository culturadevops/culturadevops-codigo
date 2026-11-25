# -*- coding: utf-8 -*-
"""Banco de precios: guardar secretos (contraseñas, claves de API) en 4 nubes, de fuentes OFICIALES (sin cuenta).
  · AWS Secrets Manager y Systems Manager Parameter Store: listas públicas us-east-1 (AWSSecretsManager, AWSSystemsManager).
  · Azure Key Vault (Standard): Retail Prices API, eastus.
  · Google Secret Manager: página oficial cloud.google.com/secret-manager/pricing.
  · Oracle OCI Vault: lista de precios oficial (oracle.com/cloud/price-list): «Secrets on Oracle Cloud Infrastructure Vault — Free».
Escenarios: 20 secretos y 100.000 lecturas al mes; 200 secretos y 10 millones de lecturas al mes.
    python secretos.py   -> SALIDA-secretos.md
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


def bajar(url, nombre):
    p = CACHE / nombre
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/130.0"})
    p.write_bytes(urllib.request.urlopen(req, timeout=300).read())
    return p


def filas(p):
    f = open(p, encoding="utf-8")
    cab = [next(f) for _ in range(5)]
    pub = next(l for l in cab if "Publication Date" in l).split(",")[1].strip().strip('"')
    return pub, list(csv.DictReader(f))


def aws():
    pub, sm = filas(bajar("https://pricing.us-east-1.amazonaws.com/offers/v1.0/aws/AWSSecretsManager/current/us-east-1/index.csv", "sm.csv"))
    por_secreto = next(float(r["PricePerUnit"]) for r in sm if r["Unit"] == "Secrets")
    por_llamada = next(float(r["PricePerUnit"]) for r in sm if r["Unit"] == "API Requests")
    _, ssm = filas(bajar("https://pricing.us-east-1.amazonaws.com/offers/v1.0/aws/AWSSystemsManager/current/us-east-1/index.csv", "ssm.csv"))
    avanzado = next(float(r["PricePerUnit"]) for r in ssm if "per Advanced Parameter per Month" in r["PriceDescription"])
    alto = next(r for r in ssm if r["PriceDescription"].startswith("$0.05 per 10,") and "Parameter" in r["PriceDescription"])
    estandar = [r["PriceDescription"] for r in ssm if "Standard Parameter" in r["PriceDescription"]]
    _, kms = filas(bajar("https://pricing.us-east-1.amazonaws.com/offers/v1.0/aws/awskms/current/us-east-1/index.csv", "kms.csv"))
    kms_gratis = next(float(r["EndingRange"]) for r in kms if "Free Tier for KMS requests" in r["PriceDescription"])
    kms_10k = next(float(r["PricePerUnit"]) * 10000 for r in kms if r["PriceDescription"].startswith("$0.03 per 10000 KMS requests"))
    return pub, {"kms_gratis": kms_gratis, "kms_10k": kms_10k, "secreto": por_secreto, "llamada": por_llamada, "avanzado_mes": avanzado * H,
                 "alto": float(alto["PricePerUnit"]), "alto_desc": alto["PriceDescription"], "estandar": estandar}


def azure():
    url = "https://prices.azure.com/api/retail/prices?$filter=" + urllib.parse.quote(
        "serviceName eq 'Key Vault' and armRegionName eq 'eastus' and skuName eq 'Standard' and priceType eq 'Consumption'")
    items = json.load(urllib.request.urlopen(url, timeout=120))["Items"]
    ops = next(i["retailPrice"] for i in items if i["meterName"] == "Operations")
    medidores = sorted({i["meterName"] for i in items})
    return {"ops10k": ops, "medidores": medidores}


def google():
    s = bajar("https://cloud.google.com/secret-manager/pricing", "gcpsm.html").read_text(encoding="utf-8")
    t = re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", " ", s)))
    m = re.search(r"Active secret versions 0 month to ([0-9]+) month \$0\.00 \(Free\).*?and above \$([0-9.]+) / 1 hour", t)
    a = re.search(r"Access operations 0 count to ([0-9,]+) count \$0\.00 \(Free\).*?and above \$([0-9.]+) / 10,000 count", t)
    return {"versiones_gratis": int(m.group(1)), "version_h": float(m.group(2)),
            "lecturas_gratis": int(a.group(1).replace(",", "")), "lectura10k": float(a.group(2))}


def oracle():
    s = bajar("https://www.oracle.com/cloud/networking/pricing/", "ocinet.html").read_text(encoding="utf-8", errors="replace")
    t = re.sub(r"<script.*?</script>|<style.*?</style>", "", s, flags=re.S)
    t = re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", " ", t)))
    m = re.search(r"Secrets on Oracle Cloud Infrastructure Vault (\S+)", t)
    k = re.search(r"Vault - Software protected Keys (\S+)", t)
    return {"secretos": m.group(1), "claves_software": k.group(1)}


def main():
    pub, a = aws()
    z, g, o = azure(), google(), oracle()
    OUT.append(f"# SALIDA — secretos en 4 nubes\n\nGenerado {datetime.now(timezone.utc):%Y-%m-%d %H:%M} UTC con `python secretos.py`. "
               f"Precios de lista en USD, sin impuestos.\n")
    OUT.append("## Las tarifas\n\n```")
    OUT.append(f"AWS Secrets Manager   {a['secreto']} por secreto al mes + {a['llamada'] * 10000:.2f} por 10.000 llamadas   (lista us-east-1 {pub})")
    OUT.append(f"AWS Parameter Store   avanzado {a['avanzado_mes']:.2f} por parámetro al mes · «{a['alto_desc'][:60]}…» "
               f"· líneas de «Standard Parameter» en la lista: {len(a['estandar'])}")
    OUT.append(f"AWS KMS               {a['kms_10k']:.2f} por 10.000 peticiones (primeras {a['kms_gratis']:,.0f} al mes gratis) — "
               "cada lectura de un SecureString de Parameter Store descifra con KMS")
    OUT.append(f"Azure Key Vault       {z['ops10k']} por 10.000 operaciones · medidores Standard: {', '.join(z['medidores'])}")
    OUT.append(f"Google Secret Manager versiones activas: {g['versiones_gratis']} gratis, después {g['version_h']}/h "
               f"(= {g['version_h'] * H:.4f} al mes) · lecturas: {g['lecturas_gratis']:,} gratis, después {g['lectura10k']} por 10.000")
    OUT.append(f"Oracle OCI Vault      secretos: {o['secretos']} · claves por software: {o['claves_software']}")
    OUT.append("```\n")

    def costes(n, lecturas):
        return [("AWS Secrets Manager", n * a["secreto"] + lecturas * a["llamada"]),
                ("AWS Parameter Store (estándar, texto plano)", 0.0),
                ("AWS Parameter Store (estándar, SecureString + KMS)", max(0, lecturas - a["kms_gratis"]) / 10000 * a["kms_10k"]),
                ("AWS Parameter Store (avanzado + alto rendimiento, sin KMS)", n * a["avanzado_mes"] + lecturas / 10000 * a["alto"]),
                ("Azure Key Vault", lecturas / 10000 * z["ops10k"]),
                ("Google Secret Manager", max(0, n - g["versiones_gratis"]) * g["version_h"] * H
                 + max(0, lecturas - g["lecturas_gratis"]) / 10000 * g["lectura10k"]),
                ("Oracle OCI Vault", 0.0)]

    for n, lecturas in ((20, 100_000), (200, 10_000_000)):
        OUT.append(f"## {n} secretos, {lecturas:,} lecturas al mes\n\n```")
        for nombre, c in sorted(costes(n, lecturas), key=lambda x: x[1]):
            OUT.append(f"{nombre:<58} {c:>8.2f} USD/mes")
        OUT.append("```\n")
    OUT.append("## Lo que cuesta solo TENER los secretos (sin leerlos), al mes\n\n```")
    for n in (1, 20, 200):
        OUT.append(f"{n:>4} secretos → AWS Secrets Manager {n * a['secreto']:>6.2f} · Google {max(0, n - g['versiones_gratis']) * g['version_h'] * H:>6.2f} "
                   f"· Azure 0.00 · Oracle 0.00")
    OUT.append("```\n")
    # ── claves de cifrado propias (la otra mitad del tema): 10 claves simétricas y 1 millón de operaciones al mes
    _, kms = filas(CACHE / "kms.csv")
    kms_clave = next(float(r["PricePerUnit"]) for r in kms if "per customer managed KMS key version" in r["PriceDescription"])
    t = re.sub(r"\s+", " ", html.unescape(bajar("https://cloud.google.com/kms/pricing", "gcpkms.html").read_text(encoding="utf-8")))
    m = re.search(r'Active symmetric AES-256 and HMAC key versions.*?"\$([0-9.]+) / 1 month".*?"\$([0-9.]+) / 1 month".*?"\$([0-9.]+) / 1 month"', t)
    g_soft, g_hsm, g_ext = map(float, m.groups())
    url = "https://prices.azure.com/api/retail/prices?$filter=" + urllib.parse.quote(
        "serviceName eq 'Key Vault' and armRegionName eq 'eastus' and priceType eq 'Consumption'")
    kv = json.load(urllib.request.urlopen(url, timeout=120))["Items"]
    az_hsm_rsa = next(i["retailPrice"] for i in kv if i["meterName"] == "Premium HSM-protected RSA 2048-bit key")
    az_rot = next(i["retailPrice"] for i in kv if i["meterName"] == "Automated Key Rotation" and i["skuName"] == "Standard")
    oj = json.loads((CACHE / "oracle.json").read_text(encoding="utf-8"))["items"] if (CACHE / "oracle.json").exists() else \
        json.loads(bajar("https://apexapps.oracle.com/pls/apex/cetools/api/v1/products/?currencyCode=USD", "oracle.json").read_text(encoding="utf-8"))["items"]
    o_hsm = next(i for i in oj if i["partNumber"] == "B92092")["currencyCodeLocalizations"][0]["prices"]
    o_hsm_gratis = next(x["rangeMax"] for x in o_hsm if x["value"] == 0)
    o_hsm_precio = next(x["value"] for x in o_hsm if x["value"] > 0)
    o_privada = next(i for i in oj if i["partNumber"] == "B90328")["currencyCodeLocalizations"][0]["prices"][0]["value"]
    az_ded = next(i["retailPrice"] for i in kv if i["productName"] == "Azure Dedicated HSM")
    OUT.append("## Claves de cifrado propias: las tarifas\n\n```")
    OUT.append(f"AWS KMS      {kms_clave} por versión de clave al mes + {a['kms_10k']:.2f} por 10.000 operaciones ({a['kms_gratis']:,.0f} gratis)")
    OUT.append(f"Azure        claves por software: solo operaciones ({z['ops10k']} por 10.000) · HSM RSA 2048 (Premium) {az_hsm_rsa} al mes · "
               f"rotación automática {az_rot} por rotación")
    OUT.append(f"Google KMS   versión de clave simétrica: software {g_soft} · HSM {g_hsm} · externa {g_ext} al mes · operaciones 0.03 por 10.000")
    OUT.append(f"Oracle       claves por software: {o['claves_software']} · HSM: {o_hsm_gratis} versiones gratis, después {o_hsm_precio} al mes")
    OUT.append("```\n")
    ops = 1_000_000
    claves = [("AWS KMS", 10 * kms_clave + max(0, ops - a["kms_gratis"]) / 10000 * a["kms_10k"]),
              ("Azure Key Vault (claves por software)", ops / 10000 * z["ops10k"]),
              ("Google Cloud KMS (software)", 10 * g_soft + ops / 10000 * 0.03),
              ("Oracle Vault (software o HSM, dentro de las 20 gratis)", 0.0)]
    OUT.append(f"## 10 claves simétricas y {ops:,} operaciones al mes\n\n```")
    for n, c in sorted(claves, key=lambda x: x[1]):
        OUT.append(f"{n:<58} {c:>8.2f} USD/mes")
    OUT.append("```\n")
    OUT.append("## Un HSM dedicado para ti solo (cuando el cumplimiento lo exige)\n\n```")
    OUT.append(f"Oracle  bóveda privada virtual   {o_privada}/h → {o_privada * H:,.2f} USD/mes")
    OUT.append(f"Azure   Dedicated HSM            {az_ded}/h → {az_ded * H:,.2f} USD/mes")
    OUT.append("```\n")
    (AQUI / "SALIDA-secretos.md").write_text("\n".join(OUT), encoding="utf-8")
    print("\n".join(OUT))


if __name__ == "__main__":
    main()
