import boto3  # el SDK que ya trae la imagen de Lambda (no se instala nada)

# Fuera del handler: se ejecuta en el INIT, una vez por entorno, como recomienda AWS.
s3 = boto3.client("s3", region_name="us-east-1")
dynamo = boto3.client("dynamodb", region_name="us-east-1")
INVOCACIONES = 0


def suma(n):
    s = 0
    for i in range(1, n + 1):
        s += (i * i) % 1000003
    return s


def handler(event, context):
    global INVOCACIONES
    INVOCACIONES += 1
    # No llama a AWS: solo comprueba que los clientes existen. Mide el coste de cargarlos.
    clientes = [s3.meta.service_model.service_name, dynamo.meta.service_model.service_name]
    return {"lang": "python", "fn": "sdk", "suma": suma(10000), "clientes": clientes, "invocacion": INVOCACIONES}
