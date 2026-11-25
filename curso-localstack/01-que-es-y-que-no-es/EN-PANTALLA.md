# Qué es LocalStack y qué no es: AWS entero en tu portátil, sin tarjeta — lo que sale en pantalla

Comandos y salidas **tal y como salen en las terminales del vídeo**, en el mismo orden.
Se sacaron automáticamente del guion del vídeo; no se escribió nada de memoria.
Las líneas con `$` son lo que tecleas; el resto es la salida que se midió al grabarlo
(tus hashes, tiempos e IDs van a ser otros).

## 1. preguntándole a AWS quién soy

```console
$ export AWS_ACCESS_KEY_ID=test
$ export AWS_SECRET_ACCESS_KEY=test
$ aws --endpoint-url=http://localhost:4566 \
$     sts get-caller-identity

{
  "Account": "000000000000",
  "Arn": "arn:aws:iam::000000000000:root"
}
```

## 2. qué servicios ofrece

```console
$ curl localhost:4566/_localstack/health

version: 3.8.1
servicios: 35

s3, dynamodb, lambda, apigateway,
iam, logs, sts, kinesis, dynamodbstreams
```

## 3. S3, de verdad

```console
$ aws s3 mb s3://mi-primer-bucket
make_bucket: mi-primer-bucket

$ aws s3 cp prueba.txt s3://mi-primer-bucket/
$ aws s3 cp s3://mi-primer-bucket/prueba.txt -
hola desde mi portatil
```

## 4. una arquitectura entera en tu portátil

```console
$ curl localhost:4566/restapis/y4k56gxekh/dev/_user_request_/

hola desde una Lambda en mi portatil
```

## 5. todo por el mismo puerto

```console
$ aws s3 ls           --endpoint-url=http://localhost:4566
$ aws dynamodb ...    --endpoint-url=http://localhost:4566
$ aws lambda ...      --endpoint-url=http://localhost:4566

mismo puerto para los tres
```

## 6. lo que pasa con la imagen «latest»

```console
LocalStack version: 2026.7.2

License activation failed!
No credentials were found in the environment.

Localstack returning with exit code 55
```

## 7. la versión que sí arranca sola

```console
$ image: localstack/localstack:3.8

LocalStack version: 3.8.1
Ready.
```

## 8. el recuento por estado

```console
servicios: 35

desactivados ... 26
en marcha ......  6
disponibles ....  3
```

## 9. la línea que lo decide

```console
$ environment:
$   - SERVICES=s3,dynamodb,lambda,apigateway,iam,logs,sts
```
