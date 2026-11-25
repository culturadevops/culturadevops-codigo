# -*- coding: utf-8 -*-
"""Curso de cloud computing desde cero (cultura-devops 497-499) — demos con la AWS CLI contra moto (emulador de AWS en local,
sin cuenta y sin factura). Escribe SALIDA-1.md, SALIDA-2.md y SALIDA-3.md.

⚠️ moto emula la API, no la factura: los presupuestos no se evalúan ni envían avisos, y las máquinas no corren de verdad.
   Lo que se enseña es lo que acepta y devuelve la API, igual que en AWS.

    python correr.py
"""
import json
import shutil
import sys
from pathlib import Path

AQUI = Path(__file__).resolve().parent
sys.path.insert(0, str(AQUI.parent))
from banco_moto import Banco  # noqa: E402

CUENTA = "123456789012"
AMI = "ami-12c6146b"  # una AMI que moto trae precargada (no es una imagen real de AWS)


def renombrar(n):
    s = AQUI / "SALIDA.md"
    if s.exists():
        shutil.move(str(s), str(AQUI / f"SALIDA-{n}.md"))


# ── Parte 1 · qué es la nube: pedir recursos por API, al momento, y soltarlos ──
with Banco(AQUI, "Curso de cloud desde cero · 1 · qué es la nube", puerto=5201) as b:
    b.titulo("Autoservicio bajo demanda: pido almacenamiento y me lo dan al instante")
    b.aws("s3api", "create-bucket", "--bucket", "mi-primer-bucket-cultura")
    (AQUI / "hola.txt").write_text("hola nube\n", encoding="utf-8")
    b.aws("s3", "cp", "hola.txt", "s3://mi-primer-bucket-cultura/hola.txt")
    b.aws("s3", "ls", "s3://mi-primer-bucket-cultura/")
    b.titulo("Elasticidad: tres servidores ahora… y cero un minuto después")
    b.aws("ec2", "run-instances", "--image-id", AMI, "--instance-type", "t3.micro", "--count", "3",
          "--query", "Instances[].{Id:InstanceId,Tipo:InstanceType,Estado:State.Name}")
    ids = b.aws("ec2", "describe-instances", "--query", "Reservations[].Instances[].InstanceId", "--output", "text",
                guardar=False).split()
    b.aws("ec2", "terminate-instances", "--instance-ids", *ids, "--query", "TerminatingInstances[].CurrentState.Name")
    b.nota("En AWS real, cada una de esas instancias se cobra por segundo mientras existe (mínimo 60 s en Linux).")
renombrar(1)

# ── Parte 2 · los servicios que tienen todas las nubes: red, cómputo, almacenamiento, identidad ──
with Banco(AQUI, "Curso de cloud desde cero · 2 · los servicios básicos", puerto=5202) as b:
    b.titulo("Red: una VPC y una subred")
    vpc = b.aws("ec2", "create-vpc", "--cidr-block", "10.0.0.0/16", "--query", "Vpc.VpcId", "--output", "text")
    sub = b.aws("ec2", "create-subnet", "--vpc-id", vpc.strip(), "--cidr-block", "10.0.1.0/24", "--query", "Subnet.SubnetId",
                "--output", "text")
    b.titulo("Seguridad de red: solo HTTPS desde internet")
    sg = b.aws("ec2", "create-security-group", "--group-name", "web", "--description", "solo https", "--vpc-id", vpc.strip(),
               "--query", "GroupId", "--output", "text")
    b.aws("ec2", "authorize-security-group-ingress", "--group-id", sg.strip(), "--protocol", "tcp", "--port", "443",
          "--cidr", "0.0.0.0/0", "--query", "SecurityGroupRules[].{Puerto:FromPort,Desde:CidrIpv4}")
    b.titulo("Cómputo: una máquina en esa subred")
    b.aws("ec2", "run-instances", "--image-id", AMI, "--instance-type", "t3.micro", "--subnet-id", sub.strip(),
          "--security-group-ids", sg.strip(), "--query", "Instances[].{Id:InstanceId,Subred:SubnetId,IP:PrivateIpAddress}")
    b.titulo("Almacenamiento: un bucket para archivos")
    b.aws("s3api", "create-bucket", "--bucket", "archivos-app-cultura")
    b.titulo("Identidad: un rol que solo puede LEER ese bucket")
    confianza = {"Version": "2012-10-17", "Statement": [{"Effect": "Allow", "Principal": {"Service": "ec2.amazonaws.com"},
                                                          "Action": "sts:AssumeRole"}]}
    permiso = {"Version": "2012-10-17", "Statement": [{"Effect": "Allow", "Action": ["s3:GetObject"],
                                                        "Resource": "arn:aws:s3:::archivos-app-cultura/*"}]}
    (AQUI / "confianza.json").write_text(json.dumps(confianza, indent=2), encoding="utf-8")
    (AQUI / "permiso.json").write_text(json.dumps(permiso, indent=2), encoding="utf-8")
    b.anotar("cat permiso.json", (AQUI / "permiso.json").read_text(encoding="utf-8"))
    b.aws("iam", "create-role", "--role-name", "app-lee-archivos", "--assume-role-policy-document", "file://confianza.json",
          "--query", "Role.Arn", "--output", "text")
    b.aws("iam", "put-role-policy", "--role-name", "app-lee-archivos", "--policy-name", "solo-leer",
          "--policy-document", "file://permiso.json")
    b.aws("iam", "list-role-policies", "--role-name", "app-lee-archivos")
renombrar(2)

# ── Parte 3 · que la factura no te sorprenda: un presupuesto con avisos ──
with Banco(AQUI, "Curso de cloud desde cero · 3 · el presupuesto", puerto=5203) as b:
    presupuesto = {"BudgetName": "mi-cuenta-de-practica", "BudgetType": "COST", "TimeUnit": "MONTHLY",
                   "BudgetLimit": {"Amount": "10", "Unit": "USD"}}
    avisos = [{"Notification": {"NotificationType": "ACTUAL", "ComparisonOperator": "GREATER_THAN", "Threshold": 50,
                                "ThresholdType": "PERCENTAGE"},
               "Subscribers": [{"SubscriptionType": "EMAIL", "Address": "yo@example.com"}]},
              {"Notification": {"NotificationType": "FORECASTED", "ComparisonOperator": "GREATER_THAN", "Threshold": 100,
                                "ThresholdType": "PERCENTAGE"},
               "Subscribers": [{"SubscriptionType": "EMAIL", "Address": "yo@example.com"}]}]
    (AQUI / "presupuesto.json").write_text(json.dumps(presupuesto, indent=2), encoding="utf-8")
    (AQUI / "avisos.json").write_text(json.dumps(avisos, indent=2), encoding="utf-8")
    b.titulo("Un presupuesto de 10 USD al mes, con dos avisos")
    b.anotar("cat presupuesto.json", (AQUI / "presupuesto.json").read_text(encoding="utf-8"))
    b.aws("budgets", "create-budget", "--account-id", CUENTA, "--budget", "file://presupuesto.json",
          "--notifications-with-subscribers", "file://avisos.json")
    b.aws("budgets", "describe-notifications-for-budget", "--account-id", CUENTA, "--budget-name", "mi-cuenta-de-practica",
          "--query", "Notifications[].{Tipo:NotificationType,Umbral:Threshold}")
    b.nota("moto guarda el presupuesto, pero no tiene facturación: no evalúa el gasto ni envía correos. En AWS, sí.")
renombrar(3)
print("ok")
