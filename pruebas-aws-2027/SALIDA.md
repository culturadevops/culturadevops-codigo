# SALIDA — AWS sin cuenta (vídeo 413)

Generado 2026-10-13 22:03 UTC con `python correr.py`. CLI oficial contra moto; moto no es AWS.

## 1 · La herramienta

### versión

`$ aws --version`

```
aws-cli/2.38.0 Python/3.14.6 Linux/6.18.33.2-microsoft-standard-WSL2 docker/x86_64.amzn.2023
```

### tamaño de moto

`$ docker image inspect -f {{.Size}} motoserver/moto`

```
104346363
```

## 2 · Lo primero en una cuenta nueva: un presupuesto con aviso

### crear el presupuesto: 10 USD al mes, aviso al 80 %

`$ aws budgets create-budget --account-id 123456789012 --budget file://presupuesto.json --notifications-with-subscribers file://aviso.json`

```

```
(código de salida 0)

### comprobarlo

`$ aws budgets describe-budgets --account-id 123456789012 --query …`

```
tope-mensual	10	USD	MONTHLY
```
(código de salida 0)

## 3 · Permisos mínimos

### la política del usuario «lector»

`$ cat lectura.json`

```
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": "s3:GetObject",
      "Resource": "arn:aws:s3:::facturas/*"
    }
  ]
}
```
(código de salida 0)

### lector: leer la factura

`$ aws s3 cp s3://facturas/f1.txt -   (como lector)`

```
factura 2027-001
```
(código de salida 0)

### lector: listar los buckets

`$ aws s3 ls   (como lector)`

```
aws: [ERROR]: An error occurred (AccessDenied) when calling the ListBuckets operation: Access Denied
```
(código de salida 254)

### lector: borrar la factura

`$ aws s3 rm s3://facturas/f1.txt   (como lector)`

```
delete failed: s3://facturas/f1.txt An error occurred (AccessDenied) when calling the DeleteObject operation: Access Denied
```
(código de salida 1)

### ¿sigue ahí?

`$ aws s3 ls s3://facturas/   (como admin)`

```
2026-10-13 22:03:38         18 f1.txt
```
(código de salida 0)

## 4 · Las regiones son independientes

### una tabla en us-east-1

`$ aws dynamodb create-table --table-name pedidos … --region us-east-1`

```
pedidos	ACTIVE
```
(código de salida 0)

### las tablas de us-east-1

`$ aws dynamodb list-tables --region us-east-1`

```
TABLENAMES	pedidos
```
(código de salida 0)

### las tablas de us-west-2

`$ aws dynamodb list-tables --region us-west-2`

```
{
    "TableNames": []
}
```
(código de salida 0)

> Si us-east-1 se cae, lo que solo vive ahí se cae con ella.
