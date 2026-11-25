#!/bin/sh
# Corredor del curso «Tu nube local SIN licencias». Se ejecuta DENTRO del contenedor de la
# CLI OFICIAL de AWS (amazon/aws-cli), contra nubecita en la misma red de Docker.
#
# ESE ES EL ARGUMENTO DEL CURSO: quien habla con el doble es siempre el cliente de Amazon.
# Ni un parche, ni un «modo local». Lo unico que cambia es --endpoint-url.
set -u
export AWS_ACCESS_KEY_ID=prueba AWS_SECRET_ACCESS_KEY=prueba AWS_DEFAULT_REGION=us-east-1
A="aws --endpoint-url http://nubecita:4566"
t() { echo; echo "############ $1 ############"; }

t "ENTORNO"
aws --version

t "EP1 · el primer bucket contra tu propia nube"
$A s3 mb s3://fotos
$A s3 ls

t "EP2 · S3 NO tiene carpetas"
echo "un gato" > /tmp/gato.txt
mkdir -p /tmp/d && echo "enero" > /tmp/d/nota.txt
$A s3 cp /tmp/gato.txt s3://fotos/gato.txt --quiet
$A s3 cp /tmp/d/nota.txt s3://fotos/2026/enero/nota.txt --quiet
echo "-- ls plano: 2026/ aparece como PRE(fijo), que no es una carpeta --"
$A s3 ls s3://fotos/
echo "-- ls --recursive: la 'carpeta' era parte del NOMBRE --"
$A s3 ls s3://fotos/ --recursive
echo "-- la API cruda: el delimitador / es quien INVENTA las carpetas --"
$A s3api list-objects-v2 --bucket fotos --delimiter / --query 'CommonPrefixes[].Prefix'
echo "-- sin delimitador: la clave entera es el nombre --"
$A s3api list-objects-v2 --bucket fotos --query 'Contents[].Key'

t "EP3 · DynamoDB: otro protocolo, el MISMO puerto"
$A dynamodb create-table --table-name pedidos \
  --attribute-definitions AttributeName=cliente,AttributeType=S AttributeName=fecha,AttributeType=S \
  --key-schema AttributeName=cliente,KeyType=HASH AttributeName=fecha,KeyType=RANGE \
  --billing-mode PAY_PER_REQUEST --query 'TableDescription.TableName' --output text
$A dynamodb put-item --table-name pedidos --item '{"cliente":{"S":"ana"},"fecha":{"S":"2026-01-03"},"total":{"N":"42.5"}}'
$A dynamodb put-item --table-name pedidos --item '{"cliente":{"S":"ana"},"fecha":{"S":"2026-02-11"},"total":{"N":"17"}}'
$A dynamodb put-item --table-name pedidos --item '{"cliente":{"S":"luis"},"fecha":{"S":"2026-01-20"},"total":{"N":"99"}}'
echo "-- Query: SOLO la particion de ana, y ya viene ordenado --"
$A dynamodb query --table-name pedidos --key-condition-expression 'cliente = :c' \
  --expression-attribute-values '{":c":{"S":"ana"}}' --query 'Items[].fecha.S'
echo "-- Query con begins_with sobre la clave de ORDEN --"
$A dynamodb query --table-name pedidos \
  --key-condition-expression 'cliente = :c AND begins_with(fecha, :f)' \
  --expression-attribute-values '{":c":{"S":"ana"},":f":{"S":"2026-01"}}' --query 'Count'
echo "-- Scan: recorre la tabla ENTERA. Por eso se paga --"
$A dynamodb scan --table-name pedidos --select COUNT --query 'Count'

t "EP4 · SQS: recibir NO saca el mensaje, lo ESCONDE"
URL=$($A sqs create-queue --queue-name trabajos --query QueueUrl --output text)
$A sqs send-message --queue-url "$URL" --message-body 'procesa el pedido 42' --query 'MD5OfMessageBody' --output text
echo "-- 1a recepcion --"
$A sqs receive-message --queue-url "$URL" --attribute-names All --query 'Messages[].[Body,Attributes.ApproximateReceiveCount]'
echo "-- 2a recepcion INMEDIATA: no hay nada. No se perdio: esta invisible --"
$A sqs receive-message --queue-url "$URL" --query 'Messages'
$A sqs get-queue-attributes --queue-url "$URL" \
  --attribute-names ApproximateNumberOfMessages ApproximateNumberOfMessagesNotVisible \
  --query 'Attributes'

t "EP4b · SNS: publicas UNA vez, y llega dentro de un SOBRE"
TEMA=$($A sns create-topic --name avisos --query TopicArn --output text)
URL2=$($A sqs create-queue --queue-name buzon --query QueueUrl --output text)
ARN=$($A sqs get-queue-attributes --queue-url "$URL2" --attribute-names QueueArn --query Attributes.QueueArn --output text)
$A sns subscribe --topic-arn "$TEMA" --protocol sqs --notification-endpoint "$ARN" --query SubscriptionArn --output text
$A sns publish --topic-arn "$TEMA" --message "se cayo el disco" --query MessageId --output text
echo "-- y esto es lo que hay en la COLA: tu mensaje NO viene solo --"
$A sqs receive-message --queue-url "$URL2" --query "Messages[0].Body" --output text

t "FIN"
