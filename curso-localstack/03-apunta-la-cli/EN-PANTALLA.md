# Apunta la CLI de AWS a LocalStack sin acabar en tu cuenta real — lo que sale en pantalla

Comandos y salidas **tal y como salen en las terminales del vídeo**, en el mismo orden.
Se sacaron automáticamente del guion del vídeo; no se escribió nada de memoria.
Las líneas con `$` son lo que tecleas; el resto es la salida que se midió al grabarlo
(tus hashes, tiempos e IDs van a ser otros).

## 1. forma 1 · la bandera en cada comando

```console
$ aws --endpoint-url=http://localhost:4566 \
$     s3 ls

$ aws --endpoint-url=http://localhost:4566 \
$     dynamodb list-tables

$ aws --endpoint-url=http://localhost:4566 \
$     lambda list-functions
```

## 2. forma 2 · una variable de entorno

```console
$ export AWS_ENDPOINT_URL=http://localhost:4566

$ aws sts get-caller-identity
{
    "Account": "000000000000",
    "Arn": "arn:aws:iam::000000000000:root"
}
```

## 3. forma 3 · un perfil con la dirección dentro

```console
# ~/.aws/config
[profile lab]
region = us-east-1
output = json
endpoint_url = http://localhost:4566

# ~/.aws/credentials
[lab]
aws_access_key_id = test
aws_secret_access_key = test
```

## 4. cómo quedan los comandos

```console
$ aws --profile lab sts get-caller-identity
{"Account": "000000000000"}

$ aws --profile lab s3 mb s3://prueba-perfil
make_bucket: prueba-perfil

$ aws --profile lab dynamodb list-tables
{"TableNames": []}
```

## 5. dos perfiles casi idénticos

```console
[profile lab]
region = us-east-1
endpoint_url = http://localhost:4566

[profile lab-malo]
region = us-east-1
# falta la linea de arriba, y ya esta
```

## 6. el mismo comando, dos destinos

```console
$ aws --profile lab sts get-caller-identity
{"Account": "000000000000"}

$ aws --profile lab-malo sts get-caller-identity

aws: [ERROR]: An error occurred
(InvalidClientTokenId) ... The security
token included in the request is invalid.
```

## 7. la comprobación de tres segundos

```console
$ aws --profile lab sts get-caller-identity

{
    "UserId": "AKIAIOSFODNN7EXAMPLE",
    "Account": "000000000000",
    "Arn": "arn:aws:iam::000000000000:root"
}
```

## 8. el mismo script, dos destinos

```console
$ ./desplegar.sh --profile lab
... contra tu contenedor, gratis

$ ./desplegar.sh --profile produccion
... contra la cuenta de verdad

# el script es el mismo archivo
```

## 9. el mismo perfil, escrito distinto

```console
# en config va con la palabra profile
[profile lab]
endpoint_url = http://localhost:4566

# en credentials va SIN ella
[lab]
aws_access_key_id = test
```

## 10. con la sección mal escrita

```console
$ aws --profile lab sts get-caller-identity

aws: [ERROR]: An error occurred
(InvalidClientTokenId) ... The security
token included in the request is invalid.
```
