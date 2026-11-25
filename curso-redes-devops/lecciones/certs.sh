#!/bin/sh
# La CA del curso (raíz + intermedia) y un certificado por cada caso de la lección 4.
# Corre DENTRO de un contenedor de la imagen, con el volumen de certificados en /c.
cd /c
set -e
q() { "$@" >/dev/null 2>&1; }
q openssl req -x509 -newkey ec -pkeyopt ec_paramgen_curve:P-256 -nodes -keyout raiz.key -out raiz.pem -days 3650 -subj "/CN=CA raiz del curso"
q openssl req -newkey ec -pkeyopt ec_paramgen_curve:P-256 -nodes -keyout inter.key -out inter.csr -subj "/CN=CA intermedia del curso"
printf "basicConstraints=critical,CA:TRUE\nkeyUsage=critical,keyCertSign,cRLSign\n" > ca.ext
q openssl x509 -req -in inter.csr -CA raiz.pem -CAkey raiz.key -CAcreateserial -out inter.pem -days 1825 -extfile ca.ext
hoja() { # nombre extfile [opciones de fechas]
  q openssl req -newkey ec -pkeyopt ec_paramgen_curve:P-256 -nodes -keyout $1.key -out $1.csr -subj "/CN=api.tienda.test"
  q openssl x509 -req -in $1.csr -CA inter.pem -CAkey inter.key -CAcreateserial -out $1.pem $3 -extfile $2
}
printf "subjectAltName=DNS:api.tienda.test\n" > san.ext
printf "subjectAltName=DNS:otra.tienda.test\n" > otra.ext
printf "basicConstraints=CA:FALSE\n" > nosan.ext
hoja bueno san.ext "-days 90"
hoja sinsan nosan.ext "-days 90"
hoja caducado san.ext "-not_before 20250101000000Z -not_after 20250401000000Z"
hoja nombre otra.ext "-days 90"
cat bueno.pem inter.pem > bueno-cadena.pem
cat sinsan.pem inter.pem > sinsan-cadena.pem
cat caducado.pem inter.pem > caducado-cadena.pem
cat nombre.pem inter.pem > nombre-cadena.pem
chmod 644 *.key
