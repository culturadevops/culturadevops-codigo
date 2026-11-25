# -*- coding: utf-8 -*-
"""Lección 4 · Lo que sigue cobrando cuando crees que borraste todo.

Un entorno de pruebas: una red, una instancia con un disco de datos, una copia del disco, una IP
pública fija y un NAT gateway para que la instancia salga a internet. Al terminar, «borro la
instancia», que es lo que se ve en la consola. Y la factura sigue.
Corre contra moto (emulador de AWS en memoria): nada de esto cuesta dinero de verdad.
"""
import sys
from pathlib import Path

import boto3
from moto import mock_aws

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import cazador as CZ  # noqa: E402
import precios as PR  # noqa: E402


def titulo(t):
    print(f"\n== {t} ==")


with mock_aws():
    ec2 = boto3.client("ec2", region_name="us-east-1")
    ami = ec2.describe_images(Owners=["amazon"])["Images"][0]["ImageId"]
    vpc = ec2.create_vpc(CidrBlock="10.0.0.0/16")["Vpc"]["VpcId"]
    sub = ec2.create_subnet(VpcId=vpc, CidrBlock="10.0.1.0/24")["Subnet"]["SubnetId"]
    t = [{"ResourceType": r, "Tags": [{"Key": "Proyecto", "Value": "pruebas"}]} for r in ("instance", "volume")]
    i = ec2.run_instances(ImageId=ami, InstanceType="t3.micro", MinCount=1, MaxCount=1, SubnetId=sub,
                          TagSpecifications=t[:1])["Instances"][0]["InstanceId"]
    vol = ec2.create_volume(AvailabilityZone="us-east-1a", Size=100, VolumeType="gp3", TagSpecifications=t[1:])["VolumeId"]
    ec2.attach_volume(VolumeId=vol, InstanceId=i, Device="/dev/sdf")
    snap = ec2.create_snapshot(VolumeId=vol, Description="antes de probar")["SnapshotId"]
    eip = ec2.allocate_address(Domain="vpc")
    ec2.associate_address(AllocationId=eip["AllocationId"], InstanceId=i)
    eip_nat = ec2.allocate_address(Domain="vpc")
    nat = ec2.create_nat_gateway(SubnetId=sub, AllocationId=eip_nat["AllocationId"])["NatGateway"]["NatGatewayId"]

    titulo("4.1 · El entorno de pruebas, encendido")
    CZ.informe(CZ.cazar(ec2), "lo que cobra")

    titulo("4.2 · «Ya terminé»: borro la instancia, como en la consola")
    ec2.terminate_instances(InstanceIds=[i])
    estado = ec2.describe_instances(InstanceIds=[i])["Reservations"][0]["Instances"][0]["State"]["Name"]
    print(f"  la instancia {i}: {estado}")
    restos = CZ.cazar(ec2)
    total = CZ.informe(restos, "lo que SIGUE cobrando")
    print(f"  en un año: {PR.usd(total * 12)}")

    titulo("4.3 · Borrar de verdad, en orden: lo que depende de otra cosa, primero")
    ec2.delete_nat_gateway(NatGatewayId=nat)
    for a in ec2.describe_addresses()["Addresses"]:
        ec2.release_address(AllocationId=a["AllocationId"])
    ec2.delete_snapshot(SnapshotId=snap)
    ec2.delete_volume(VolumeId=vol)
    for paso in ("delete_nat_gateway", "release_address × 2", "delete_snapshot", "delete_volume"):
        print(f"  {paso}")
    restos = CZ.cazar(ec2)
    CZ.informe(restos, "lo que cobra ahora")
