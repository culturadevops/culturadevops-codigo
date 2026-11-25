# -*- coding: utf-8 -*-
"""cazador.py — lo que sigue cobrando cuando crees que lo borraste todo.

Recorre la cuenta (una región) y apunta lo que cobra por estar, se use o no:
  · discos (EBS) sin instancia            · instantáneas (snapshots)
  · IPs públicas reservadas sin usar      · NAT gateways
  · instancias encendidas, y su IP pública (también cobra)
Pone precio mensual a cada cosa con la lista de precios pública (precios.py) y sale con 0 si no
hay nada que cobre, o con 1 si lo hay. Se programa a diario, como una copia.

    python cazador.py [--endpoint http://127.0.0.1:5000] [--etiqueta Proyecto]
"""
import argparse
import sys

import boto3

import precios as PR

H = PR.HORAS_MES


def cliente(endpoint=None):
    kw = {"region_name": "us-east-1"}
    if endpoint:
        kw.update(endpoint_url=endpoint, aws_access_key_id="prueba", aws_secret_access_key="prueba")
    return boto3.client("ec2", **kw)


def etiqueta(recurso, clave):
    return next((t["Value"] for t in recurso.get("Tags", []) if t["Key"] == clave), "(sin etiqueta)")


def cazar(ec2, clave="Proyecto"):
    """Devuelve [(tipo, id, detalle, dueño, usd_mes)]."""
    out = []
    fijas = {a["PublicIp"] for a in ec2.describe_addresses()["Addresses"]}
    # AWS desasocia la IP fija al terminar la instancia; moto no: se mira el estado de la instancia.
    vivas = {i["InstanceId"] for r in ec2.describe_instances()["Reservations"] for i in r["Instances"]
             if i["State"]["Name"] in ("running", "stopped", "pending")}
    for r in ec2.describe_instances(Filters=[{"Name": "instance-state-name", "Values": ["running", "stopped"]}])["Reservations"]:
        for i in r["Instances"]:
            tipo = i["InstanceType"]
            clave_precio = {"t3.micro": "t3_micro_hora", "m7i.large": "m7i_large_hora"}.get(tipo)
            coste = PR.P[clave_precio][0] * H if (clave_precio and i["State"]["Name"] == "running") else 0.0
            out.append(("instancia", i["InstanceId"], f"{tipo} {i['State']['Name']}", etiqueta(i, clave), coste))
            # La IP pública que da AWS al arrancar también cobra (las IPs fijas se cuentan abajo).
            if i.get("PublicIpAddress") and i["PublicIpAddress"] not in fijas:
                out.append(("IPv4 pública", i["PublicIpAddress"], f"en uso por {i['InstanceId']}", etiqueta(i, clave),
                            PR.P["ipv4_en_uso_hora"][0] * H))
    for v in ec2.describe_volumes()["Volumes"]:
        suelto = v["State"] == "available"
        det = "sin instancia" if suelto else f"en {v['Attachments'][0]['InstanceId']}" if v.get("Attachments") else v["State"]
        out.append(("disco suelto" if suelto else "disco", v["VolumeId"], f"{v['Size']} GB {v['VolumeType']}, {det}",
                    etiqueta(v, clave), v["Size"] * PR.P[f"{v['VolumeType']}_gb_mes" if v["VolumeType"] in ("gp2", "gp3") else "gp3_gb_mes"][0]))
    # Una instantánea que respalda una imagen (AMI) registrada no está huérfana: se cuenta aparte.
    # (Además, moto arranca con su catálogo de imágenes, cada una con su instantánea.)
    de_imagenes = {bd["Ebs"]["SnapshotId"] for im in ec2.describe_images(Owners=["self", "amazon"])["Images"]
                   for bd in im.get("BlockDeviceMappings", []) if bd.get("Ebs", {}).get("SnapshotId")}
    for s in ec2.describe_snapshots(OwnerIds=["self"])["Snapshots"]:
        if s["SnapshotId"] in de_imagenes:
            continue
        out.append(("instantánea", s["SnapshotId"], f"{s['VolumeSize']} GB de {s.get('VolumeId', '?')}", etiqueta(s, clave),
                    s["VolumeSize"] * PR.P["snapshot_gb_mes"][0]))
    # Toda IP fija cobra lo mismo, se use o no (0,005 USD/h en uso y libre, misma lista).
    for a in ec2.describe_addresses()["Addresses"]:
        viva = a.get("InstanceId") in vivas
        uso = (f"en {a['InstanceId']}" if viva else "SIN USAR (su instancia ya no existe)" if a.get("InstanceId")
               else "en un NAT o interfaz" if a.get("AssociationId") else "SIN USAR")
        out.append(("IPv4 fija", a["PublicIp"], uso, etiqueta(a, clave),
                    PR.P["ipv4_en_uso_hora" if a.get("AssociationId") else "ipv4_libre_hora"][0] * H))
    for n in ec2.describe_nat_gateways(Filter=[{"Name": "state", "Values": ["available", "pending"]}])["NatGateways"]:
        out.append(("NAT gateway", n["NatGatewayId"], f"en {n['SubnetId']}", etiqueta(n, clave), PR.P["nat_hora"][0] * H))
    return out


def informe(hallazgos, titulo="lo que cobra"):
    print(f"  {titulo}: {len(hallazgos)} recursos")
    for tipo, rid, det, dueno, coste in hallazgos:
        print(f"    {tipo:15s} {rid:24s} {det[:36]:36s} {dueno:16s} {PR.usd(coste):>12s}/mes")
    total = sum(h[4] for h in hallazgos)
    print(f"  TOTAL estimado: {PR.usd(total)} al mes (precio de lista, {PR.HORAS_MES} h)")
    return total


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--endpoint", default=None)
    ap.add_argument("--etiqueta", default="Proyecto")
    a = ap.parse_args()
    h = cazar(cliente(a.endpoint), a.etiqueta)
    informe(h)
    return 1 if h else 0


if __name__ == "__main__":
    sys.exit(main())
