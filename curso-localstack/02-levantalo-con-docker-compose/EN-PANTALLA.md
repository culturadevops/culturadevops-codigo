# Levanta AWS en local con Docker Compose (12 líneas explicadas una a una) — lo que sale en pantalla

Comandos y salidas **tal y como salen en las terminales del vídeo**, en el mismo orden.
Se sacaron automáticamente del guion del vídeo; no se escribió nada de memoria.
Las líneas con `$` son lo que tecleas; el resto es la salida que se midió al grabarlo
(tus hashes, tiempos e IDs van a ser otros).

## 1. docker-compose.yml

```console
services:
  localstack:
    image: localstack/localstack:3.8
    container_name: labaws
    ports:
      - "4566:4566"
    environment:
      - SERVICES=s3,dynamodb,lambda,apigateway,iam,logs,sts
      - DEBUG=0
    volumes:
      - "./datos:/var/lib/localstack"
      - "/var/run/docker.sock:/var/run/docker.sock"
```

## 2. levantando el laboratorio

```console
$ docker compose up -d

Network trabajo_default  Created
Container labaws  Created
Container labaws  Started

real    0m0.383s
```

## 3. tres formas de saber si está vivo

```console
$ docker ps
labaws   Up 11 seconds (healthy)

$ curl localhost:4566/_localstack/health
{"services": {"s3": "available", ...},
 "version": "3.8.1"}

$ aws --endpoint-url=http://localhost:4566 \
$     sts get-caller-identity
{"Account": "000000000000"}
```

## 4. el arranque, con la variable copiada

```console
$ docker logs labaws

LocalStack version: 3.8.1

WARN  localstack.deprecations :
LAMBDA_EXECUTOR is deprecated (since 2.0.0)
and will be removed in upcoming releases

Please mount the Docker socket ...
```

## 5. el arranque, sin la variable

```console
$ docker logs labaws

LocalStack version: 3.8.1
LocalStack build date: 2024-10-08

Ready.
```

## 6. y Lambda sigue funcionando

```console
$ aws --endpoint-url=$L lambda create-function ...
Pending

$ aws --endpoint-url=$L lambda invoke --function-name prueba salida.json
200

$ cat salida.json
{"statusCode": 200,
 "body": "hola sin la variable"}
```

## 7. tropiezo 1 · el puerto está ocupado

```console
$ docker compose up -d

Error response from daemon:
driver failed programming external
connectivity on endpoint labaws

Bind for 0.0.0.0:4566 failed:
port is already allocated
```

## 8. tropiezo 2 · esa versión no existe

```console
$ docker compose up -d

Error response from daemon:
failed to resolve reference
"docker.io/localstack/localstack:9.9"

not found
```
