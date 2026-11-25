# -*- coding: utf-8 -*-
"""Vídeo 692 · demos con la AWS CLI contra moto (emulador de la API de AWS en local, sin cuenta y sin factura).

1. Qué máquinas marca la API como «Free tier eligible».
2. Se monta la arquitectura «de tutorial» (VPC, máquina con IP pública, NAT gateway con su IP, base de datos) y se hace
   inventario: cada recurso que devuelve la API, con su precio de lista al mes (lista.py).
3. Un presupuesto de 10 USD con avisos, por API.
4. Se borra la máquina y el NAT, pero se olvida la IP fija: la API la sigue listando, ahora sin asociar.

⚠️ moto no cobra ni conoce el plan gratuito (la API freetier responde 500): el precio sale de la lista pública, no de una factura.
    python correr.py   -> SALIDA-moto.md   (lo llama ejecutar_todo.py)
"""
import json
import shutil
import sys
from pathlib import Path

AQUI = Path(__file__).resolve().parent
sys.path.insert(0, str(AQUI.parent))
sys.path.insert(0, str(AQUI))
from banco_moto import Banco  # noqa: E402
from lista import H, bajar, uno  # noqa: E402

EC2, VPC, RDS = bajar("AmazonEC2"), bajar("AmazonVPC"), bajar("AmazonRDS")
PRECIO = {
    "t3.small": uno(EC2, usageType="BoxUsage:t3.small")[0] * H,
    "ipv4": uno(VPC, usageType="USE1-PublicIPv4:InUseAddress")[0] * H,
    "ipv4_libre": uno(VPC, usageType="USE1-PublicIPv4:IdleAddress")[0] * H,
    "nat": uno(EC2, usageType="NatGateway-Hours")[0] * H,
    "gp3": uno(EC2, usageType="EBS:VolumeUsage.gp3")[0],
    "rds": uno(RDS, usageType="InstanceUsage:db.t4g.micro")[0] * H,
    "rds_gb": uno(RDS, usageType="RDS:GP3-Storage")[0],
}
AMI = "ami-12c6146b"  # AMI precargada en moto (no es una imagen real de AWS)


def j(b, *a):
    return json.loads(b.aws(*a, "--output", "json", guardar=False) or "null")


with Banco(AQUI, "La capa gratuita de AWS en 2026 (692)", puerto=5692) as b:
    b.titulo("1 · Las máquinas que la API marca como Free tier eligible")
    b.aws("ec2", "describe-instance-types", "--filters", "Name=free-tier-eligible,Values=true",
          "--query", "sort_by(InstanceTypes,&InstanceType)[].[InstanceType,VCpuInfo.DefaultVCpus,MemoryInfo.SizeInMiB]",
          "--output", "text")

    b.titulo("2 · La arquitectura de tutorial, creada por API")
    vpc = j(b, "ec2", "create-vpc", "--cidr-block", "10.0.0.0/16")["Vpc"]["VpcId"]
    pub = j(b, "ec2", "create-subnet", "--vpc-id", vpc, "--cidr-block", "10.0.1.0/24")["Subnet"]["SubnetId"]
    j(b, "ec2", "create-subnet", "--vpc-id", vpc, "--cidr-block", "10.0.2.0/24")
    igw = j(b, "ec2", "create-internet-gateway")["InternetGateway"]["InternetGatewayId"]
    j(b, "ec2", "attach-internet-gateway", "--internet-gateway-id", igw, "--vpc-id", vpc)
    b.aws("ec2", "run-instances", "--image-id", AMI, "--instance-type", "t3.small", "--subnet-id", pub,
          "--associate-public-ip-address", "--block-device-mappings",
          "DeviceName=/dev/xvda,Ebs={VolumeSize=30,VolumeType=gp3}",
          "--query", "Instances[].{Id:InstanceId,Tipo:InstanceType,IP:PublicIpAddress}")
    eip = b.aws("ec2", "allocate-address", "--domain", "vpc", "--query", "{IP:PublicIp,Id:AllocationId}")
    alloc = json.loads(eip)["Id"]
    b.aws("ec2", "create-nat-gateway", "--subnet-id", pub, "--allocation-id", alloc,
          "--query", "NatGateway.{Id:NatGatewayId,Estado:State}")
    b.aws("rds", "create-db-instance", "--db-instance-identifier", "tienda", "--engine", "postgres",
          "--db-instance-class", "db.t4g.micro", "--allocated-storage", "20", "--storage-type", "gp3",
          "--master-username", "app", "--master-user-password", "no-es-real-123",
          "--query", "DBInstance.{Id:DBInstanceIdentifier,Clase:DBInstanceClass,GB:AllocatedStorage}")

    b.titulo("3 · Inventario: lo que devuelve la API, con su precio de lista al mes")
    filas = []
    for r in j(b, "ec2", "describe-instances")["Reservations"]:
        for i in r["Instances"]:
            filas.append((f"máquina {i['InstanceType']}", i["InstanceId"], PRECIO[i["InstanceType"]]))
            if i.get("PublicIpAddress"):
                filas.append(("IPv4 pública de la máquina", i["PublicIpAddress"], PRECIO["ipv4"]))
    for v in j(b, "ec2", "describe-volumes")["Volumes"]:
        filas.append((f"disco {v['VolumeType']} {v['Size']} GB", v["VolumeId"], v["Size"] * PRECIO["gp3"]))
    for n in j(b, "ec2", "describe-nat-gateways")["NatGateways"]:
        filas.append(("NAT gateway", n["NatGatewayId"], PRECIO["nat"]))
    for a in j(b, "ec2", "describe-addresses")["Addresses"]:
        filas.append(("IPv4 fija (la del NAT)", a["PublicIp"], PRECIO["ipv4"]))
    for d in j(b, "rds", "describe-db-instances")["DBInstances"]:
        filas.append((f"RDS {d['DBInstanceClass']}", d["DBInstanceIdentifier"], PRECIO["rds"]))
        filas.append((f"RDS disco {d['AllocatedStorage']} GB", d["DBInstanceIdentifier"], d["AllocatedStorage"] * PRECIO["rds_gb"]))
    n_ip = sum(1 for t, *_ in filas if t.startswith("IPv4"))
    filas.append(("750 h de IPv4 gratis con EC2", f"{n_ip} IP × {H} h", -min(n_ip * H, 750) * PRECIO["ipv4"] / H))
    tot = sum(x for *_, x in filas)
    txt = [f"{t:<30} {x:6.2f} USD/mes" for t, i, x in filas]
    txt += [f"{'TOTAL':<30} {tot:6.2f} USD/mes",
            f"100 USD de créditos: {100 / tot:.1f} meses · 200 USD: {200 / tot:.1f} meses (día {200 / (tot / H * 24):.0f})"]
    b.anotar("python inventario (describe-instances, describe-volumes, describe-nat-gateways, describe-addresses, "
             "describe-db-instances) × lista de precios", "\n".join(txt))

    b.titulo("4 · Un presupuesto de 10 USD con avisos, por API")
    presu = AQUI / "presupuesto.json"
    presu.write_text(json.dumps({"BudgetName": "no-me-asustes", "BudgetLimit": {"Amount": "10", "Unit": "USD"},
                                 "TimeUnit": "MONTHLY", "BudgetType": "COST"}), encoding="utf-8")
    avisos = AQUI / "avisos.json"
    avisos.write_text(json.dumps([{"Notification": {"NotificationType": t, "ComparisonOperator": "GREATER_THAN",
                                                    "Threshold": u, "ThresholdType": "PERCENTAGE"},
                                   "Subscribers": [{"SubscriptionType": "EMAIL", "Address": "yo@example.com"}]}
                                  for t, u in (("ACTUAL", 50), ("ACTUAL", 80), ("FORECASTED", 100))]), encoding="utf-8")
    b.aws("budgets", "create-budget", "--account-id", "123456789012", "--budget", "file://presupuesto.json",
          "--notifications-with-subscribers", "file://avisos.json")
    b.aws("budgets", "describe-notifications-for-budget", "--account-id", "123456789012", "--budget-name", "no-me-asustes",
          "--query", "Notifications[].[NotificationType,Threshold]", "--output", "text")

    b.titulo("5 · Apago todo… menos la IP fija")
    ids = [i["InstanceId"] for r in j(b, "ec2", "describe-instances")["Reservations"] for i in r["Instances"]]
    b.aws("ec2", "terminate-instances", "--instance-ids", *ids, "--query", "TerminatingInstances[].CurrentState.Name")
    nat = j(b, "ec2", "describe-nat-gateways")["NatGateways"][0]["NatGatewayId"]
    b.aws("ec2", "delete-nat-gateway", "--nat-gateway-id", nat, "--query", "NatGatewayId")
    b.aws("rds", "delete-db-instance", "--db-instance-identifier", "tienda", "--skip-final-snapshot",
          "--query", "DBInstance.DBInstanceStatus")
    b.aws("ec2", "describe-addresses", "--query", "Addresses[].PublicIp", "--output", "text")
    b.nota(f"La IP fija sigue en la cuenta. En uso o sin usar, la lista de VPC cobra lo mismo: "
           f"{PRECIO['ipv4']:.2f} y {PRECIO['ipv4_libre']:.2f} USD/mes. (moto no la desasocia al borrar el NAT: por eso "
           f"aquí no se muestra la asociación.)")
    b.aws("ec2", "release-address", "--allocation-id", alloc)
    b.aws("ec2", "describe-addresses", "--query", "length(Addresses)")

shutil.move(str(AQUI / "SALIDA.md"), str(AQUI / "SALIDA-moto.md"))
