#!/bin/sh
# EP5 (firmas) y EP8 (persistencia). Se ejecuta con la CLI oficial contra dos nubecitas
# distintas: una con -firmar y otra con -semilla.
set -u
export AWS_DEFAULT_REGION=us-east-1
t() { echo; echo "############ $1 ############"; }

t "EP5 · con -firmar: la credencial BUENA entra"
export AWS_ACCESS_KEY_ID=prueba AWS_SECRET_ACCESS_KEY=prueba
aws --endpoint-url http://nubefirma:4566 s3 mb s3://privado

t "EP5 · la credencial MALA: y fijate en lo que NO dice el error"
export AWS_ACCESS_KEY_ID=prueba AWS_SECRET_ACCESS_KEY=me-la-invento
aws --endpoint-url http://nubefirma:4566 s3 ls 2>&1 | head -4

t "EP8 · con -semilla: se lee al arrancar y NO se escribe nunca"
export AWS_ACCESS_KEY_ID=prueba AWS_SECRET_ACCESS_KEY=prueba
echo "-- lo que trae la semilla --"
aws --endpoint-url http://nubesemilla:4566 s3 ls
aws --endpoint-url http://nubesemilla:4566 s3 ls s3://sembrado/
echo "-- escribo algo nuevo, que solo vive en memoria --"
echo hola > /tmp/h.txt
aws --endpoint-url http://nubesemilla:4566 s3 cp /tmp/h.txt s3://sembrado/h.txt
aws --endpoint-url http://nubesemilla:4566 s3 ls s3://sembrado/
t "FIN"
