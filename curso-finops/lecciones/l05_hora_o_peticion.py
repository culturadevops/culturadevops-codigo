# -*- coding: utf-8 -*-
"""Lección 5 · Pagar por hora o pagar por petición: la decisión que más dinero mueve.

Una API pequeña en una t3.micro encendida todo el mes (con su IPv4 pública), contra la misma API
en Lambda. Supuestos, dichos: 128 MB de memoria, 100 ms por petición, sin el cupo gratuito de
Lambda (se enseña aparte). ¿A partir de cuántas peticiones al mes sale más cara Lambda?
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import precios as PR  # noqa: E402

H = PR.HORAS_MES
MEM_GB, SEG = 128 / 1024, 0.1
servidor = (PR.P["t3_micro_hora"][0] + PR.P["ipv4_en_uso_hora"][0]) * H
por_millon = 1e6 * (PR.P["lambda_peticion"][0] + SEG * MEM_GB * PR.P["lambda_gb_segundo"][0])

print("\n== 5.1 · Los dos precios ==")
print(f"  t3.micro + IPv4, todo el mes:            {PR.usd(servidor):>10s}  (pase lo que pase)")
print(f"  Lambda, 128 MB y 100 ms, por millón:     {PR.usd(por_millon):>10s}  (si no hay peticiones, 0)")

print("\n== 5.2 · Al mes, según el tráfico ==")
print(f"  {'peticiones/mes':>16s} {'Lambda':>12s} {'t3.micro':>12s}  más barato")
for m in (0.1, 1, 10, 25, 50, 100):
    l = m * por_millon
    print(f"  {m * 1e6:>16,.0f} {PR.usd(l):>12s} {PR.usd(servidor):>12s}  {'Lambda' if l < servidor else 't3.micro'}".replace(",", "."))

corte = servidor / por_millon
print(f"\n== 5.3 · El punto de corte ==")
print(f"  {corte:.1f} millones de peticiones al mes = {corte * 1e6 / (H * 3600):.1f} peticiones por segundo de media")
print("  el cupo gratuito de Lambda: «The free tier includes one million requests and 400,000 GB-seconds per month.»")
print(f"\n  precios: {PR.fuentes()}")
