# -*- coding: utf-8 -*-
"""10 tips para AWS CloudTrail — demos ejecutables con la AWS CLI contra moto. Escribe SALIDA.md.

    python correr.py
"""
import json
import sys
from pathlib import Path

AQUI = Path(__file__).resolve().parent
sys.path.insert(0, str(AQUI.parent))
from banco_moto import Banco  # noqa: E402

POLITICA = {
    "Version": "2012-10-17",
    "Statement": [
        {"Sid": "AWSCloudTrailAclCheck", "Effect": "Allow", "Principal": {"Service": "cloudtrail.amazonaws.com"},
         "Action": "s3:GetBucketAcl", "Resource": "arn:aws:s3:::auditoria-cuenta"},
        {"Sid": "AWSCloudTrailWrite", "Effect": "Allow", "Principal": {"Service": "cloudtrail.amazonaws.com"},
         "Action": "s3:PutObject", "Resource": "arn:aws:s3:::auditoria-cuenta/AWSLogs/123456789012/*",
         "Condition": {"StringEquals": {"s3:x-amz-acl": "bucket-owner-full-control"}}}]}

with Banco(AQUI, "10 tips para AWS CloudTrail", puerto=5110) as b:
    # El historial de eventos (90 días, gratis) va SIN terminal: moto 5.2.3 no implementa
    # LookupEvents (responde 500). Se cuenta con la documentación.

    b.titulo("El bucket del trail y su política")
    b.aws("s3api", "create-bucket", "--bucket", "auditoria-cuenta", guardar=False)
    (AQUI / "politica.json").write_text(json.dumps(POLITICA, indent=2), encoding="utf-8")
    b.aws("s3api", "put-bucket-policy", "--bucket", "auditoria-cuenta", "--policy", "file://politica.json",
          mostrar="s3api put-bucket-policy --bucket auditoria-cuenta --policy file://politica.json")

    b.titulo("Un trail creado con la CLI, solo con lo obligatorio")
    b.aws("cloudtrail", "create-trail", "--name", "auditoria", "--s3-bucket-name", "auditoria-cuenta",
          "--query", "{Nombre:Name,MultiRegion:IsMultiRegionTrail,Validacion:LogFileValidationEnabled}",
          mostrar="cloudtrail create-trail --name auditoria --s3-bucket-name auditoria-cuenta")
    b.aws("cloudtrail", "get-trail-status", "--name", "auditoria", "--query", "IsLogging",
          mostrar="cloudtrail get-trail-status --name auditoria --query IsLogging")

    b.titulo("Encenderlo")
    b.aws("cloudtrail", "start-logging", "--name", "auditoria", mostrar="cloudtrail start-logging --name auditoria")
    b.aws("cloudtrail", "get-trail-status", "--name", "auditoria", "--query", "IsLogging",
          mostrar="cloudtrail get-trail-status --name auditoria --query IsLogging")

    b.titulo("Multirregión y validación de integridad")
    b.aws("cloudtrail", "update-trail", "--name", "auditoria", "--is-multi-region-trail",
          "--enable-log-file-validation",
          "--query", "{MultiRegion:IsMultiRegionTrail,Validacion:LogFileValidationEnabled}",
          mostrar="cloudtrail update-trail --name auditoria --is-multi-region-trail --enable-log-file-validation")

    b.titulo("Eventos de datos: no vienen por defecto")
    b.aws("cloudtrail", "get-event-selectors", "--trail-name", "auditoria", "--query", "EventSelectors",
          mostrar="cloudtrail get-event-selectors --trail-name auditoria")
    sel = [{"ReadWriteType": "All", "IncludeManagementEvents": True,
            "DataResources": [{"Type": "AWS::S3::Object", "Values": ["arn:aws:s3:::datos-clientes/"]}]}]
    (AQUI / "selectores.json").write_text(json.dumps(sel, indent=2), encoding="utf-8")
    b.aws("cloudtrail", "put-event-selectors", "--trail-name", "auditoria", "--event-selectors", "file://selectores.json",
          "--query", "EventSelectors[0].DataResources",
          mostrar="cloudtrail put-event-selectors --trail-name auditoria --event-selectors file://selectores.json")

    b.titulo("Cifrar los logs con tu clave de KMS")
    clave = b.aws("kms", "create-key", "--description", "logs-cloudtrail", "--query", "KeyMetadata.Arn",
                  "--output", "text", guardar=False)
    b.aws("cloudtrail", "update-trail", "--name", "auditoria", "--kms-key-id", clave,
          "--query", "KmsKeyId", mostrar="cloudtrail update-trail --name auditoria --kms-key-id <arn de la clave>")

    b.titulo("Enviar a CloudWatch Logs")
    grupo = b.aws("logs", "create-log-group", "--log-group-name", "cloudtrail/auditoria", guardar=False)
    arn_grupo = b.aws("logs", "describe-log-groups", "--log-group-name-prefix", "cloudtrail/auditoria",
                      "--query", "logGroups[0].arn", "--output", "text", guardar=False)
    rol = b.aws("iam", "create-role", "--role-name", "cloudtrail-a-logs", "--assume-role-policy-document",
                '{"Version":"2012-10-17","Statement":[{"Effect":"Allow","Principal":{"Service":"cloudtrail.amazonaws.com"},"Action":"sts:AssumeRole"}]}',
                "--query", "Role.Arn", "--output", "text", guardar=False)
    b.aws("cloudtrail", "update-trail", "--name", "auditoria", "--cloud-watch-logs-log-group-arn", arn_grupo,
          "--cloud-watch-logs-role-arn", rol, "--query", "CloudWatchLogsLogGroupArn",
          mostrar="cloudtrail update-trail --name auditoria --cloud-watch-logs-log-group-arn <grupo> --cloud-watch-logs-role-arn <rol>")
    b.aws("logs", "put-metric-filter", "--log-group-name", "cloudtrail/auditoria", "--filter-name", "uso-de-root",
          "--filter-pattern", '{ $.userIdentity.type = "Root" && $.userIdentity.invokedBy NOT EXISTS && $.eventType != "AwsServiceEvent" }',
          "--metric-transformations", "metricName=UsoDeRoot,metricNamespace=Seguridad,metricValue=1",
          mostrar="logs put-metric-filter --log-group-name cloudtrail/auditoria --filter-name uso-de-root ...")
    b.aws("logs", "describe-metric-filters", "--log-group-name", "cloudtrail/auditoria",
          "--query", "metricFilters[].{Filtro:filterName,Metrica:metricTransformations[0].metricName}",
          mostrar="logs describe-metric-filters --log-group-name cloudtrail/auditoria")

    b.titulo("El trail, al final")
    b.aws("cloudtrail", "describe-trails", "--query",
          "trailList[0].{Nombre:Name,MultiRegion:IsMultiRegionTrail,Validacion:LogFileValidationEnabled,KMS:KmsKeyId!=null,Logs:CloudWatchLogsLogGroupArn!=null}",
          mostrar="cloudtrail describe-trails")

    b.titulo("Apagarlo es una llamada")
    b.aws("cloudtrail", "stop-logging", "--name", "auditoria", mostrar="cloudtrail stop-logging --name auditoria")
    b.aws("cloudtrail", "get-trail-status", "--name", "auditoria", "--query", "IsLogging",
          mostrar="cloudtrail get-trail-status --name auditoria --query IsLogging")
