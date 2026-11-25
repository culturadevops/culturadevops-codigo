# Conecta boto3 a LocalStack sin el error que comete todo el mundo — lo que sale en pantalla

Comandos y salidas **tal y como salen en las terminales del vídeo**, en el mismo orden.
Se sacaron automáticamente del guion del vídeo; no se escribió nada de memoria.
Las líneas con `$` son lo que tecleas; el resto es la salida que se midió al grabarlo
(tus hashes, tiempos e IDs van a ser otros).

## 1. lo que escribe todo el mundo

```console
import boto3

s3 = boto3.client("s3")
print(s3.list_buckets())
```

## 2. y esto es lo que contesta

```console
$ python mal.py

botocore.exceptions.ClientError:
An error occurred (InvalidAccessKeyId)
The AWS Access Key Id you provided
does not exist in our records.
```

## 3. la forma obvia

```console
import boto3

s3 = boto3.client(
    "s3",
    endpoint_url="http://localhost:4566",
    aws_access_key_id="test",
    aws_secret_access_key="test",
    region_name="us-east-1")
```

## 4. funcionando

```console
$ python bien.py

buckets: ['desde-python']
```

## 5. usando el perfil

```console
import boto3

s = boto3.Session(profile_name="lab")
s3 = s.client("s3")

# y ya esta. Sin direcciones ni claves.

con perfil: ['desde-python']
```

## 6. con la variable de entorno

```console
$ export AWS_ENDPOINT_URL=http://localhost:4566
$ python variable.py

con variable: ['desde-python']

# el codigo es el del principio,
# sin tocar una sola letra
```

## 7. la forma de bajo nivel

```console
s3 = sesion.client("s3")
s3.create_bucket(Bucket="x")
s3.list_buckets()

# los nombres son los de la nube,
# con mayusculas y todo
```

## 8. error 1 · has ido a la nube

```console
ClientError: (InvalidAccessKeyId)
The AWS Access Key Id you provided
does not exist in our records.

# traduccion: te falta la direccion
```

## 9. error 2 · no hay nadie ahí

```console
EndpointConnectionError:
Could not connect to the endpoint
URL: "http://localhost:4599/"

# el contenedor esta caido,
# o el puerto no es ese
```

## 10. error 3 · una parrafada de certificados

```console
SSLError: SSL validation failed for
https://localhost:4566/ hostname
'localhost' doesn't match either of
'localhost.localstack.cloud',
'*.s3.localhost.localstack.cloud',
'*.execute-api.localhost...',
... y cincuenta nombres mas
```

## 11. lab.py · el archivo que se importa

```console
import boto3

sesion = boto3.Session(profile_name="lab")

s3 = sesion.client("s3")
ddb = sesion.client("dynamodb")
fn = sesion.client("lambda")
```

## 12. y así queda un programa cualquiera

```console
from lab import s3

s3.create_bucket(Bucket="mis-cosas")
s3.upload_file("foto.jpg",
               "mis-cosas", "foto.jpg")

# y ya esta. Dos lineas de verdad.
```
