# -*- coding: utf-8 -*-
"""Banco del vídeo 413 «¿Vale la pena AWS en 2027?». Sin cuenta: la CLI oficial (amazon/aws-cli) contra moto
(motoserver/moto), el emulador libre de AWS. moto NO es AWS: aquí solo se enseña lo que hace la API.
  · lo primero en una cuenta nueva: un presupuesto con aviso (Budgets);
  · permisos mínimos: un usuario que solo puede leer un bucket (moto con IAM activado);
  · las regiones son independientes: una tabla de DynamoDB en us-east-1 no existe en us-west-2.
    python correr.py   -> SALIDA.md
"""
import json
import subprocess
import time
from datetime import datetime, timezone
from pathlib import Path

AQUI = Path(__file__).parent
OUT = []
NET = "lab-aws27"
ADMIN = "-e AWS_ACCESS_KEY_ID=admin -e AWS_SECRET_ACCESS_KEY=admin"


def run(args, timeout=None):
    p = subprocess.run(args, capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=timeout)
    return (p.stdout + p.stderr).strip(), p.returncode


def aws(args, creds=("admin", "admin"), region="us-east-1"):
    return run(["docker", "run", "--rm", "--network", NET, "-e", f"AWS_ACCESS_KEY_ID={creds[0]}",
                "-e", f"AWS_SECRET_ACCESS_KEY={creds[1]}", "-e", f"AWS_DEFAULT_REGION={region}",
                "-v", f"{AQUI.as_posix()}/tmp:/aws", "amazon/aws-cli", "--endpoint-url", "http://moto:5000"] + args)


def bloque(titulo, mostrado, res, nota=None):
    s, rc = res
    OUT.append(f"### {titulo}\n\n`$ {mostrado}`\n\n```\n{s}\n```\n(código de salida {rc})\n" + (f"\n> {nota}\n" if nota else ""))
    print(f"[{rc}] {titulo}")
    return s, rc


def main():
    (AQUI / "tmp").mkdir(exist_ok=True)
    run(["docker", "rm", "-f", "moto"])
    run(["docker", "network", "create", NET])
    # INITIAL_NO_AUTH_ACTION_COUNT=8: las 8 primeras llamadas (montar el escenario) sin comprobar permisos; después, IAM manda.
    run(["docker", "run", "-d", "--name", "moto", "--network", NET, "-e", "INITIAL_NO_AUTH_ACTION_COUNT=8", "motoserver/moto"])
    time.sleep(4)
    OUT.append(f"# SALIDA — AWS sin cuenta (vídeo 413)\n\nGenerado {datetime.now(timezone.utc):%Y-%m-%d %H:%M} UTC con `python correr.py`. "
               "CLI oficial contra moto; moto no es AWS.\n")
    s, _ = run(["docker", "run", "--rm", "amazon/aws-cli", "--version"])
    OUT.append(f"## 1 · La herramienta\n\n### versión\n\n`$ aws --version`\n\n```\n{s}\n```\n")
    s, _ = run(["docker", "image", "inspect", "-f", "{{.Size}}", "motoserver/moto"])
    OUT.append(f"### tamaño de moto\n\n`$ docker image inspect -f {{{{.Size}}}} motoserver/moto`\n\n```\n{s}\n```\n")

    # ── escenario (llamadas 1-8, sin comprobar permisos)
    (AQUI / "tmp" / "lectura.json").write_text(json.dumps({"Version": "2012-10-17", "Statement": [
        {"Effect": "Allow", "Action": "s3:GetObject", "Resource": "arn:aws:s3:::facturas/*"}]}), encoding="utf-8")
    (AQUI / "tmp" / "factura.txt").write_text("factura 2027-001\n", encoding="utf-8")
    s1, _ = aws(["s3api", "create-bucket", "--bucket", "facturas"])                                       # 1
    s2, _ = aws(["s3api", "put-object", "--bucket", "facturas", "--key", "f1.txt", "--body", "/aws/factura.txt"])  # 2
    s3, _ = aws(["iam", "create-user", "--user-name", "lector"])                                           # 3
    s4, _ = aws(["iam", "put-user-policy", "--user-name", "lector", "--policy-name", "solo-leer",
                 "--policy-document", "file:///aws/lectura.json"])                                         # 4
    k, _ = aws(["iam", "create-access-key", "--user-name", "lector"])                                      # 5
    k = json.loads(k)["AccessKey"]
    lector = (k["AccessKeyId"], k["SecretAccessKey"])
    # admin con permisos de todo, para lo que sigue con IAM activo
    (AQUI / "tmp" / "todo.json").write_text(json.dumps({"Version": "2012-10-17", "Statement": [
        {"Effect": "Allow", "Action": "*", "Resource": "*"}]}), encoding="utf-8")
    aws(["iam", "create-user", "--user-name", "admin"])                                                   # 6
    aws(["iam", "put-user-policy", "--user-name", "admin", "--policy-name", "todo", "--policy-document", "file:///aws/todo.json"])  # 7
    a, _ = aws(["iam", "create-access-key", "--user-name", "admin"])                                       # 8
    a = json.loads(a)["AccessKey"]
    adm = (a["AccessKeyId"], a["SecretAccessKey"])

    OUT.append("## 2 · Lo primero en una cuenta nueva: un presupuesto con aviso\n")
    (AQUI / "tmp" / "presupuesto.json").write_text(json.dumps({"BudgetName": "tope-mensual", "BudgetLimit": {"Amount": "10", "Unit": "USD"},
        "TimeUnit": "MONTHLY", "BudgetType": "COST"}), encoding="utf-8")
    (AQUI / "tmp" / "aviso.json").write_text(json.dumps([{"Notification": {"NotificationType": "ACTUAL", "ComparisonOperator": "GREATER_THAN",
        "Threshold": 80, "ThresholdType": "PERCENTAGE"}, "Subscribers": [{"SubscriptionType": "EMAIL", "Address": "tu@correo.com"}]}]), encoding="utf-8")
    bloque("crear el presupuesto: 10 USD al mes, aviso al 80 %", "aws budgets create-budget --account-id 123456789012 --budget file://presupuesto.json --notifications-with-subscribers file://aviso.json",
           aws(["budgets", "create-budget", "--account-id", "123456789012", "--budget", "file:///aws/presupuesto.json",
                "--notifications-with-subscribers", "file:///aws/aviso.json"], creds=adm))
    bloque("comprobarlo", "aws budgets describe-budgets --account-id 123456789012 --query …",
           aws(["budgets", "describe-budgets", "--account-id", "123456789012", "--query",
                "Budgets[].[BudgetName,BudgetLimit.Amount,BudgetLimit.Unit,TimeUnit]", "--output", "text"], creds=adm))

    OUT.append("## 3 · Permisos mínimos\n")
    bloque("la política del usuario «lector»", "cat lectura.json", (json.dumps(json.loads((AQUI / "tmp" / "lectura.json").read_text()), indent=2), 0))
    bloque("lector: leer la factura", "aws s3 cp s3://facturas/f1.txt -   (como lector)",
           aws(["s3", "cp", "s3://facturas/f1.txt", "-"], creds=lector))
    bloque("lector: listar los buckets", "aws s3 ls   (como lector)", aws(["s3", "ls"], creds=lector))
    bloque("lector: borrar la factura", "aws s3 rm s3://facturas/f1.txt   (como lector)",
           aws(["s3", "rm", "s3://facturas/f1.txt"], creds=lector))
    bloque("¿sigue ahí?", "aws s3 ls s3://facturas/   (como admin)", aws(["s3", "ls", "s3://facturas/"], creds=adm))

    OUT.append("## 4 · Las regiones son independientes\n")
    bloque("una tabla en us-east-1", "aws dynamodb create-table --table-name pedidos … --region us-east-1",
           aws(["dynamodb", "create-table", "--table-name", "pedidos", "--attribute-definitions", "AttributeName=id,AttributeType=S",
                "--key-schema", "AttributeName=id,KeyType=HASH", "--billing-mode", "PAY_PER_REQUEST",
                "--query", "TableDescription.[TableName,TableStatus]", "--output", "text"], creds=adm, region="us-east-1"))
    bloque("las tablas de us-east-1", "aws dynamodb list-tables --region us-east-1",
           aws(["dynamodb", "list-tables", "--output", "text"], creds=adm, region="us-east-1"))
    bloque("las tablas de us-west-2", "aws dynamodb list-tables --region us-west-2",
           aws(["dynamodb", "list-tables", "--output", "json"], creds=adm, region="us-west-2"),
           "Si us-east-1 se cae, lo que solo vive ahí se cae con ella.")

    (AQUI / "SALIDA.md").write_text("\n".join(OUT), encoding="utf-8")
    print("ok SALIDA.md")


if __name__ == "__main__":
    main()
