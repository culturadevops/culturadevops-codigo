# SALIDA — La capa gratuita de AWS en 2026 (692) (demos ejecutadas)

Generado por `python correr.py`. **No se edita a mano.**

- fecha: 2026-10-29 12:52 UTC
- aws-cli/2.36.5 Python/3.14.6 Windows/11 exe/AMD64
- moto 5.2.3 (emulador de la API de AWS)
- moto emula la API, no la factura ni todos los valores por defecto.

## 1 · Las máquinas que la API marca como Free tier eligible

`$ aws ec2 describe-instance-types --filters Name=free-tier-eligible,Values=true --query sort_by(InstanceTypes,&InstanceType)[].[InstanceType,VCpuInfo.DefaultVCpus,MemoryInfo.SizeInMiB] --output text`

```
c7i-flex.large	2	4096
m7i-flex.large	2	8192
t3.micro	2	1024
t3.small	2	2048
t4g.micro	2	1024
t4g.small	2	2048
```

## 2 · La arquitectura de tutorial, creada por API

`$ aws ec2 run-instances --image-id ami-12c6146b --instance-type t3.small --subnet-id subnet-470dc33956e5dac28 --associate-public-ip-address --block-device-mappings DeviceName=/dev/xvda,Ebs={VolumeSize=30,VolumeType=gp3} --query Instances[].{Id:InstanceId,Tipo:InstanceType,IP:PublicIpAddress}`

```
[
    {
        "Id": "i-bb2b8d76c13a60d2e",
        "Tipo": "t3.small",
        "IP": "54.214.116.219"
    }
]
```

`$ aws ec2 allocate-address --domain vpc --query {IP:PublicIp,Id:AllocationId}`

```
{
    "IP": "127.129.70.168",
    "Id": "eipalloc-d4f4c90be1b034b29"
}
```

`$ aws ec2 create-nat-gateway --subnet-id subnet-470dc33956e5dac28 --allocation-id eipalloc-d4f4c90be1b034b29 --query NatGateway.{Id:NatGatewayId,Estado:State}`

```
{
    "Id": "nat-a6931d1fcf823c6e3",
    "Estado": "available"
}
```

`$ aws rds create-db-instance --db-instance-identifier tienda --engine postgres --db-instance-class db.t4g.micro --allocated-storage 20 --storage-type gp3 --master-username app --master-user-password no-es-real-123 --query DBInstance.{Id:DBInstanceIdentifier,Clase:DBInstanceClass,GB:AllocatedStorage}`

```
{
    "Id": "tienda",
    "Clase": "db.t4g.micro",
    "GB": 20
}
```

## 3 · Inventario: lo que devuelve la API, con su precio de lista al mes

`$ python inventario (describe-instances, describe-volumes, describe-nat-gateways, describe-addresses, describe-db-instances) × lista de precios`

```
máquina t3.small                15.18 USD/mes
IPv4 pública de la máquina       3.65 USD/mes
disco gp3 30 GB                  2.40 USD/mes
NAT gateway                     32.85 USD/mes
IPv4 fija (la del NAT)           3.65 USD/mes
RDS db.t4g.micro                11.68 USD/mes
RDS disco 20 GB                  2.30 USD/mes
750 h de IPv4 gratis con EC2    -3.75 USD/mes
TOTAL                           67.96 USD/mes
100 USD de créditos: 1.5 meses · 200 USD: 2.9 meses (día 90)
```

## 4 · Un presupuesto de 10 USD con avisos, por API

`$ aws budgets create-budget --account-id 123456789012 --budget file://presupuesto.json --notifications-with-subscribers file://avisos.json`

```
(sin salida)
```

`$ aws budgets describe-notifications-for-budget --account-id 123456789012 --budget-name no-me-asustes --query Notifications[].[NotificationType,Threshold] --output text`

```
ACTUAL	50
ACTUAL	80
FORECASTED	100
```

## 5 · Apago todo… menos la IP fija

`$ aws ec2 terminate-instances --instance-ids i-bb2b8d76c13a60d2e --query TerminatingInstances[].CurrentState.Name`

```
[
    "shutting-down"
]
```

`$ aws ec2 delete-nat-gateway --nat-gateway-id nat-a6931d1fcf823c6e3 --query NatGatewayId`

```
"nat-a6931d1fcf823c6e3"
```

`$ aws rds delete-db-instance --db-instance-identifier tienda --skip-final-snapshot --query DBInstance.DBInstanceStatus`

```
"deleting"
```

`$ aws ec2 describe-addresses --query Addresses[].PublicIp --output text`

```
127.129.70.168
```

> La IP fija sigue en la cuenta. En uso o sin usar, la lista de VPC cobra lo mismo: 3.65 y 3.65 USD/mes. (moto no la desasocia al borrar el NAT: por eso aquí no se muestra la asociación.)

`$ aws ec2 release-address --allocation-id eipalloc-d4f4c90be1b034b29`

```
(sin salida)
```

`$ aws ec2 describe-addresses --query length(Addresses)`

```
0
```
