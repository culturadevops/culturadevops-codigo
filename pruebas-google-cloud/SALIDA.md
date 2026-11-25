# SALIDA — Google Cloud en local (vídeo 411)

Generado 2026-10-13 22:02 UTC con `python correr.py`. Sin cuenta: imagen oficial `gcr.io/google.com/cloudsdktool/google-cloud-cli:emulators`.

## 1 · La herramienta

### versión de gcloud

`$ gcloud version`

```
Google Cloud SDK 589.0.0
beta 2026.10.09
bigtable
```
(código de salida 0)

### tamaño de la imagen

`$ docker image inspect -f {{.Size}} gcr.io/google.com/cloudsdktool/google-cloud-cli:emulators`

```
451541469
```

## 2 · Pub/Sub en local

### arranca el emulador

`$ gcloud beta emulators pubsub start --project=demo`

```
INFO: Server started, listening on 8085
```
(código de salida 0)

### crear un tema y una suscripción

`$ curl -X PUT …/topics/pedidos; curl -X PUT …/subscriptions/facturacion`

```
{
  "name": "projects/demo/topics/pedidos"
}

{
  "name": "projects/demo/subscriptions/facturacion",
  "topic": "projects/demo/topics/pedidos",
  "pushConfig": {
  },
  "ackDeadlineSeconds": 10,
  "messageRetentionDuration": "604800s"
}
```
(código de salida 0)

### publicar dos mensajes

`$ curl -X POST …/topics/pedidos:publish`

```
{
  "messageIds": ["1", "2"]
}
```
(código de salida 0)

### sacarlos (sin confirmar todavía)

`$ curl -X POST …/subscriptions/facturacion:pull`

```
pedido 1001
pedido 1002
```

### confirmar solo el primero

`$ curl -X POST …/subscriptions/facturacion:acknowledge`

```
{
}
confirmado
```
(código de salida 0)

### 13 segundos después, volver a sacar

`$ sleep 13; curl -X POST …/subscriptions/facturacion:pull`

```
pedido 1002
```

> El plazo de confirmación era de 10 s: el que no se confirmó vuelve a entregarse.

## 3 · Firestore en local

### guardar un documento

`$ curl -X POST …/documents/clientes?documentId=ana`

```
"name": "projects/demo/databases/(default)/documents/clientes/ana",
      "stringValue": "Ana"
      "integerValue": "3"
```
(código de salida 0)

### leerlo

`$ curl …/documents/clientes/ana`

```
"stringValue": "Ana"
      "integerValue": "3"
```
(código de salida 0)
