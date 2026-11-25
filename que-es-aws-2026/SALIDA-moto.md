# SALIDA — ¿Qué es AWS? (693) (demos ejecutadas)

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
