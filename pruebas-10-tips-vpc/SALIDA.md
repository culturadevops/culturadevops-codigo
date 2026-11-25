# SALIDA — 10 tips para Amazon VPC (demos ejecutadas)

Generado por `python correr.py`. **No se edita a mano.**

- fecha: 2026-10-10 00:19 UTC
- aws-cli/2.36.5 Python/3.14.6 Windows/11 exe/AMD64
- moto 5.2.3 (emulador de la API de AWS)
- moto emula la API, no la factura ni todos los valores por defecto.

## Una VPC y sus subredes

`$ aws ec2 create-vpc --cidr-block 10.0.0.0/16 --query Vpc.VpcId --output text`

```
vpc-587bf94ff316d1d21
```

`$ aws ec2 create-subnet --vpc-id <vpc> --cidr-block 10.0.1.0/24 --availability-zone us-east-1a`

```
"10.0.1.0/24"
```

`$ aws ec2 create-subnet --vpc-id <vpc> --cidr-block 10.0.1.128/25 --availability-zone us-east-1a`

```
aws: [ERROR]: An error occurred (InvalidSubnet.Conflict) when calling the CreateSubnet operation: The CIDR '10.0.1.128/25' conflicts with another subnet
```

`$ aws ec2 create-vpc --cidr-block 10.0.0.0/8`

```
aws: [ERROR]: An error occurred (InvalidVpc.Range) when calling the CreateVpc operation: The CIDR '10.0.0.0/8' is invalid.
```

## Cinco direcciones reservadas por subred

`$ aws ec2 create-subnet --vpc-id <vpc> --cidr-block 10.0.9.0/28 --availability-zone us-east-1b`

```
{
    "Cidr": "10.0.9.0/28",
    "IPsLibres": 11
}
```

## Una IPv4 pública sin usar

`$ aws ec2 describe-addresses --query Addresses[0].{Asignada:AllocationId,Asociada:AssociationId}`

```
{
    "Asignada": "eipalloc-ad4353ac2ec7e2dd3",
    "Asociada": null
}
```

## Endpoint de gateway para S3

`$ aws ec2 create-vpc-endpoint --vpc-id <vpc> --vpc-endpoint-type Gateway --service-name com.amazonaws.us-east-1.s3 --route-table-ids <tabla>`

```
{
    "Tipo": "Gateway",
    "Servicio": "com.amazonaws.us-east-1.s3",
    "Estado": "available"
}
```

`$ aws ec2 describe-route-tables --route-table-ids <tabla>`

```
[
    {
        "Destino": "10.0.0.0/16",
        "Via": "local"
    },
    {
        "Destino": "pl-c0661374daa9f0a04",
        "Via": "vpce-796d745b24f74b694"
    }
]
```

## Flow Logs

`$ aws ec2 create-flow-logs --resource-type VPC --resource-ids <vpc> --traffic-type REJECT --log-destination-type cloud-watch-logs --log-group-name /vpc/rechazos ...`

```
1
```

`$ aws ec2 describe-flow-logs --query FlowLogs[0].{Trafico:TrafficType,Destino:LogGroupName}`

```
{
    "Trafico": "REJECT",
    "Destino": "/vpc/rechazos"
}
```
