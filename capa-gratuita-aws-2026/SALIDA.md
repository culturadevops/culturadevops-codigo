# SALIDA — vídeo 692 · La capa gratuita de AWS en 2026

Generado por `python ejecutar_todo.py`. **No se edita a mano.** Importes: precio de lista × uso (estimación).

- fecha: 2026-10-29 12:52 UTC

## Precios (calculo.py)

```
== 1 · Las máquinas «Free tier eligible» de una cuenta nueva, a precio de lista (Linux, bajo demanda) ==
  t3.micro         0.01040 USD/h     7.59 USD/mes   «$0.0104 per On Demand Linux t3.micro Instance Hour»
  t3.small         0.02080 USD/h    15.18 USD/mes   «$0.0208 per On Demand Linux t3.small Instance Hour»
  t4g.micro        0.00840 USD/h     6.13 USD/mes   «$0.0084 per On Demand Linux t4g.micro Instance Hour»
  t4g.small        0.01680 USD/h    12.26 USD/mes   «$0.0168 per On Demand Linux t4g.small Instance Hour»
  c7i-flex.large   0.08479 USD/h    61.90 USD/mes   «$0.08479 per On Demand Linux c7i-flex.large Instance Hour»
  m7i-flex.large   0.09576 USD/h    69.90 USD/mes   «$0.09576 per On Demand Linux m7i-flex.large Instance Hour»
  la más cara se come 200 USD en 2.9 meses; la más barata, en 32.6

== 2 · Lo que se cobra por hora aunque no lo uses (us-east-1) ==
  IPv4 pública en uso                  0.0050 USD/h     3.65 USD/mes   «$0.005 per In-use public IPv4 address per hour»
  IPv4 pública sin usar                0.0050 USD/h     3.65 USD/mes   «$0.005 per Idle public IPv4 address per hour»
  NAT gateway, por hora                0.0450 USD/h    32.85 USD/mes   «$0.045 per NAT Gateway Hour»
  Balanceador de aplicaciones (ALB)    0.0225 USD/h    16.43 USD/mes   «$0.0225 per Application LoadBalancer-hour (or partial hour)»
  Disco gp3, por GB                    0.080 USD/GB-mes  30 GB: 2.40 USD/mes   «$0.08 per GB-month of General Purpose (gp3) provisioned storage - US East (N. Virginia)»
  Instantánea (snapshot), por GB       0.050 USD/GB-mes  30 GB: 1.50 USD/mes
  NAT gateway, por GB procesado        0.045 USD/GB
  Salida a internet (tras lo gratis)   0.090 USD/GB   «$0.090 per GB - first 10 TB / month data transfer out beyond the global free tier»
  IPv4: 750 h/mes gratis con EC2 → 1 IP todo el mes (730 h): 0.00 USD · 2 IP: 3.55 USD · 3 IP: 7.20 USD

== 3 · Lo que es gratis siempre (lista de precios, a 0 USD) ==
  0 USD · «$0 for 100GB of data transfer out to the internet, aggregated globally, each month»
  0 USD · «AWS Lambda - Requests Free Tier - 1,000,000 Requests»
  0 USD · «AWS Lambda - Compute Free Tier - 400,000 GB-Seconds»

== 4 · ¿Cuánto duran los créditos? (encendido 24/7, precio de lista, tope del plan: 6 meses) ==
  A · aprender: 1 t3.micro + su IPv4 + disco de 30 GB
      t3.micro 24/7                          7.59 USD/mes
      IPv4 pública (dentro de las 750 h)     0.00 USD/mes
      disco gp3 30 GB                        2.40 USD/mes
      TOTAL                                  9.99 USD/mes   (0.33 USD/día)
      100 USD: alcanzan 10.0 meses → manda el plazo: a los 6 meses sobran 40.05 USD
      200 USD: alcanzan 20.0 meses → manda el plazo: a los 6 meses sobran 140.05 USD
  B · web con base de datos: t3.small + RDS db.t4g.micro
      t3.small 24/7                         15.18 USD/mes
      IPv4 pública (dentro de las 750 h)     0.00 USD/mes
      disco gp3 30 GB                        2.40 USD/mes
      RDS PostgreSQL db.t4g.micro           11.68 USD/mes
      RDS disco gp3 20 GB                    2.30 USD/mes
      TOTAL                                 31.56 USD/mes   (1.04 USD/día)
      100 USD: se acaban en 3.2 meses (día 96)
      200 USD: alcanzan 6.3 meses → manda el plazo: a los 6 meses sobran 10.62 USD
  C · la de un tutorial: B + NAT gateway + balanceador
      t3.small 24/7                         15.18 USD/mes
      disco gp3 30 GB                        2.40 USD/mes
      RDS PostgreSQL db.t4g.micro           11.68 USD/mes
      RDS disco gp3 20 GB                    2.30 USD/mes
      NAT gateway (sin tráfico)             32.85 USD/mes
      2 IPv4 (máquina + NAT) − 750 h         3.55 USD/mes
      ALB (sin tráfico ni sus IP)           16.43 USD/mes
      TOTAL                                 84.39 USD/mes   (2.77 USD/día)
      100 USD: se acaban en 1.2 meses (día 36)
      200 USD: se acaban en 2.4 meses (día 72)
  D · la grande «elegible»: m7i-flex.large + IPv4 + 30 GB
      m7i-flex.large 24/7                   69.90 USD/mes
      IPv4 pública (dentro de las 750 h)     0.00 USD/mes
      disco gp3 30 GB                        2.40 USD/mes
      TOTAL                                 72.30 USD/mes   (2.38 USD/día)
      100 USD: se acaban en 1.4 meses (día 42)
      200 USD: se acaban en 2.8 meses (día 84)

== 5 · El peso del NAT en el escenario C ==
  NAT + la IPv4 de más: 36.40 USD/mes de 84.39: 43 %
  con 1 GB/día por el NAT: +1.35 USD/mes

  precios: lista pública de AWS us-east-1 · EC2 2026-10-28 · VPC 2026-10-16 · RDS 2026-10-29 · ELB 2026-09-11 · DataTransfer 2026-09-16 · Lambda 2026-10-22
```

## Demos contra moto (correr.py)


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

