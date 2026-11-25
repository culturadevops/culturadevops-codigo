# SALIDA — vídeo 693 · ¿Qué es AWS?

Generado por `python ejecutar_todo.py`. **No se edita a mano.** Importes: precio de lista × uso (estimación).

- fecha: 2026-10-29 12:53 UTC

## Precios (calculo.py)

```
== 1 · Regiones en la lista de precios de EC2 (region_index.json, publicado 2026-10-28) ==
  códigos en el índice: 107
  con forma de región (xx-nombre-N): 36 · de ellas GovCloud: 2 · comerciales: 34
  el resto (71) cuelga de una región (zonas locales y Wavelength), p. ej.: af-south-1-los-1, ap-northeast-1-tpe-1, ap-northeast-1-wl1-kix1, ap-northeast-1-wl1-nrt1…
  en Latinoamérica: mx-central-1, sa-east-1

== 2 · La misma máquina y el mismo GB, en tres regiones (Linux bajo demanda · S3 Standard) ==
  us-east-1     Virginia del Norte   t3.micro 0.0104 USD/h =  7.59 USD/mes (+0 %) · S3 0.0230 USD/GB-mes   «$0.0104 per On Demand Linux t3.micro Instance Hour»
  mx-central-1  México (Central)     t3.micro 0.0109 USD/h =  7.96 USD/mes (+5 %) · S3 0.0242 USD/GB-mes   «$0.0109 per On Demand Linux t3.micro Instance Hour»
  sa-east-1     São Paulo            t3.micro 0.0168 USD/h = 12.26 USD/mes (+62 %) · S3 0.0405 USD/GB-mes   «$0.0168 per On Demand Linux t3.micro Instance Hour»
  publicación: EC2 2026-10-28 · S3 2026-10-15

== 3 · Pagar por uso: la misma t3.micro, según cuánto la tengas encendida (us-east-1) ==
  10 minutos                   0.0017 USD
  1 hora                       0.0104 USD
  8 h × 22 días laborables     1.8304 USD
  todo el mes (730 h)          7.5920 USD
  (Linux se cobra por segundo, con un mínimo de 60 s: página de precios bajo demanda de EC2)

== 4 · Lambda: se paga por petición y por GB-segundo; el primer millón es gratis cada mes ==
  1,000,000 peticiones · 128 MB · 200 ms →    25,000 GB-s →  0.00 USD/mes
  5,000,000 peticiones · 512 MB · 300 ms →   750,000 GB-s →  6.63 USD/mes
  precio: 0.20 USD por millón de peticiones · 0.0000166667 USD por GB-s

== 5 · Lo básico de cada servicio, a precio de lista (us-east-1) ==
  EC2 t3.micro, el mes                               7.592 USD
  IPv4 pública, el mes                               3.650 USD
  disco gp3, por GB-mes                              0.080 USD
  S3 Standard, por GB-mes                            0.023 USD
  RDS PostgreSQL db.t4g.micro, el mes               11.680 USD
  Salida a internet, por GB (tras 100 GB gratis)     0.090 USD
  IAM y VPC (la red en sí)                           0.000 USD
  (IAM no tiene oferta en la lista de precios: la guía de IAM dice «no additional charge». La guía de VPC: «There's no additional charge for using a VPC»; sí cobran cosas dentro, como el NAT o las IPv4)

== 6 · Un primer proyecto, al mes (us-east-1, precio normal, sin contar la capa gratuita) ==
  t3.micro 24/7                                7.59 USD
  su IPv4 pública                              3.65 USD
  disco gp3 de 8 GB                            0.64 USD
  S3: 5 GB                                     0.11 USD
  salida: 20 GB (dentro de los 100 gratis)     0.00 USD
  TOTAL                                       12.00 USD

  precios: lista pública de AWS · EC2 2026-10-28 · VPC 2026-10-16 · S3 2026-10-15 · RDS 2026-10-29 · Lambda 2026-10-22 · DataTransfer 2026-09-16
```

## Demos contra moto (correr.py)


Generado por `python correr.py`. **No se edita a mano.**

- fecha: 2026-10-29 12:53 UTC
- aws-cli/2.36.5 Python/3.14.6 Windows/11 exe/AMD64
- moto 5.2.3 (emulador de la API de AWS)
- moto emula la API, no la factura ni todos los valores por defecto.

## 1 · Una región por dentro: sus zonas de disponibilidad

`$ aws ec2 describe-availability-zones --region us-east-1 --query AvailabilityZones[].ZoneName --output text`

```
us-east-1a	us-east-1b	us-east-1c	us-east-1d	us-east-1e	us-east-1f
```

`$ aws ec2 describe-availability-zones --region sa-east-1 --query AvailabilityZones[].ZoneName --output text`

```
sa-east-1a	sa-east-1b	sa-east-1c
```

## 2 · IAM: un usuario que solo puede leer un bucket

`$ aws iam create-user --user-name ana --query User.Arn --output text`

```
arn:aws:iam::123456789012:user/ana
```

`$ aws iam create-policy --policy-name leer-bucket --policy-document file://permiso.json --query Policy.Arn --output text`

```
arn:aws:iam::123456789012:policy/leer-bucket
```

`$ aws iam attach-user-policy --user-name ana --policy-arn arn:aws:iam::123456789012:policy/leer-bucket`

```
(sin salida)
```

`$ aws iam list-attached-user-policies --user-name ana --query AttachedPolicies[].PolicyName --output text`

```
leer-bucket
```

## 3 · VPC: tu red privada, con una subred en una zona

`$ aws ec2 create-vpc --cidr-block 10.0.0.0/16 --query Vpc.VpcId --output text`

```
vpc-a8d4e677eb54bcb30
```

`$ aws ec2 create-subnet --vpc-id vpc-a8d4e677eb54bcb30 --cidr-block 10.0.1.0/24 --availability-zone us-east-1a --query Subnet.[SubnetId,AvailabilityZone,CidrBlock] --output text`

```
subnet-c488857503e3c6147	us-east-1a	10.0.1.0/24
```

## 4 · EC2: un servidor t3.micro en esa subred

`$ aws ec2 run-instances --image-id ami-12c6146b --instance-type t3.micro --subnet-id subnet-c488857503e3c6147 --query Instances[].[InstanceId,InstanceType,Placement.AvailabilityZone,State.Name] --output text`

```
i-c1ab97c7273cb0123	t3.micro	us-east-1a	pending
```

## 5 · S3: un bucket y un archivo

`$ aws s3api create-bucket --bucket mi-primer-bucket-693 --query Location --output text`

```
/mi-primer-bucket-693
```

`$ aws s3 cp hola.txt s3://mi-primer-bucket-693/hola.txt --no-progress`

```
upload: .\hola.txt to s3://mi-primer-bucket-693/hola.txt
```

`$ aws s3 ls s3://mi-primer-bucket-693/`

```
2026-10-29 07:53:34         10 hola.txt
```

## 6 · RDS: una base de datos PostgreSQL administrada

`$ aws rds create-db-instance --db-instance-identifier app --engine postgres --db-instance-class db.t4g.micro --allocated-storage 20 --master-username app --master-user-password no-es-real-123 --query DBInstance.[DBInstanceIdentifier,Engine,DBInstanceClass,AllocatedStorage] --output text`

```
app	postgres	db.t4g.micro	20
```

## 7 · Lambda: una función, sin servidor que administrar

`$ aws lambda create-function --function-name hola --runtime python3.12 --role arn:aws:iam::123456789012:role/fn-hola --handler app.handler --zip-file fileb://fn.zip --memory-size 128 --query [FunctionName,Runtime,MemorySize] --output text`

```
hola	python3.12	128
```

## 8 · Pago por uso: parar la máquina

`$ aws ec2 stop-instances --instance-ids i-c1ab97c7273cb0123 --query StoppingInstances[].CurrentState.Name --output text`

```
stopping
```

`$ aws ec2 describe-volumes --query Volumes[].[VolumeId,Size,State] --output text`

```
vol-0261f68ad888f33eb	8	in-use
```

> Parada, la máquina no suma horas de cómputo; el disco sigue existiendo, y se cobra por GB-mes.

