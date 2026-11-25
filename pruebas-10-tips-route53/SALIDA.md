# SALIDA — 10 tips para Amazon Route 53 (demos ejecutadas)

Generado por `python correr.py`. **No se edita a mano.**

- fecha: 2026-10-10 18:15 UTC
- aws-cli/2.36.5 Python/3.14.6 Windows/11 exe/AMD64
- moto 5.2.3 (emulador de la API de AWS)
- moto emula la API, no la factura ni todos los valores por defecto.

## Una zona pública nueva

`$ aws route53 create-hosted-zone --name ejemplo.com ...
$ aws route53 list-resource-record-sets --hosted-zone-id <zona>`

```
[
    {
        "Nombre": "ejemplo.com.",
        "Tipo": "NS",
        "TTL": 172800
    },
    {
        "Nombre": "ejemplo.com.",
        "Tipo": "SOA",
        "TTL": 900
    }
]
```

## Un registro A para www, con su TTL

`$ aws route53 change-resource-record-sets ... www.ejemplo.com A 203.0.113.10 TTL 300`

```
"INSYNC"
```

## Un alias en el ápex de la zona

`$ aws route53 change-resource-record-sets ... ejemplo.com A alias → www.ejemplo.com`

```
"INSYNC"
```

`$ aws route53 list-resource-record-sets --hosted-zone-id <zona>   # los A`

```
[
    {
        "Nombre": "ejemplo.com.",
        "Alias": "www.ejemplo.com",
        "TTL": null
    },
    {
        "Nombre": "www.ejemplo.com.",
        "Alias": null,
        "TTL": 300
    }
]
```

## Reparto por pesos: 90 y 10

`$ aws route53 change-resource-record-sets ... api estable 90 · canario 10
$ aws route53 list-resource-record-sets ... api.ejemplo.com`

```
[
    {
        "Id": "estable",
        "Peso": 90,
        "IP": "203.0.113.20"
    },
    {
        "Id": "canario",
        "Peso": 10,
        "IP": "203.0.113.30"
    }
]
```

## Un health check y conmutación por error

`$ aws route53 create-health-check ... HTTPS 203.0.113.20:443/salud
$ aws route53 get-health-check --health-check-id <id>`

```
{
    "Tipo": "HTTPS",
    "IP": "203.0.113.20",
    "Ruta": "/salud",
    "Intervalo": 30,
    "Fallos": 3
}
```

`$ aws route53 change-resource-record-sets ... app PRIMARY (con health check) · SECONDARY
$ aws route53 list-resource-record-sets ... app.ejemplo.com`

```
[
    {
        "Id": "principal",
        "Failover": "PRIMARY",
        "IP": "203.0.113.20",
        "HC": true
    },
    {
        "Id": "reserva",
        "Failover": "SECONDARY",
        "IP": "203.0.113.40",
        "HC": false
    }
]
```

## Una zona privada, solo dentro de una VPC

`$ aws route53 create-hosted-zone --name interno.ejemplo --vpc VPCRegion=us-east-1,VPCId=<vpc> --hosted-zone-config PrivateZone=true`

```
{
    "Nombre": "interno.ejemplo.",
    "Privada": true
}
```

## Borrar una zona que tiene registros

`$ aws route53 delete-hosted-zone --id <zona>`

```
aws: [ERROR]: An error occurred (HostedZoneNotEmpty) when calling the DeleteHostedZone operation: The hosted zone contains resource records that are not SOA or NS records.
```
