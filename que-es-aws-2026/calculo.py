# -*- coding: utf-8 -*-
"""Vídeo 693 · ¿Qué es AWS? — regiones de la lista de precios y pago por uso con precios reales.

Los precios salen de ../capa-gratuita-aws-2026/lista.py (lista de precios pública de AWS, sin cuenta). Mes = 730 h.
    python calculo.py   (lo llama ejecutar_todo.py)
"""
import json
import re
import sys
import urllib.request
from pathlib import Path

AQUI = Path(__file__).resolve().parent
sys.path.insert(0, str(AQUI.parent / "capa-gratuita-aws-2026"))
from lista import BASE, H, bajar, uno  # noqa: E402

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
REFRESCAR = "--refrescar" in sys.argv

# ── Regiones: el índice de regiones de la oferta de EC2 ──
ri = AQUI / "precios" / "AmazonEC2-region_index.json"
ri.parent.mkdir(exist_ok=True)
if REFRESCAR or not ri.exists():
    ri.write_bytes(urllib.request.urlopen(f"{BASE}/AmazonEC2/current/region_index.json", timeout=120).read())
idx = json.loads(ri.read_text(encoding="utf-8"))
codigos = sorted(idx["regions"])
regiones = [c for c in codigos if re.fullmatch(r"[a-z]{2}(-gov)?-[a-z]+-\d+", c)]
gov = [c for c in regiones if "-gov-" in c]
print(f"== 1 · Regiones en la lista de precios de EC2 (region_index.json, publicado {idx['publicationDate'][:10]}) ==")
print(f"  códigos en el índice: {len(codigos)}")
print(f"  con forma de región (xx-nombre-N): {len(regiones)} · de ellas GovCloud: {len(gov)} · comerciales: {len(regiones) - len(gov)}")
resto = [c for c in codigos if c not in regiones]
print(f"  el resto ({len(resto)}) cuelga de una región (zonas locales y Wavelength), p. ej.: {', '.join(resto[:4])}…")
latam = [c for c in regiones if c.startswith(("sa-", "mx-"))]
print(f"  en Latinoamérica: {', '.join(latam)}")
print()

# ── Pago por uso, tres regiones ──
REG = {"us-east-1": "Virginia del Norte", "mx-central-1": "México (Central)", "sa-east-1": "São Paulo"}
PFX = {"us-east-1": "", "mx-central-1": "MXC1-", "sa-east-1": "SAE1-"}
print("== 2 · La misma máquina y el mismo GB, en tres regiones (Linux bajo demanda · S3 Standard) ==")
base = None
for r, nom in REG.items():
    ec2, s3 = bajar("AmazonEC2", r), bajar("AmazonS3", r)
    t3 = uno(ec2, usageType=f"{PFX[r]}BoxUsage:t3.micro")
    gb = uno(s3, usageType__fin="TimedStorage-ByteHrs")
    base = base or t3[0]
    print(f"  {r:<13} {nom:<20} t3.micro {t3[0]:.4f} USD/h = {t3[0] * H:5.2f} USD/mes ({100 * t3[0] / base - 100:+.0f} %)"
          f" · S3 {gb[0]:.4f} USD/GB-mes   «{t3[1]}»")
print(f"  publicación: EC2 {bajar('AmazonEC2', 'sa-east-1')['publicacion'][:10]} · S3 {bajar('AmazonS3')['publicacion'][:10]}")
print()

EC2, VPC, S3 = bajar("AmazonEC2"), bajar("AmazonVPC"), bajar("AmazonS3")
RDS, LAM, DT = bajar("AmazonRDS"), bajar("AWSLambda"), bajar("AWSDataTransfer")
t3 = uno(EC2, usageType="BoxUsage:t3.micro")[0]
ip = uno(VPC, usageType="USE1-PublicIPv4:InUseAddress")[0]
gp3 = uno(EC2, usageType="EBS:VolumeUsage.gp3")[0]
s3 = uno(S3, usageType="TimedStorage-ByteHrs")[0]
rds = uno(RDS, usageType="InstanceUsage:db.t4g.micro")[0]
req = uno(LAM, usageType="Request")[0]
gbs = uno(LAM, usageType="Lambda-GB-Second", PriceDescription__fin="Tier-1")[0]
salida = uno(DT, usageType="DataTransfer-Out-Bytes", PriceDescription__tiene="first 10 TB")[0]

print("== 3 · Pagar por uso: la misma t3.micro, según cuánto la tengas encendida (us-east-1) ==")
for t, horas in (("10 minutos", 10 / 60), ("1 hora", 1), ("8 h × 22 días laborables", 8 * 22), ("todo el mes (730 h)", H)):
    print(f"  {t:<26} {t3 * horas:8.4f} USD")
print("  (Linux se cobra por segundo, con un mínimo de 60 s: página de precios bajo demanda de EC2)")
print()

print("== 4 · Lambda: se paga por petición y por GB-segundo; el primer millón es gratis cada mes ==")
for n, mb, ms in ((1_000_000, 128, 200), (5_000_000, 512, 300)):
    gs = n * mb / 1024 * ms / 1000
    costo = max(0, n - 1_000_000) * req + max(0, gs - 400_000) * gbs
    print(f"  {n:>9,} peticiones · {mb} MB · {ms} ms → {gs:>9,.0f} GB-s → {costo:5.2f} USD/mes")
print(f"  precio: {req * 1e6:.2f} USD por millón de peticiones · {gbs:.10f} USD por GB-s")
print()

print("== 5 · Lo básico de cada servicio, a precio de lista (us-east-1) ==")
for t, v in (("EC2 t3.micro, el mes", t3 * H), ("IPv4 pública, el mes", ip * H), ("disco gp3, por GB-mes", gp3),
             ("S3 Standard, por GB-mes", s3), ("RDS PostgreSQL db.t4g.micro, el mes", rds * H),
             ("Salida a internet, por GB (tras 100 GB gratis)", salida), ("IAM y VPC (la red en sí)", 0.0)):
    print(f"  {t:<48} {v:7.3f} USD")
print("  (IAM no tiene oferta en la lista de precios: la guía de IAM dice «no additional charge». La guía de VPC: «There's no "
      "additional charge for using a VPC»; sí cobran cosas dentro, como el NAT o las IPv4)")
print()

pp = [("t3.micro 24/7", t3 * H), ("su IPv4 pública", ip * H), ("disco gp3 de 8 GB", 8 * gp3), ("S3: 5 GB", 5 * s3),
      ("salida: 20 GB (dentro de los 100 gratis)", 0.0)]
print("== 6 · Un primer proyecto, al mes (us-east-1, precio normal, sin contar la capa gratuita) ==")
for t, v in pp:
    print(f"  {t:<42} {v:6.2f} USD")
print(f"  {'TOTAL':<42} {sum(v for _, v in pp):6.2f} USD")
print()
print(f"  precios: lista pública de AWS · EC2 {EC2['publicacion'][:10]} · VPC {VPC['publicacion'][:10]} · S3 "
      f"{S3['publicacion'][:10]} · RDS {RDS['publicacion'][:10]} · Lambda {LAM['publicacion'][:10]} · DataTransfer "
      f"{DT['publicacion'][:10]}")
