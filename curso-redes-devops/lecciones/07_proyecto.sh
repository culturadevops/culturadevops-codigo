#!/bin/sh
# Lección 7 · El proyecto: diagnostico.sh contra los fallos del curso, uno por capa.
# Necesita CURSO_HOST (la ruta del curso en la máquina): los contenedores montan /curso de ahí.
. /curso/comun.sh
limpiar
docker volume rm -f red-certs >/dev/null 2>&1
docker network create red-t >/dev/null
docker volume create red-certs >/dev/null
docker run --rm -v red-certs:/c -v "$CURSO_HOST/lecciones:/curso:ro" $IMG sh /curso/certs.sh
conf='
server { listen 443 ssl; ssl_certificate /c/bueno-cadena.pem;  ssl_certificate_key /c/bueno.key;  location / { root /w; } }
server { listen 8443 ssl; ssl_certificate /c/sinsan-cadena.pem; ssl_certificate_key /c/sinsan.key; location / { root /w; } }'
docker run -d --name red-web --network red-t --network-alias api.tienda.test -v red-certs:/c:ro $IMG \
  sh -c "mkdir -p /w && echo hola > /w/index.html && printf '%s\n' '$conf' > /etc/nginx/conf.d/t.conf && exec nginx -g 'daemon off;'" >/dev/null
docker run -d --name red-mudo --network red-t $IMG sleep 600 >/dev/null              # nadie escucha
docker run -d --name red-local -p 18007:8000 $IMG python3 -m http.server 8000 --bind 127.0.0.1 >/dev/null
sleep 2

diag() { # titulo url
  titulo "$1"
  docker run --rm --network red-t -v red-certs:/c:ro -v "$CURSO_HOST/lecciones:/curso:ro" $IMG \
    bash /curso/diagnostico.sh "$2" --ca /c/raiz.pem
  echo "  (código de salida $?)"
}
diag "7.1 · Todo bien"                       https://api.tienda.test/
diag "7.2 · Un nombre que no existe"         https://api.tienda.text/
diag "7.3 · El contenedor está, el servicio no" http://red-mudo:8000/
diag "7.4 · El certificado sin SAN"          https://api.tienda.test:8443/
diag "7.5 · Escucha en 127.0.0.1 detrás de -p (lección 1)" http://host.docker.internal:18007/

titulo "7.6 · El camino con el MTU roto (lección 5)"
montar_mtu "$TIRA_ICMP"
docker exec red-cliente bash /curso/diagnostico.sh http://10.82.0.10/200000
echo "  (código de salida $?)"
limpiar
docker volume rm red-certs >/dev/null
