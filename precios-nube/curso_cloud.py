# -*- coding: utf-8 -*-
"""Banco de precios del «Curso de cloud computing desde cero» (cultura-devops, parte 3), de fuentes OFICIALES y sin cuenta.
  · AWS EC2 (lista pública us-east-1, la misma caché ec2.csv de la serie «¿Dónde es más barato?»): t3.micro y t4g.micro, Linux,
    bajo demanda, tenencia compartida; y la salida de datos a internet (primer tramo).
  · AWS S3 (lista pública us-east-1): almacenamiento Standard, primer tramo, por GB-mes.
  · Azure: Retail Prices API — Virtual Machines B1s Linux, eastus, pago por uso.
Mes = 730 h.
    python curso_cloud.py   -> SALIDA-curso-cloud.md
"""
import csv
import json
import urllib.parse
import urllib.request
from datetime import datetime, timezone

from nat import bajar  # misma descarga y caché

H = 730
OUT = []


def w(t=""):
    OUT.append(t)
    print(t)


def ec2():
    p = bajar("https://pricing.us-east-1.amazonaws.com/offers/v1.0/aws/AmazonEC2/current/us-east-1/index.csv", "ec2.csv", refrescar=False)
    f = open(p, encoding="utf-8")
    cab = [next(f) for _ in range(5)]
    pub = next(l for l in cab if "Publication Date" in l).split(",")[1].strip().strip('"')
    maq, salida = {}, []
    for r in csv.DictReader(f):
        if (r.get("Instance Type") in ("t3.micro", "t4g.micro") and r["TermType"] == "OnDemand" and r["Operating System"] == "Linux"
                and r["Tenancy"] == "Shared" and r["Pre Installed S/W"] == "NA" and r["CapacityStatus"] == "Used"
                and r["Unit"] == "Hrs" and r["Location"] == "US East (N. Virginia)"):
            maq[r["Instance Type"]] = (float(r["PricePerUnit"]), r["PriceDescription"], r["vCPU"], r["Memory"])
        if r.get("Transfer Type") == "AWS Outbound" and r["Unit"] == "GB" and "first 10 TB" in r["PriceDescription"]:
            salida.append((float(r["PricePerUnit"]), r["PriceDescription"]))
    return pub, maq, salida


def s3():
    p = bajar("https://pricing.us-east-1.amazonaws.com/offers/v1.0/aws/AmazonS3/current/us-east-1/index.csv", "s3.csv")
    f = open(p, encoding="utf-8")
    cab = [next(f) for _ in range(5)]
    pub = next(l for l in cab if "Publication Date" in l).split(",")[1].strip().strip('"')
    for r in csv.DictReader(f):
        if (r["Location"] == "US East (N. Virginia)" and r.get("Volume Type") == "Standard" and r["Unit"] == "GB-Mo"
                and r["StartingRange"] == "0" and r["TermType"] == "OnDemand"):
            return pub, float(r["PricePerUnit"]), r["PriceDescription"]


def azure():
    f = ("serviceName eq 'Virtual Machines' and armRegionName eq 'eastus' and armSkuName eq 'Standard_B1s' "
         "and priceType eq 'Consumption'")
    url = "https://prices.azure.com/api/retail/prices?$filter=" + urllib.parse.quote(f)
    filas = []
    while url:
        d = json.load(urllib.request.urlopen(url, timeout=120))
        filas += d["Items"]
        url = d.get("NextPageLink")
    lin = [i for i in filas if "Windows" not in i["productName"] and "Spot" not in i["skuName"] and "Low Priority" not in i["skuName"]]
    i = lin[0]
    return i["retailPrice"], i["productName"], i["skuName"], i["effectiveStartDate"]


pub, maq, salida = ec2()
s3pub, s3gb, s3desc = s3()
az, azprod, azsku, azdesde = azure()
w("# SALIDA — precios del curso de cloud computing (fuentes oficiales)")
w()
w(f"> Corrida del {datetime.now(timezone.utc):%Y-%m-%d %H:%M} UTC. Regenerable con `python curso_cloud.py`. Mes = {H} h.")
w()
w(f"## AWS EC2 · us-east-1 · Linux bajo demanda (lista pública, publicada {pub})")
w()
w("| máquina | vCPU | memoria | USD/hora | USD/mes |")
w("|---|---|---|---|---|")
for k in ("t3.micro", "t4g.micro"):
    pr, desc, cpu, mem = maq[k]
    w(f"| {k} | {cpu} | {mem} | {pr:.4f} | {pr * H:.2f} |")
w()
dt = bajar("https://pricing.us-east-1.amazonaws.com/offers/v1.0/aws/AWSDataTransfer/current/us-east-1/index.csv", "datatransfer.csv",
           refrescar=False)
fdt = open(dt, encoding="utf-8")
cabdt = [next(fdt) for _ in range(5)]
pubdt = next(l for l in cabdt if "Publication Date" in l).split(",")[1].strip().strip('"')
tramos = sorted({(float(r["StartingRange"]), float(r["PricePerUnit"]), r["PriceDescription"]) for r in csv.DictReader(fdt)
                 if r["From Location"] == "US East (N. Virginia)" and r["To Location Type"] == "Other"
                 and r["Transfer Type"] == "AWS Outbound" and r["Unit"] == "GB"})
w(f"Salida de datos a internet desde us-east-1 (lista AWSDataTransfer, publicada {pubdt}):")
for ini, pr, d in tramos[:3]:
    w(f"- {pr} USD/GB · «{d}»")
pr1 = tramos[0][1]
w(f"- 100 GB fuera del tramo gratis: {100 * pr1:.2f} USD · 1 TB (1.024 GB): {1024 * pr1:.2f} USD")
w()
w(f"## AWS S3 · us-east-1 · Standard (lista pública, publicada {s3pub})")
w()
w(f"- {s3gb} USD por GB-mes · «{s3desc}»")
w(f"- 100 GB: {100 * s3gb:.2f} USD/mes · 1 TB (1.024 GB): {1024 * s3gb:.2f} USD/mes")
w()
w("## Azure · eastus · B1s Linux, pago por uso (Retail Prices API)")
w()
w(f"- {az} USD/hora · {az * H:.2f} USD/mes · {azprod} · {azsku} · vigente desde {azdesde[:10]}")
w()
(__import__("pathlib").Path(__file__).parent / "SALIDA-curso-cloud.md").write_text("\n".join(OUT) + "\n", encoding="utf-8")
