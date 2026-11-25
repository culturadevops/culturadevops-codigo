# SALIDA — Curso de cloud desde cero · 2 · los servicios básicos (demos ejecutadas)

Generado por `python correr.py`. **No se edita a mano.**

- fecha: 2026-10-18 14:26 UTC
- aws-cli/2.36.5 Python/3.14.6 Windows/11 exe/AMD64
- moto 5.2.3 (emulador de la API de AWS)
- moto emula la API, no la factura ni todos los valores por defecto.

## Red: una VPC y una subred

`$ aws ec2 create-vpc --cidr-block 10.0.0.0/16 --query Vpc.VpcId --output text`

```
vpc-819f7694965d8bd78
```

`$ aws ec2 create-subnet --vpc-id vpc-819f7694965d8bd78 --cidr-block 10.0.1.0/24 --query Subnet.SubnetId --output text`

```
subnet-08ea8a22c68174262
```

## Seguridad de red: solo HTTPS desde internet

`$ aws ec2 create-security-group --group-name web --description solo https --vpc-id vpc-819f7694965d8bd78 --query GroupId --output text`

```
sg-b4d3328850dc1941a
```

`$ aws ec2 authorize-security-group-ingress --group-id sg-b4d3328850dc1941a --protocol tcp --port 443 --cidr 0.0.0.0/0 --query SecurityGroupRules[].{Puerto:FromPort,Desde:CidrIpv4}`

```
[
    {
        "Puerto": 443,
        "Desde": "0.0.0.0/0"
    }
]
```

## Cómputo: una máquina en esa subred

`$ aws ec2 run-instances --image-id ami-12c6146b --instance-type t3.micro --subnet-id subnet-08ea8a22c68174262 --security-group-ids sg-b4d3328850dc1941a --query Instances[].{Id:InstanceId,Subred:SubnetId,IP:PrivateIpAddress}`

```
[
    {
        "Id": "i-2b96e07fa920c6119",
        "Subred": "subnet-08ea8a22c68174262",
        "IP": "10.0.1.4"
    }
]
```

## Almacenamiento: un bucket para archivos

`$ aws s3api create-bucket --bucket archivos-app-cultura`

```
{
    "Location": "/archivos-app-cultura"
}
```

## Identidad: un rol que solo puede LEER ese bucket

`$ cat permiso.json`

```
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "s3:GetObject"
      ],
      "Resource": "arn:aws:s3:::archivos-app-cultura/*"
    }
  ]
}
```

`$ aws iam create-role --role-name app-lee-archivos --assume-role-policy-document file://confianza.json --query Role.Arn --output text`

```
arn:aws:iam::123456789012:role/app-lee-archivos
```

`$ aws iam put-role-policy --role-name app-lee-archivos --policy-name solo-leer --policy-document file://permiso.json`

```
(sin salida)
```

`$ aws iam list-role-policies --role-name app-lee-archivos`

```
{
    "PolicyNames": [
        "solo-leer"
    ]
}
```
