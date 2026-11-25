#!/bin/sh
# Corredor del curso «Tu nube local SIN licencias». Se ejecuta DENTRO del contenedor de la
# CLI OFICIAL de AWS, contra nubecita en la misma red de Docker. Ese es el argumento del
# curso: quien habla con el doble es siempre el cliente de Amazon, sin parches.
set -u
export AWS_ACCESS_KEY_ID=prueba AWS_SECRET_ACCESS_KEY=prueba AWS_DEFAULT_REGION=us-east-1
A="aws --endpoint-url http://nubecita:4566"
t() { echo; echo "############ $1 ############"; }

t "ENTORNO"
aws --version
echo "nubecita: imagen local, un solo binario en Go"

t "EP1 · el primer bucket contra tu propia nube"
$A s3 mb s3://fotos
$A s3 ls

t "EP2 · S3: subir, listar, y que S3 NO tiene carpetas"
echo "un gato" > /tmp/gato.txt
mkdir -p /tmp/2026/enero && echo "enero" > /tmp/2026/enero/nota.txt
$A s3 cp /tmp/gato.txt s3://fotos/gato.txt
$A s3 cp /tmp/2026/enero/nota.txt s3://fotos/2026/enero/nota.txt
echo "-- ls plano: solo ve el primer nivel, y 2026/ sale como PRE(fijo) --"
$A s3 ls s3://fotos/
echo "-- ls --recursive: aqui se ve que la 'carpeta' era parte del nombre --"
$A s3 ls s3://fotos/ --recursive
echo "-- la API cruda: delimitador / y el prefijo comun --"
$A s3api list-objects-v2 --bucket fotos --delimiter / --query 'CommonPrefixes'
echo "-- y sin delimitador NO hay carpetas: la clave entera es el nombre --"
$A s3api list-objects-v2 --bucket fotos --query 'Contents[].Key'

t "EP3 · DynamoDB: otro protocolo, el MISMO puerto"
$A dynamodb create-table --table-name pedidos \
  --attribute-definitions AttributeName=cliente,AttributeType=S AttributeName=fecha,AttributeType=S \
  --key-schema AttributeName=cliente,KeyType=HASH AttributeName=fecha,KeyType=RANGE \
  --billing-mode PAY_PER_REQUEST --query 'TableDescription.TableName'
$A dynamodb put-item --table-name pedidos \
  --item '{"cliente":{"S":"ana"},"fecha":{"S":"2026-01-03"},"total":{"N":"42.5"}}'
$A dynamodb put-item --table-name pedidos \
  --item '{"cliente":{"S":"ana"},"fecha":{"S":"2026-02-11"},"total":{"N":"17"}}'
$A dynamodb put-item --table-name pedidos \
  --item '{"cliente":{"S":"luis"},"fecha":{"S":"2026-01-20"},"total":{"N":"99"}}'
echo "-- Query: solo la particion de ana, y el orden por fecha --"
$A dynamodb query --table-name pedidos \
  --key-condition-expression 'cliente = :c' \
  --expression-attribute-values '{":c":{"S":"ana"}}' --query 'Items[].fecha.S'
echo "-- Query con rango: begins_with sobre la clave de orden --"
$A dynamodb query --table-name pedidos \
  --key-condition-expression 'cliente = :c AND begins_with(fecha, :f)' \
  --expression-attribute-values '{":c":{"S":"ana"},":f":{"S":"2026-01"}}' --query 'Count'
echo "-- Scan: recorre TODA la tabla, y por eso se paga --"
$A dynamodb scan --table-name pedidos --select COUNT --query 'Count'

t "EP4 · SQS: recibir NO saca el mensaje, lo esconde"
URL=$($A sqs create-queue --queue-name trabajos --query QueueUrl --output text)
echo "cola: $URL"
$A sqs send-message --queue-url "$URL" --message-body 'procesa el pedido 42' --query 'MD5OfMessageBody'
echo "-- primera recepcion --"
$A sqs receive-message --queue-url "$URL" --query 'Messages[].[Body,Attributes]' --attribute-names All
echo "-- segunda recepcion INMEDIATA: no hay nada, esta invisible --"
$A sqs receive-message --queue-url "$URL" --query 'Messages'
echo "-- cuantos hay: en vuelo, no perdidos --"
$A sqs get-queue-attributes --queue-url "$URL" \
  --attribute-names ApproximateNumberOfMessages ApproximateNumberOfMessagesNotVisible \
  --query 'Attributes'

t "FIN"
