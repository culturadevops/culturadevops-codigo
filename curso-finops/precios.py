# -*- coding: utf-8 -*-
"""Los precios del curso, leídos de la LISTA DE PRECIOS PÚBLICA de AWS (us-east-1), sin credenciales.

Los ficheros de `precios/` se descargaron de pricing.us-east-1.amazonaws.com (ver FUENTES.md) y
llevan su fecha de publicación. Ningún precio de este curso está escrito a mano: sale de aquí.
⚠️ Son precios de LISTA. La factura real lleva impuestos, descuentos y créditos: todo importe del
curso es una estimación «precio de lista × uso», y se dice.
"""
import json
from pathlib import Path

AQUI = Path(__file__).resolve().parent / "precios"
HORAS_MES = 730          # 365 × 24 / 12: un mes medio


def _ec2():
    d = json.loads((AQUI / "ec2-us-east-1.json").read_text(encoding="utf-8"))
    fecha = d["cabecera"][2].split(",")[1].strip('"')
    return {p["usageType"]: (float(p["PricePerUnit"]), p["Unit"], p["PriceDescription"]) for p in d["precios"]}, fecha


def _oferta(nombre):
    d = json.loads((AQUI / f"{nombre}-us-east-1.json").read_text(encoding="utf-8"))
    out = {}
    for sku, p in d["products"].items():
        ut = p["attributes"].get("usagetype", "")
        for t in d["terms"]["OnDemand"].get(sku, {}).values():
            for dim in t["priceDimensions"].values():
                if dim.get("beginRange", "0") == "0":
                    out[ut] = (float(dim["pricePerUnit"]["USD"]), dim["unit"], dim["description"])
    return out, d["publicationDate"]


EC2, FECHA_EC2 = _ec2()
VPC, FECHA_VPC = _oferta("AmazonVPC")
LAMBDA, FECHA_LAMBDA = _oferta("AWSLambda")

# Lo que usa el curso: (precio, unidad, descripción literal de AWS)
P = {
    "nat_hora": EC2["NatGateway-Hours"],
    "gp3_gb_mes": EC2["EBS:VolumeUsage.gp3"],
    "gp2_gb_mes": EC2["EBS:VolumeUsage.gp2"],
    "snapshot_gb_mes": EC2["EBS:SnapshotUsage"],
    "t3_micro_hora": EC2["BoxUsage:t3.micro"],
    "m7i_large_hora": EC2["BoxUsage:m7i.large"],
    "ipv4_libre_hora": VPC["USE1-PublicIPv4:IdleAddress"],
    "ipv4_en_uso_hora": VPC["USE1-PublicIPv4:InUseAddress"],
    "lambda_peticion": LAMBDA["Request"],
    "lambda_gb_segundo": LAMBDA["Lambda-GB-Second"],
}


def usd(x):
    return f"{x:,.2f} USD".replace(",", " ")


def fuentes():
    return (f"lista de precios pública de AWS, us-east-1 · EC2 {FECHA_EC2[:10]} · VPC {FECHA_VPC[:10]}"
            f" · Lambda {FECHA_LAMBDA[:10]}")
