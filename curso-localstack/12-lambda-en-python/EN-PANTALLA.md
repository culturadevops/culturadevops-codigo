# Lambda en Python con dependencias: empaquetar sin el error de importación — lo que sale en pantalla

Comandos y salidas **tal y como salen en las terminales del vídeo**, en el mismo orden.
Se sacaron automáticamente del guion del vídeo; no se escribió nada de memoria.
Las líneas con `$` son lo que tecleas; el resto es la salida que se midió al grabarlo
(tus hashes, tiempos e IDs van a ser otros).

## 1. app.py · con una dependencia externa

```console
from tabulate import tabulate

def handler(event, context):
    filas = [["ana", 3], ["luis", 1]]
    return {
        "statusCode": 200,
        "body": tabulate(filas,
            headers=["cliente", "pedidos"])}
```

## 2. se despliega sin problemas

```console
$ python -c "import zipfile; ..."
$ aws --profile lab lambda create-function \
$     --function-name contabla ...

Pending
# y un momento despues: Active
```

## 3. y al invocarla

```console
$ aws --profile lab lambda invoke \
$     --function-name contabla salida.json
200    Unhandled

Runtime.ImportModuleError
Unable to import module 'app':
No module named 'tabulate'
```

## 4. instalar en una carpeta

```console
$ mkdir paquete
$ python -m pip install \
$     --target paquete tabulate

$ cp app.py paquete/

# ahora paquete/ tiene tu codigo
# y la biblioteca, juntos
```

## 5. y ahora sí funciona

```console
archivos en el zip: 12   tamaño: 136 KB

$ aws --profile lab lambda \
$     update-function-code ...
200    None

cliente      pedidos
---------  ---------
ana                3
luis               1
```

## 6. probar sin desplegar

```console
import sys; sys.path.insert(0, "paquete")
from app import handler

class Contexto:
    memory_limit_in_mb = 128
    aws_request_id = "local-1"

r = handler({"nombre": "ana"}, Contexto())
print(r)
```

## 7. separado en dos

```console
def resumen(filas):
    # el trabajo de verdad
    return tabulate(filas, ...)

def handler(event, context):
    # solo traduce la peticion
    filas = event.get("filas", [])
    return {"statusCode": 200,
            "body": resumen(filas)}
```

## 8. la receta de los registros

```console
$ docker ps -a --format '{{.Names}}' \
$   | grep lambda-contabla
labaws-lambda-contabla-8f2a...

$ docker logs labaws-lambda-contabla-8f2a...

# aqui esta todo lo que imprime
```

## 9. desplegar.sh

```console
rm -rf paquete && mkdir paquete
pip install -q --target paquete -r requisitos.txt
cp app.py paquete/
python empaquetar.py
aws --profile lab lambda \
    update-function-code \
    --function-name contabla \
    --zip-file fileb://fn.zip
```
