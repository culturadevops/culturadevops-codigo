# -*- coding: utf-8 -*-
"""10 tips para Amazon Route 53 — demos ejecutables con la AWS CLI contra moto. Escribe SALIDA.md.

    python correr.py
"""
import json
import sys
from pathlib import Path

AQUI = Path(__file__).resolve().parent
sys.path.insert(0, str(AQUI.parent))
from banco_moto import Banco  # noqa: E402


def cambio(nombre, accion, rrs):
    (AQUI / nombre).write_text(json.dumps({"Changes": [{"Action": accion, "ResourceRecordSet": r} for r in rrs]},
                                          indent=2), encoding="utf-8")
    return f"file://{nombre}"


with Banco(AQUI, "10 tips para Amazon Route 53", puerto=5111) as b:
    b.titulo("Una zona pública nueva")
    zona = b.aws("route53", "create-hosted-zone", "--name", "ejemplo.com", "--caller-reference", "r1",
                 "--query", "HostedZone.Id", "--output", "text", guardar=False)
    b.aws("route53", "list-resource-record-sets", "--hosted-zone-id", zona,
          "--query", "ResourceRecordSets[].{Nombre:Name,Tipo:Type,TTL:TTL}",
          mostrar="route53 create-hosted-zone --name ejemplo.com ...\n$ aws route53 list-resource-record-sets --hosted-zone-id <zona>")

    b.titulo("Un registro A para www, con su TTL")
    b.aws("route53", "change-resource-record-sets", "--hosted-zone-id", zona, "--change-batch",
          cambio("www.json", "UPSERT", [{"Name": "www.ejemplo.com", "Type": "A", "TTL": 300,
                                         "ResourceRecords": [{"Value": "203.0.113.10"}]}]),
          "--query", "ChangeInfo.Status",
          mostrar="route53 change-resource-record-sets ... www.ejemplo.com A 203.0.113.10 TTL 300")

    # Un CNAME en el ápex NO se enseña: moto 5.2.3 lo acepta, y AWS lo rechaza («You can't create a
    # CNAME record that has the same name as the hosted zone», guía de Route 53).
    b.titulo("Un alias en el ápex de la zona")
    b.aws("route53", "change-resource-record-sets", "--hosted-zone-id", zona, "--change-batch",
          cambio("apex-alias.json", "CREATE", [{"Name": "ejemplo.com", "Type": "A",
                 "AliasTarget": {"HostedZoneId": zona.split("/")[-1], "DNSName": "www.ejemplo.com",
                                 "EvaluateTargetHealth": False}}]),
          "--query", "ChangeInfo.Status",
          mostrar="route53 change-resource-record-sets ... ejemplo.com A alias → www.ejemplo.com")
    b.aws("route53", "list-resource-record-sets", "--hosted-zone-id", zona,
          "--query", "ResourceRecordSets[?Type=='A'].{Nombre:Name,Alias:AliasTarget.DNSName,TTL:TTL}",
          mostrar="route53 list-resource-record-sets --hosted-zone-id <zona>   # los A")

    b.titulo("Reparto por pesos: 90 y 10")
    b.aws("route53", "change-resource-record-sets", "--hosted-zone-id", zona, "--change-batch",
          cambio("pesos.json", "CREATE", [
              {"Name": "api.ejemplo.com", "Type": "A", "TTL": 60, "SetIdentifier": "estable", "Weight": 90,
               "ResourceRecords": [{"Value": "203.0.113.20"}]},
              {"Name": "api.ejemplo.com", "Type": "A", "TTL": 60, "SetIdentifier": "canario", "Weight": 10,
               "ResourceRecords": [{"Value": "203.0.113.30"}]}]),
          "--query", "ChangeInfo.Status", guardar=False)
    b.aws("route53", "list-resource-record-sets", "--hosted-zone-id", zona,
          "--query", "ResourceRecordSets[?Name=='api.ejemplo.com.'].{Id:SetIdentifier,Peso:Weight,IP:ResourceRecords[0].Value}",
          mostrar="route53 change-resource-record-sets ... api estable 90 · canario 10\n$ aws route53 list-resource-record-sets ... api.ejemplo.com")

    b.titulo("Un health check y conmutación por error")
    hc = b.aws("route53", "create-health-check", "--caller-reference", "hc1", "--health-check-config",
               "IPAddress=203.0.113.20,Port=443,Type=HTTPS,ResourcePath=/salud,RequestInterval=30,FailureThreshold=3",
               "--query", "HealthCheck.Id", "--output", "text", guardar=False)
    b.aws("route53", "get-health-check", "--health-check-id", hc,
          "--query", "HealthCheck.HealthCheckConfig.{Tipo:Type,IP:IPAddress,Ruta:ResourcePath,Intervalo:RequestInterval,Fallos:FailureThreshold}",
          mostrar="route53 create-health-check ... HTTPS 203.0.113.20:443/salud\n$ aws route53 get-health-check --health-check-id <id>")
    b.aws("route53", "change-resource-record-sets", "--hosted-zone-id", zona, "--change-batch",
          cambio("failover.json", "CREATE", [
              {"Name": "app.ejemplo.com", "Type": "A", "TTL": 60, "SetIdentifier": "principal", "Failover": "PRIMARY",
               "HealthCheckId": hc, "ResourceRecords": [{"Value": "203.0.113.20"}]},
              {"Name": "app.ejemplo.com", "Type": "A", "TTL": 60, "SetIdentifier": "reserva", "Failover": "SECONDARY",
               "ResourceRecords": [{"Value": "203.0.113.40"}]}]),
          "--query", "ChangeInfo.Status", guardar=False)
    b.aws("route53", "list-resource-record-sets", "--hosted-zone-id", zona,
          "--query", "ResourceRecordSets[?Name=='app.ejemplo.com.'].{Id:SetIdentifier,Failover:Failover,IP:ResourceRecords[0].Value,HC:HealthCheckId!=null}",
          mostrar="route53 change-resource-record-sets ... app PRIMARY (con health check) · SECONDARY\n$ aws route53 list-resource-record-sets ... app.ejemplo.com")

    b.titulo("Una zona privada, solo dentro de una VPC")
    vpc = b.aws("ec2", "create-vpc", "--cidr-block", "10.0.0.0/16", "--query", "Vpc.VpcId", "--output", "text", guardar=False)
    b.aws("route53", "create-hosted-zone", "--name", "interno.ejemplo", "--caller-reference", "r2",
          "--vpc", f"VPCRegion=us-east-1,VPCId={vpc}", "--hosted-zone-config", "PrivateZone=true",
          "--query", "HostedZone.{Nombre:Name,Privada:Config.PrivateZone}",
          mostrar="route53 create-hosted-zone --name interno.ejemplo --vpc VPCRegion=us-east-1,VPCId=<vpc> --hosted-zone-config PrivateZone=true")

    b.titulo("Borrar una zona que tiene registros")
    b.aws("route53", "delete-hosted-zone", "--id", zona, mostrar="route53 delete-hosted-zone --id <zona>")

    for f in ("www.json", "apex-alias.json", "pesos.json", "failover.json"):
        (AQUI / f).unlink(missing_ok=True)
