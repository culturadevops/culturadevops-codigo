# -*- coding: utf-8 -*-
"""Vídeo 692 · La capa gratuita de AWS en 2026 — cuánto cuesta cada cosa a precio de lista y cuánto duran los créditos.

Todo precio sale de `lista.py` (lista de precios pública de AWS, us-east-1). Mes = 730 h. Los créditos y el plazo salen de
la documentación oficial (FUENTES.md): 100 USD al abrir la cuenta + hasta 100 USD por 5 actividades; el plan gratuito
termina a los 6 meses o cuando se acaban los créditos, lo que llegue antes.

    python calculo.py   (lo llama ejecutar_todo.py)
"""
import sys

from lista import H, MAQUINAS, bajar, uno, usd

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

EC2, VPC, RDS, ELB = bajar("AmazonEC2"), bajar("AmazonVPC"), bajar("AmazonRDS"), bajar("AWSELB")
DT, LAM = bajar("AWSDataTransfer"), bajar("AWSLambda")
PLAZO = 6  # meses del plan gratuito

P = {m: uno(EC2, usageType=f"BoxUsage:{m}") for m in MAQUINAS}
ip_uso = uno(VPC, usageType="USE1-PublicIPv4:InUseAddress")
ip_libre = uno(VPC, usageType="USE1-PublicIPv4:IdleAddress")
nat_h = uno(EC2, usageType="NatGateway-Hours")
nat_gb = uno(EC2, usageType="NatGateway-Bytes")
gp3 = uno(EC2, usageType="EBS:VolumeUsage.gp3")
snap = uno(EC2, usageType="EBS:SnapshotUsage")
alb = uno(ELB, usageType="LoadBalancerUsage")
rds = uno(RDS, usageType="InstanceUsage:db.t4g.micro")
rds_gb = uno(RDS, usageType="RDS:GP3-Storage")
salida = uno(DT, usageType="DataTransfer-Out-Bytes", PriceDescription__tiene="first 10 TB")
salida_gratis = uno(DT, usageType="Global-DataTransfer-Out-Bytes")
lam_req_gratis = uno(LAM, usageType="Global-Request")
lam_gbs_gratis = uno(LAM, usageType="Global-Lambda-GB-Second")


def mes(p):
    return p[0] * H


IPV4_GRATIS = 750  # h/mes de IPv4 pública con EC2 sin costo para clientes de la capa gratuita (guía de VPC)


def ipv4(n):
    """IPv4 públicas encendidas todo el mes, descontando las 750 h gratis (en el mejor caso: contadas todas juntas)."""
    return max(0, n * H - IPV4_GRATIS) * ip_uso[0]


def duracion(creditos, al_mes):
    """Meses que duran los créditos a ese ritmo, con el tope de 6 meses del plan gratuito."""
    m = creditos / al_mes
    return min(m, PLAZO), m


print("== 1 · Las máquinas «Free tier eligible» de una cuenta nueva, a precio de lista (Linux, bajo demanda) ==")
for m in MAQUINAS:
    print(f"  {m:<16} {P[m][0]:.5f} USD/h   {mes(P[m]):6.2f} USD/mes   «{P[m][1]}»")
print(f"  la más cara se come 200 USD en {200 / mes(P['m7i-flex.large']):.1f} meses; la más barata, en "
      f"{200 / mes(P['t4g.micro']):.1f}")
print()

print("== 2 · Lo que se cobra por hora aunque no lo uses (us-east-1) ==")
filas = [("IPv4 pública en uso", ip_uso), ("IPv4 pública sin usar", ip_libre), ("NAT gateway, por hora", nat_h),
         ("Balanceador de aplicaciones (ALB)", alb)]
for t, p in filas:
    print(f"  {t:<36} {p[0]:.4f} USD/h   {mes(p):6.2f} USD/mes   «{p[1]}»")
print(f"  {'Disco gp3, por GB':<36} {gp3[0]:.3f} USD/GB-mes  30 GB: {30 * gp3[0]:.2f} USD/mes   «{gp3[1]}»")
print(f"  {'Instantánea (snapshot), por GB':<36} {snap[0]:.3f} USD/GB-mes  30 GB: {30 * snap[0]:.2f} USD/mes")
print(f"  {'NAT gateway, por GB procesado':<36} {nat_gb[0]:.3f} USD/GB")
print(f"  {'Salida a internet (tras lo gratis)':<36} {salida[0]:.3f} USD/GB   «{salida[1]}»")
print(f"  IPv4: {IPV4_GRATIS} h/mes gratis con EC2 → 1 IP todo el mes ({H} h): {ipv4(1):.2f} USD · 2 IP: {ipv4(2):.2f} USD"
      f" · 3 IP: {ipv4(3):.2f} USD")
print()
print("== 3 · Lo que es gratis siempre (lista de precios, a 0 USD) ==")
for p in (salida_gratis, lam_req_gratis, lam_gbs_gratis):
    print(f"  {p[0]:.0f} USD · «{p[1]}»")
print()

ESC = {
    "A · aprender: 1 t3.micro + su IPv4 + disco de 30 GB": [
        ("t3.micro 24/7", mes(P["t3.micro"])), ("IPv4 pública (dentro de las 750 h)", ipv4(1)), ("disco gp3 30 GB", 30 * gp3[0])],
    "B · web con base de datos: t3.small + RDS db.t4g.micro": [
        ("t3.small 24/7", mes(P["t3.small"])), ("IPv4 pública (dentro de las 750 h)", ipv4(1)), ("disco gp3 30 GB", 30 * gp3[0]),
        ("RDS PostgreSQL db.t4g.micro", mes(rds)), ("RDS disco gp3 20 GB", 20 * rds_gb[0])],
    "C · la de un tutorial: B + NAT gateway + balanceador": [
        ("t3.small 24/7", mes(P["t3.small"])), ("disco gp3 30 GB", 30 * gp3[0]),
        ("RDS PostgreSQL db.t4g.micro", mes(rds)), ("RDS disco gp3 20 GB", 20 * rds_gb[0]),
        ("NAT gateway (sin tráfico)", mes(nat_h)), ("2 IPv4 (máquina + NAT) − 750 h", ipv4(2)),
        ("ALB (sin tráfico ni sus IP)", mes(alb))],
    "D · la grande «elegible»: m7i-flex.large + IPv4 + 30 GB": [
        ("m7i-flex.large 24/7", mes(P["m7i-flex.large"])), ("IPv4 pública (dentro de las 750 h)", ipv4(1)), ("disco gp3 30 GB", 30 * gp3[0])],
}
print("== 4 · ¿Cuánto duran los créditos? (encendido 24/7, precio de lista, tope del plan: 6 meses) ==")
TOT = {}
for nombre, partes in ESC.items():
    tot = sum(v for _, v in partes)
    TOT[nombre] = tot
    print(f"  {nombre}")
    for t, v in partes:
        print(f"      {t:<36} {v:6.2f} USD/mes")
    print(f"      {'TOTAL':<36} {tot:6.2f} USD/mes   ({tot / H * 24:.2f} USD/día)")
    for c in (100, 200):
        tope, libre = duracion(c, tot)
        dias = c / (tot / H * 24)
        if libre >= PLAZO:
            sobra = c - tot * PLAZO
            print(f"      {c} USD: alcanzan {libre:.1f} meses → manda el plazo: a los 6 meses sobran {sobra:.2f} USD")
        else:
            print(f"      {c} USD: se acaban en {libre:.1f} meses (día {dias:.0f})")
print()

c_nat = mes(nat_h) + ipv4(2)
print("== 5 · El peso del NAT en el escenario C ==")
print(f"  NAT + la IPv4 de más: {c_nat:.2f} USD/mes de {TOT[list(ESC)[2]]:.2f}: {100 * c_nat / TOT[list(ESC)[2]]:.0f} %")
print(f"  con 1 GB/día por el NAT: +{30 * nat_gb[0]:.2f} USD/mes")
print()
print(f"  precios: lista pública de AWS us-east-1 · EC2 {EC2['publicacion'][:10]} · VPC {VPC['publicacion'][:10]} · "
      f"RDS {RDS['publicacion'][:10]} · ELB {ELB['publicacion'][:10]} · DataTransfer {DT['publicacion'][:10]} · "
      f"Lambda {LAM['publicacion'][:10]}")
