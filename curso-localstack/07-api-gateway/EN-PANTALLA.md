# API Gateway, Lambda y DynamoDB juntos en tu portátil, sin nube — lo que sale en pantalla

Comandos y salidas **tal y como salen en las terminales del vídeo**, en el mismo orden.
Se sacaron automáticamente del guion del vídeo; no se escribió nada de memoria.
Las líneas con `$` son lo que tecleas; el resto es la salida que se midió al grabarlo
(tus hashes, tiempos e IDs van a ser otros).

## 1. la función del contador

```console
def handler(event, context):
    d = boto3.resource(
        "dynamodb",
        endpoint_url=ENDPOINT)
    t = d.Table("visitas")
    r = t.update_item(
        Key={"pagina": "/"},
        UpdateExpression="ADD contador :u",
        ...)
```

## 2. con la dirección de siempre

```console
endpoint_url="http://localhost:4566"

$ aws --profile lab lambda invoke \
$     --function-name contador-mal salida.json

200    Unhandled

"Task timed out after 20.00 seconds"
```

## 3. la dirección que sí vale desde dentro

```console
# desde tu terminal:
  "http://localhost:4566"

# desde dentro de una funcion:
  "http://localhost.localstack.cloud:4566"
```

## 4. la función, funcionando

```console
$ aws --profile lab lambda invoke \
$     --function-name contador salida.json
200    None

$ cat salida.json
{"visitas": 1, "ruta": "?"}
```

## 5. paso 1 · crear la API

```console
$ aws --profile lab apigateway create-rest-api \
$     --name contador-api \
$     --query 'id' --output text

l0gpe6196x
```

## 6. paso 2 · decir qué acepta

```console
$ aws --profile lab apigateway put-method \
$     --rest-api-id $API \
$     --resource-id $RAIZ \
$     --http-method GET \
$     --authorization-type NONE
```

## 7. paso 3 · atarla a la función

```console
$ aws --profile lab apigateway put-integration \
$     --rest-api-id $API --resource-id $RAIZ \
$     --http-method GET \
$     --type AWS_PROXY \
$     --integration-http-method POST \
$     --uri arn:aws:apigateway:us-east-1:lambda:
$       path/2015-03-31/functions/...:contador/
$       invocations
```

## 8. paso 4 · publicarla

```console
$ aws --profile lab apigateway create-deployment \
$     --rest-api-id $API \
$     --stage-name dev

99kv7ngd8o
```

## 9. una ruta nueva SIN publicar

```console
$ # creo la ruta /nueva y su conexion
$ # y NO ejecuto create-deployment

$ curl $URL/nueva

{"visitas": 7, "ruta": "/nueva"}
```

## 10. una ruta que acepta cualquier nombre

```console
$ aws --profile lab apigateway create-resource \
$     --rest-api-id $API \
$     --parent-id $RAIZ \
$     --path-part '{pagina}'

$ # y las mismas dos ordenes de antes:
$ # put-method y put-integration
```

## 11. un contador por página

```console
$ curl $URL/blog
{"visitas": 5, "ruta": "/blog"}

$ curl $URL/tienda
{"visitas": 6, "ruta": "/tienda"}
```

## 12. la dirección aquí y allí

```console
# en la nube:
https://<id>.execute-api.<region>
   .amazonaws.com/dev/

# aqui:
http://localhost:4566/restapis/<id>
   /dev/_user_request_/
```

## 13. tres visitas seguidas

```console
$ curl $URL
{"visitas": 2, "ruta": "/"}

$ curl $URL
{"visitas": 3, "ruta": "/"}

$ curl $URL
{"visitas": 4, "ruta": "/"}
```

## 14. la prueba, en la base de datos

```console
$ aws --profile lab dynamodb get-item \
$     --table-name visitas \
$     --key '{"pagina":{"S":"/"}}'

4
```
