# Recibir un mensaje no lo saca de la cola: lo esconde (curso 4/8) — lo que sale en pantalla

Comandos y salidas **tal y como salen en las terminales del vídeo**, en el mismo orden.
Se sacaron automáticamente del guion del vídeo; no se escribió nada de memoria.
Las líneas con `$` son lo que tecleas; el resto es la salida que se midió al grabarlo
(tus hashes, tiempos e IDs van a ser otros).

## 1. mandar un mensaje · salida real

```console
$ aws ... sqs create-queue --queue-name trabajos
$ aws ... sqs send-message --queue-url ... \
$        --message-body 'procesa el pedido 42'
1d3cf5a2dcee492cb8398be401c1989b
```

## 2. primera recepcion · salida real

```console
$ aws ... sqs receive-message --queue-url ... \
$        --attribute-names All
[[
    "procesa el pedido 42",
    "1"                       <- veces entregado
]]
```

## 3. segunda recepcion, inmediata · salida real

```console
$ aws ... sqs receive-message --queue-url ...
null
```

## 4. los dos numeros que lo explican · salida real

```console
$ aws ... sqs get-queue-attributes --queue-url ... \
$        --attribute-names ApproximateNumberOfMessages \
$                         ApproximateNumberOfMessagesNotVisible
ApproximateNumberOfMessages:            0
ApproximateNumberOfMessagesNotVisible:  1
VisibilityTimeout:                     30
```

## 5. pedir mas tiempo mientras trabajas

```console
aws ... sqs change-message-visibility \
       --queue-url ... \
       --receipt-handle ... \
       --visibility-timeout 120
```

## 6. apuntar una cola a un tema · salida real

```console
$ aws ... sns create-topic --name avisos
$ aws ... sns subscribe --topic-arn ... \
$        --protocol sqs --notification-endpoint ...
arn:aws:sns:us-east-1:000000000000:avisos:00000001-...
```

## 7. lo que hay en la cola · salida real

```console
$ aws ... sqs receive-message --query 'Messages[0].Body'
{"Type":"Notification",
 "MessageId":"avisos-2",
 "TopicArn":"arn:aws:sns:...:avisos",
 "Message":"se cayo el disco",
 "Timestamp":"2026-09-03T18:53:34.973Z"}
```

## 8. el material del curso

```console
aws-cli/2.36.19  ·  la oficial de Amazon
nubecita:curso   ·  10,5 MB en disco
corrida: 2026-09-03 · salida-real.txt
```
