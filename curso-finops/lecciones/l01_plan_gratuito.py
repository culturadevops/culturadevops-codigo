# -*- coding: utf-8 -*-
"""Lección 1 · El plan gratuito ya no es un año: son créditos, y se gastan.

Lo que dice el anuncio oficial (citas literales en FUENTES.md) y lo que cuesta, a precio de lista,
lo que la gente se deja encendido. ¿Cuánto duran 200 USD de créditos con eso?
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import precios as PR  # noqa: E402

H = PR.HORAS_MES
print("\n== 1.1 · Lo que dice el anuncio (16 de julio de 2025) ==")
for l in (Path(__file__).resolve().parent.parent / "FUENTES.md").read_text(encoding="utf-8").splitlines():
    if l.startswith("- «") and ("credits" in l or "expires" in l or "always-free" in l):
        print("  " + l[2:])

print(f"\n== 1.2 · Lo que se deja encendido, al mes ({H} h), a precio de lista ==")
filas = [
    ("una instancia t3.micro", PR.P["t3_micro_hora"][0] * H),
    ("  y su IPv4 pública (también cobra)", PR.P["ipv4_en_uso_hora"][0] * H),
    ("un disco gp3 de 30 GB", 30 * PR.P["gp3_gb_mes"][0]),
    ("una instantánea de 30 GB", 30 * PR.P["snapshot_gb_mes"][0]),
    ("un NAT gateway (sin tráfico)", PR.P["nat_hora"][0] * H),
    ("  y la IP fija del NAT", PR.P["ipv4_en_uso_hora"][0] * H),
]
for nombre, c in filas:
    print(f"  {nombre:38s} {PR.usd(c):>12s}")
total = sum(c for _, c in filas)
print(f"  {'TOTAL':38s} {PR.usd(total):>12s}")

print("\n== 1.3 · ¿Cuánto duran los créditos? ==")
for creditos in (100, 200):
    print(f"  {creditos} USD de créditos / {PR.usd(total)} al mes = {creditos / total:.1f} meses")
nat = PR.P["nat_hora"][0] * H + PR.P["ipv4_en_uso_hora"][0] * H
print(f"  solo el NAT con su IP: {PR.usd(nat)} al mes, {nat / total * 100:.0f}% del total")
print(f"\n  precios: {PR.fuentes()}")
