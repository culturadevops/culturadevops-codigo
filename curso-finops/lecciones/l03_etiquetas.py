# -*- coding: utf-8 -*-
"""Lección 3 · Etiquetar: lo único que contesta «¿de quién es este gasto?».

Una cuenta con tres proyectos. Unos recursos llevan la etiqueta Proyecto y otros no, que es lo
normal. El cazador reparte el coste por proyecto: lo que no tiene dueño es la pregunta que nadie
sabe contestar el día que llega la factura.
"""
import sys
from collections import defaultdict
from pathlib import Path

import boto3
from moto import mock_aws

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import cazador as CZ  # noqa: E402
import precios as PR  # noqa: E402


def tags(p):
    return [{"ResourceType": r, "Tags": [{"Key": "Proyecto", "Value": p}]} for r in ("instance", "volume")] if p else []


with mock_aws():
    ec2 = boto3.client("ec2", region_name="us-east-1")
    ami = ec2.describe_images(Owners=["amazon"])["Images"][0]["ImageId"]
    for proyecto, tipo, n in (("tienda", "m7i.large", 2), ("blog", "t3.micro", 1), (None, "t3.micro", 2), (None, "m7i.large", 1)):
        ec2.run_instances(ImageId=ami, InstanceType=tipo, MinCount=n, MaxCount=n, TagSpecifications=tags(proyecto))
    ec2.create_volume(AvailabilityZone="us-east-1a", Size=200, VolumeType="gp3")              # «el de las pruebas»
    ec2.allocate_address(Domain="vpc")

    print("\n== 3.1 · El coste, por proyecto ==")
    por = defaultdict(float)
    for tipo, rid, det, dueno, coste in CZ.cazar(ec2):
        por[dueno] += coste
    total = sum(por.values())
    for dueno, c in sorted(por.items(), key=lambda x: -x[1]):
        print(f"  {dueno:16s} {PR.usd(c):>12s}/mes  {c / total * 100:5.1f}%")
    print(f"  {'TOTAL':16s} {PR.usd(total):>12s}/mes")

    print("\n== 3.2 · Los que no tienen dueño ==")
    for tipo, rid, det, dueno, coste in CZ.cazar(ec2):
        if dueno == "(sin etiqueta)":
            print(f"  {tipo:12s} {rid:24s} {det[:30]:30s} {PR.usd(coste):>10s}/mes")

print("\n== 3.3 · Y la letra pequeña: etiquetar no basta ==")
for l in (Path(__file__).resolve().parent.parent / "FUENTES.md").read_text(encoding="utf-8").splitlines():
    if l.startswith("- «") and ("activate them" in l or "24 hours" in l):
        print("  " + l[2:])
