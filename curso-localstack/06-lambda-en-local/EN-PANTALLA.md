# Lambda en local con LocalStack: desplegar, invocar y encontrar los logs — lo que sale en pantalla

Comandos y salidas **tal y como salen en las terminales del vídeo**, en el mismo orden.
Se sacaron automáticamente del guion del vídeo; no se escribió nada de memoria.
Las líneas con `$` son lo que tecleas; el resto es la salida que se midió al grabarlo
(tus hashes, tiempos e IDs van a ser otros).

## 1. handler.py

```console
import json

def handler(event, context):
    nombre = event.get("nombre", "mundo")
    return {
      "statusCode": 200,
      "body": json.dumps({
        "saludo": "hola " + nombre,
        "memoria": context.memory_limit_in_mb})}
```

## 2. empaquetar sin instalar nada

```console
$ python -c "import zipfile; \
$   zipfile.ZipFile('fn.zip','w')\
$   .write('handler.py')"

# fn.zip listo, sin instalar nada
```

## 3. crear la función

```console
$ aws --profile lab lambda create-function \
$     --function-name saluda \
$     --runtime python3.11 \
$     --handler handler.handler \
$     --role arn:aws:iam::000000000000:role/lambda-role \
$     --zip-file fileb://fn.zip

Pending    128    3
```

## 4. esperar a que esté lista

```console
$ aws --profile lab lambda \
$     wait function-active-v2 \
$     --function-name saluda

$ # y ahora sí:
Active    128    3
```

## 5. invocar con datos

```console
$ aws --profile lab lambda invoke \
$     --function-name saluda \
$     --payload '{"nombre":"ana"}' \
$     --cli-binary-format raw-in-base64-out \
$     salida.json

200

{"saludo": "hola ana", "memoria": "128"}
```

## 6. cinco invocaciones seguidas

```console
invocacion 1: 0.42 s
invocacion 2: 0.39 s
invocacion 3: 0.39 s
invocacion 4: 0.39 s
invocacion 5: 0.38 s
```

## 7. ahora sí, en frío de verdad

```console
$ docker rm -f labaws-lambda-saluda-...

invocacion 1: 62.19 s   <- en frio
invocacion 2: 0.40 s
invocacion 3: 0.38 s
```

## 8. una función que revienta

```console
def handler(event, context):
    return 1 / 0

$ aws --profile lab lambda invoke \
$     --function-name rota salida.json

200    Unhandled
```

## 9. donde sí está la verdad

```console
$ cat salida.json

  "errorType": "ZeroDivisionError",
  "errorMessage": "division by zero"
```

## 10. una función que tarda demasiado

```console
def handler(event, context):
    time.sleep(6)

200    Unhandled

"errorMessage": "Task timed out
 after 3.00 seconds"
```

## 11. los grupos de registro existen

```console
$ aws --profile lab logs describe-log-groups

/aws/lambda/lenta
/aws/lambda/rota
/aws/lambda/saluda
```

## 12. y al pedir su contenido

```console
$ aws --profile lab logs describe-log-streams \
$     --log-group-name "/aws/lambda/saluda"

An error occurred
(ResourceNotFoundException)
The specified log group does not exist
```

## 13. ahí no está

```console
$ docker logs labaws | grep ESTOY-DENTRO

# 0 coincidencias
```

## 14. el plan B que sí funciona

```console
$ docker ps -a --format '{{.Names}}' \
$   | grep lambda-habla
labaws-lambda-habla-0d47c261abbb...

$ docker logs labaws-lambda-habla-0d47...

ESTOY-DENTRO-DE-LA-FUNCION
```

## 15. actualizar solo el código

```console
$ # cambio el archivo y lo vuelvo a comprimir
$ aws --profile lab lambda \
$     update-function-code \
$     --function-name saluda \
$     --zip-file fileb://fn.zip

InProgress
```

## 16. y ya responde la versión nueva

```console
$ aws --profile lab lambda invoke \
$     --function-name saluda salida.json
$ cat salida.json

{"version": "v2",
 "entorno": "(sin variable)"}
```

## 17. variables, memoria y tiempo, de una vez

```console
$ aws --profile lab lambda \
$     update-function-configuration \
$     --function-name saluda \
$     --environment \
$       'Variables={SALUDO=hola-desde-el-entorno}' \
$     --memory-size 512 --timeout 30

512    30
```

## 18. la variable llega a la función

```console
$ aws --profile lab lambda invoke \
$     --function-name saluda salida.json
$ cat salida.json

{"version": "v2",
 "entorno": "hola-desde-el-entorno"}
```

## 19. una función, un contenedor

```console
$ docker ps -a --format '{{.Names}}'

labaws
labaws-lambda-saluda-f7d12427ef50...
labaws-lambda-habla-0d47c261abbb...
labaws-lambda-rota-9b31a0c4d7f2...
```
