# -*- coding: utf-8 -*-
"""Banco de precios: colas de mensajes en 4 nubes, de fuentes OFICIALES (sin cuenta).
  · AWS SQS: lista pública AWSQueueService us-east-1 (estándar y FIFO por tramos; primer millón gratis al mes).
  · Azure: Retail Prices API eastus — Service Bus (Basic, Standard con base mensual y tramos) y Storage Queues (Queues v1 y v2).
  · Google Pub/Sub: página oficial cloud.google.com/pubsub/pricing (40 USD por TiB de throughput, 10 GiB gratis, mínimo 1 KB).
  · Oracle OCI Queue: API pública de precios (primer millón de peticiones gratis, después por millón).
MODELO (para comparar lo mismo): mensajes de 1 KB; cada mensaje = 3 peticiones (enviar, recibir y borrar/confirmar) en
SQS, Service Bus, Storage Queues y OCI Queue. En Pub/Sub se paga por bytes: publicar + entregar a 1 suscripción = 2 KB.
    python colas.py   -> SALIDA-colas.md
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
M = 1_000_000


def bajar(url, nombre):
    p = CACHE / nombre
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/130.0"})
    p.write_bytes(urllib.request.urlopen(req, timeout=300).read())
    return p


def tramos_coste(n, tramos):
    """tramos: [(desde, hasta, precio_por_unidad)]"""
    total = 0.0
    for a, b, precio in tramos:
        if n > a:
            total += (min(n, b) - a) * precio
    return total


def aws():
    p = bajar("https://pricing.us-east-1.amazonaws.com/offers/v1.0/aws/AWSQueueService/current/us-east-1/index.csv", "sqs.csv")
    f = open(p, encoding="utf-8")
    cab = [next(f) for _ in range(5)]
    pub = next(l for l in cab if "Publication Date" in l).split(",")[1].strip().strip('"')
    est, fifo, gratis = [], [], 0
    for r in csv.DictReader(f):
        d = r["PriceDescription"]
        a, b = float(r["StartingRange"] or 0), float("inf") if r["EndingRange"] == "Inf" else float(r["EndingRange"])
        if "are free" in d:
            gratis = b
        elif "standard requests" in d and "N Virginia" in d:
            est.append((a, b, float(r["PricePerUnit"])))
        elif "FIFO requests" in d and "N Virginia" in d:
            fifo.append((a, b, float(r["PricePerUnit"])))
    return pub, gratis, sorted(est), sorted(fifo)


def azure():
    def q(f):
        url = "https://prices.azure.com/api/retail/prices?$filter=" + urllib.parse.quote(f)
        rows = []
        while url:
            d = json.load(urllib.request.urlopen(url, timeout=120))
            rows += d["Items"]
            url = d.get("NextPageLink")
        return rows
    sb = q("serviceName eq 'Service Bus' and armRegionName eq 'eastus' and priceType eq 'Consumption'")
    base = next(i["retailPrice"] for i in sb if i["meterName"] == "Standard Base Unit" and i["unitOfMeasure"] == "1/Month")
    ops = sorted((i["tierMinimumUnits"] * M, i["retailPrice"] / M) for i in sb if i["meterName"] == "Standard Messaging Operations")
    std = [(ops[k][0], ops[k + 1][0] if k + 1 < len(ops) else float("inf"), ops[k][1]) for k in range(len(ops))]
    basic = next(i["retailPrice"] for i in sb if i["meterName"] == "Basic Messaging Operations") / M
    # Las cuentas v1 («Queues») se retiraron el 13-10-2026 (learn.microsoft.com, storage-account-upgrade): vale el precio de v2.
    sq = q("serviceName eq 'Storage' and armRegionName eq 'eastus' and productName eq 'Queues v2' and skuName eq 'Standard LRS' "
           "and priceType eq 'Consumption'")
    sq1 = next(i["retailPrice"] for i in sq if i["meterName"] == "LRS Class 1 Operations") / 10000
    sq2 = next(i["retailPrice"] for i in sq if i["meterName"] == "Class 2 Operations") / 10000
    return base, std, basic, sq1, sq2


def google():
    s = bajar("https://cloud.google.com/pubsub/pricing", "gcpps.html").read_text(encoding="utf-8")
    t = re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", " ", s)))
    gratis = float(re.search(r"the first ([0-9]+) GiB of throughput identified as the Message Delivery Basic SKU", t).group(1))
    tib = float(re.search(r"After that, the price is \$([0-9.]+) per TiB", t).group(1))
    minimo = "A minimum of 1 KB is assessed for each request" in t
    global G_ALMACEN
    G_ALMACEN = float(re.search(r"Storage costs of \$([0-9.]+) per GiB-month", t).group(1))
    return gratis, tib, minimo


def oracle():
    p = bajar("https://apexapps.oracle.com/pls/apex/cetools/api/v1/products/?currencyCode=USD", "oracle.json")
    it = next(i for i in json.loads(p.read_text(encoding="utf-8"))["items"] if i["partNumber"] == "B95697")
    fr = it["currencyCodeLocalizations"][0]["prices"]
    gratis = next(x["rangeMax"] for x in fr if x["value"] == 0) * M
    precio = next(x["value"] for x in fr if x["value"] > 0) / M
    return gratis, precio


def main():
    pub, a_gratis, a_est, a_fifo = aws()
    z_base, z_std, z_basic, z_sq1, z_sq2 = azure()
    g_gratis, g_tib, g_min = google()
    o_gratis, o_precio = oracle()
    OUT.append(f"# SALIDA — colas de mensajes en 4 nubes\n\nGenerado {datetime.now(timezone.utc):%Y-%m-%d %H:%M} UTC con `python colas.py`. "
               "Mensajes de 1 KB; 3 peticiones por mensaje (enviar, recibir, borrar) salvo Pub/Sub (2 KB de throughput por mensaje).\n")
    OUT.append("## Las tarifas\n\n```")
    OUT.append(f"AWS SQS        {a_gratis / M:.0f} M peticiones gratis al mes · estándar " +
               " · ".join(f"{p * M:.2f}/M" for _, _, p in a_est) + " · FIFO " + " · ".join(f"{p * M:.2f}/M" for _, _, p in a_fifo) +
               f"   (lista us-east-1 {pub})")
    OUT.append(f"Azure Bus Std  {z_base} USD al mes de base · operaciones: " +
               " · ".join(f"desde {x / M:,.0f} M: {p * M:.2f}/M" for x, _, p in z_std))
    OUT.append(f"Azure Bus Basic {z_basic * M:.2f}/M operaciones, sin base")
    OUT.append(f"Azure Storage Queues (v2, LRS) {z_sq1 * M:.3f}/M operaciones de escritura · {z_sq2 * M:.3f}/M de lectura "
               "(las cuentas v1 se retiraron el 13-10-2026)")
    OUT.append(f"Google Pub/Sub {g_tib} USD por TiB de throughput · {g_gratis:.0f} GiB gratis al mes · mínimo 1 KB por petición: {'sí' if g_min else 'no'}")
    OUT.append(f"Oracle Queue   {o_gratis / M:.0f} M peticiones gratis al mes · después {o_precio * M:.2f}/M")
    OUT.append(f"Pub/Sub, guardar mensajes ya confirmados o instantáneas: {G_ALMACEN} USD por GiB al mes")
    OUT.append("```\n")

    for mens in (1 * M, 100 * M, 1000 * M):
        pet = 3 * mens
        gib = 2 * mens * 1024 / 2 ** 30                          # 2 KB por mensaje, en GiB
        filas = [("AWS SQS estándar", tramos_coste(max(0, pet - a_gratis), a_est)),
                 ("AWS SQS FIFO", tramos_coste(max(0, pet - a_gratis), a_fifo)),
                 ("AWS SQS estándar, en lotes de 10", tramos_coste(max(0, pet / 10 - a_gratis), a_est)),
                 ("Azure Service Bus Standard", z_base + tramos_coste(pet, z_std)),
                 ("Azure Service Bus Basic", pet * z_basic),
                 ("Azure Storage Queues", mens * z_sq1 + 2 * mens * z_sq2),   # enviar = escritura; recibir y borrar = 2 más
                 ("Google Pub/Sub", max(0, gib - g_gratis) / 1024 * g_tib),
                 ("Oracle Queue", max(0, pet - o_gratis) * o_precio)]
        OUT.append(f"## {mens / M:,.0f} millones de mensajes al mes ({pet / M:,.0f} M peticiones · {gib:,.1f} GiB en Pub/Sub)\n\n```")
        for n, c in sorted(filas, key=lambda x: x[1]):
            OUT.append(f"{n:<34} {c:>10,.2f} USD/mes")
        OUT.append("```\n")
    OUT.append("## Pub/Sub: el mínimo de 1 KB por petición, y agrupar\n\n```")
    for por_peticion in (1, 10, 100):
        kb = max(1, por_peticion * 0.1)                           # mensajes de 100 bytes agrupados
        OUT.append(f"100 M mensajes de 100 bytes, {por_peticion:>3} por petición → se cobran {kb:.1f} KB por petición "
                   f"→ {max(0, (100 * M / por_peticion) * kb * 1024 * 2 / 2 ** 30 - g_gratis) / 1024 * g_tib:>8.2f} USD/mes")
    OUT.append("```\n")
    # ── mensajes grandes: SQS cobra cada fragmento de 64 KB como una petición (página de precios de AWS); Pub/Sub, por bytes
    OUT.append("## Mensajes grandes: 10 M mensajes de 256 KB al mes\n\n```")
    fr = 256 // 64                                             # fragmentos de 64 KB por mensaje
    pet_g = 10 * M * (fr + fr + 1)                             # enviar y recibir se cobran por fragmento; borrar, 1
    gib_g = 10 * M * 256 * 1024 * 2 / 2 ** 30
    OUT.append(f"AWS SQS estándar   {fr} fragmentos de 64 KB → {pet_g / M:,.0f} M peticiones → {tramos_coste(max(0, pet_g - a_gratis), a_est):>8,.2f} USD/mes")
    OUT.append(f"Google Pub/Sub     {gib_g:,.1f} GiB de throughput → {max(0, gib_g - g_gratis) / 1024 * g_tib:>8,.2f} USD/mes")
    OUT.append("```\n")
    # ── SQS: una cola VACÍA también cuesta si se consulta sin parar (sondeo corto) — 10 trabajadores, 30 días
    seg_mes = 30 * 24 * 3600
    OUT.append("## SQS: 10 trabajadores consultando una cola vacía, 30 días\n\n```")
    for etiqueta, por_seg in (("sondeo corto, 10 consultas/s cada uno", 10), ("sondeo corto, 1 consulta/s cada uno", 1),
                              ("sondeo largo de 20 s (el máximo)", 1 / 20)):
        pet = 10 * por_seg * seg_mes
        OUT.append(f"{etiqueta:<40} {pet / M:>8,.1f} M peticiones → {tramos_coste(max(0, pet - a_gratis), a_est):>7.2f} USD/mes")
    OUT.append("```\n")
    # ── Pub/Sub con varias suscripciones: cada entrega se cobra
    OUT.append("## Pub/Sub: 100 M mensajes de 1 KB entregados a N suscripciones\n\n```")
    for subs in (1, 3, 5):
        gib = (1 + subs) * 100 * M * 1024 / 2 ** 30
        OUT.append(f"{subs} suscripción(es) → {gib:>7.1f} GiB → {max(0, gib - g_gratis) / 1024 * g_tib:>6.2f} USD/mes")
    OUT.append("```\n")
    # ── Azure Service Bus: el plan Premium y las conexiones del Standard
    sb = json.load(urllib.request.urlopen("https://prices.azure.com/api/retail/prices?$filter=" + urllib.parse.quote(
        "serviceName eq 'Service Bus' and armRegionName eq 'eastus' and priceType eq 'Consumption'"), timeout=120))["Items"]
    prem = next(i["retailPrice"] for i in sb if i["meterName"] == "Premium Messaging Unit")
    con = sorted((i["tierMinimumUnits"], i["retailPrice"]) for i in sb if i["meterName"] == "Standard Brokered Connection")
    OUT.append("## Azure Service Bus: Premium y conexiones del Standard\n\n```")
    OUT.append(f"Premium: {prem}/h por unidad de mensajería → {prem * 730:,.2f} USD/mes por unidad (730 h)")
    OUT.append("Standard, conexiones: " + " · ".join(f"desde {int(a):,}: {p}" for a, p in con) + " USD por conexión")
    OUT.append("```\n")
    (AQUI / "SALIDA-colas.md").write_text("\n".join(OUT), encoding="utf-8")
    print("\n".join(OUT))


if __name__ == "__main__":
    main()
