# -*- coding: utf-8 -*-
"""Vídeo 693 · ¿Qué es AWS? — los servicios base, creados con la AWS CLI contra moto (emulador local: sin cuenta, sin factura).

Zonas de una región, IAM, VPC, EC2, S3, RDS y Lambda; y parar una máquina.
⚠️ moto emula la API, no la infraestructura: las zonas y los tipos de máquina salen de los datos del emulador.
    python correr.py   -> SALIDA-moto.md   (lo llama ejecutar_todo.py)
"""
import io
import json
import shutil
import sys
import zipfile
from pathlib import Path

AQUI = Path(__file__).resolve().parent
sys.path.insert(0, str(AQUI.parent))
from banco_moto import Banco  # noqa: E402

AMI = "ami-12c6146b"  # AMI precargada en moto (no es una imagen real de AWS)


def j(b, *a):
    return json.loads(b.aws(*a, "--output", "json", guardar=False) or "null")


with Banco(AQUI, "¿Qué es AWS? (693)", puerto=5693) as b:
    b.titulo("1 · Una región por dentro: sus zonas de disponibilidad")
    b.aws("ec2", "describe-availability-zones", "--region", "us-east-1", "--query", "AvailabilityZones[].ZoneName",
          "--output", "text")
    b.aws("ec2", "describe-availability-zones", "--region", "sa-east-1", "--query", "AvailabilityZones[].ZoneName",
          "--output", "text")

    b.titulo("2 · IAM: un usuario que solo puede leer un bucket")
    b.aws("iam", "create-user", "--user-name", "ana", "--query", "User.Arn", "--output", "text")
    (AQUI / "permiso.json").write_text(json.dumps({"Version": "2012-10-17", "Statement": [
        {"Effect": "Allow", "Action": ["s3:GetObject", "s3:ListBucket"],
         "Resource": ["arn:aws:s3:::mi-primer-bucket-693", "arn:aws:s3:::mi-primer-bucket-693/*"]}]}), encoding="utf-8")
    pol = b.aws("iam", "create-policy", "--policy-name", "leer-bucket", "--policy-document", "file://permiso.json",
                "--query", "Policy.Arn", "--output", "text").strip()
    b.aws("iam", "attach-user-policy", "--user-name", "ana", "--policy-arn", pol)
    b.aws("iam", "list-attached-user-policies", "--user-name", "ana", "--query", "AttachedPolicies[].PolicyName",
          "--output", "text")

    b.titulo("3 · VPC: tu red privada, con una subred en una zona")
    vpc = b.aws("ec2", "create-vpc", "--cidr-block", "10.0.0.0/16", "--query", "Vpc.VpcId", "--output", "text").strip()
    sub = b.aws("ec2", "create-subnet", "--vpc-id", vpc, "--cidr-block", "10.0.1.0/24", "--availability-zone", "us-east-1a",
                "--query", "Subnet.[SubnetId,AvailabilityZone,CidrBlock]", "--output", "text")
    sub = sub.split()[0]

    b.titulo("4 · EC2: un servidor t3.micro en esa subred")
    b.aws("ec2", "run-instances", "--image-id", AMI, "--instance-type", "t3.micro", "--subnet-id", sub,
          "--query", "Instances[].[InstanceId,InstanceType,Placement.AvailabilityZone,State.Name]", "--output", "text")
    ids = b.aws("ec2", "describe-instances", "--query", "Reservations[].Instances[].InstanceId", "--output", "text",
                guardar=False).split()

    b.titulo("5 · S3: un bucket y un archivo")
    b.aws("s3api", "create-bucket", "--bucket", "mi-primer-bucket-693", "--query", "Location", "--output", "text")
    (AQUI / "hola.txt").write_text("hola AWS\n", encoding="utf-8")
    b.aws("s3", "cp", "hola.txt", "s3://mi-primer-bucket-693/hola.txt", "--no-progress")
    b.aws("s3", "ls", "s3://mi-primer-bucket-693/")

    b.titulo("6 · RDS: una base de datos PostgreSQL administrada")
    b.aws("rds", "create-db-instance", "--db-instance-identifier", "app", "--engine", "postgres", "--db-instance-class",
          "db.t4g.micro", "--allocated-storage", "20", "--master-username", "app", "--master-user-password", "no-es-real-123",
          "--query", "DBInstance.[DBInstanceIdentifier,Engine,DBInstanceClass,AllocatedStorage]", "--output", "text")

    b.titulo("7 · Lambda: una función, sin servidor que administrar")
    conf = json.dumps({"Version": "2012-10-17", "Statement": [{"Effect": "Allow", "Principal": {"Service": "lambda.amazonaws.com"},
                                                                "Action": "sts:AssumeRole"}]})
    (AQUI / "confianza.json").write_text(conf, encoding="utf-8")
    rol = b.aws("iam", "create-role", "--role-name", "fn-hola", "--assume-role-policy-document", "file://confianza.json",
                "--query", "Role.Arn", "--output", "text", guardar=False).strip()
    zbuf = io.BytesIO()
    with zipfile.ZipFile(zbuf, "w") as z:
        z.writestr("app.py", "def handler(event, context):\n    return {'hola': 'AWS'}\n")
    (AQUI / "fn.zip").write_bytes(zbuf.getvalue())
    b.aws("lambda", "create-function", "--function-name", "hola", "--runtime", "python3.12", "--role", rol, "--handler",
          "app.handler", "--zip-file", "fileb://fn.zip", "--memory-size", "128",
          "--query", "[FunctionName,Runtime,MemorySize]", "--output", "text")

    b.titulo("8 · Pago por uso: parar la máquina")
    b.aws("ec2", "stop-instances", "--instance-ids", *ids, "--query", "StoppingInstances[].CurrentState.Name", "--output", "text")
    b.aws("ec2", "describe-volumes", "--query", "Volumes[].[VolumeId,Size,State]", "--output", "text")
    b.nota("Parada, la máquina no suma horas de cómputo; el disco sigue existiendo, y se cobra por GB-mes.")

shutil.move(str(AQUI / "SALIDA.md"), str(AQUI / "SALIDA-moto.md"))
