#!/bin/sh
# Lección 4 · TLS de principio a fin: la cadena, el SAN, la caducidad y el nombre.
#
# Una CA propia (raíz + intermedia) y un nginx con un puerto por cada certificado roto. El cliente
# confía en la raíz, como confiaría en la de Let's Encrypt. Los cuatro errores que salen en
# pantalla, y qué significa cada uno.
. /curso/comun.sh
limpiar
docker network create red-t >/dev/null
docker volume create red-certs >/dev/null

# ── Los certificados, fabricados dentro de un contenedor con openssl ────────────────────────
docker run --rm -v red-certs:/c -v "$CURSO_HOST/lecciones:/curso:ro" $IMG sh /curso/certs.sh

conf='
server { listen 4431 ssl; ssl_certificate /c/bueno-cadena.pem;    ssl_certificate_key /c/bueno.key;    return 200 "ok\n"; }
server { listen 4432 ssl; ssl_certificate /c/bueno.pem;           ssl_certificate_key /c/bueno.key;    return 200 "ok\n"; }
server { listen 4433 ssl; ssl_certificate /c/sinsan-cadena.pem;   ssl_certificate_key /c/sinsan.key;   return 200 "ok\n"; }
server { listen 4434 ssl; ssl_certificate /c/caducado-cadena.pem; ssl_certificate_key /c/caducado.key; return 200 "ok\n"; }
server { listen 4435 ssl; ssl_certificate /c/nombre-cadena.pem;   ssl_certificate_key /c/nombre.key;   return 200 "ok\n"; }'
docker run -d --name red-tls --network red-t --network-alias api.tienda.test -v red-certs:/c:ro $IMG \
  sh -c "printf '%s\n' '$conf' > /etc/nginx/conf.d/t.conf && exec nginx -g 'daemon off;'" >/dev/null
sleep 2

probar() { # puerto titulo
  r=$(docker run --rm --network red-t -v red-certs:/c:ro $IMG curl -sS -m 5 --cacert /c/raiz.pem "https://api.tienda.test:$1/" 2>&1 | head -1)
  v=$(docker run --rm --network red-t -v red-certs:/c:ro $IMG sh -c \
      "openssl s_client -connect api.tienda.test:$1 -servername api.tienda.test -verify_hostname api.tienda.test -CAfile /c/raiz.pem </dev/null 2>/dev/null | grep 'Verify return code'")
  printf '  %-30s curl: %s\n  %-30s openssl: %s\n' "$2" "$r" "" "$(echo "$v" | sed 's/^ *//')"
}

titulo "4.1 · El bueno: hoja + intermedia, con SAN, en fecha"
probar 4431 "bueno"
titulo "4.2 · Cadena incompleta: el servidor manda solo la hoja"
probar 4432 "sin la intermedia"
titulo "4.3 · Sin SAN: el nombre solo en el CN"
probar 4433 "sin SAN"
titulo "4.3b · El mismo certificado sin SAN, con un cliente en Go"
# CURSO_HOST: la ruta del curso en la máquina (los -v de aquí dentro son rutas del anfitrión).
go_get() {
  docker run --rm --network red-t -v red-certs:/c:ro -v "$CURSO_HOST/cliente-go:/src:ro" \
    -e GOCACHE=/tmp/gc -e GOFLAGS=-buildvcs=false golang:1.26 \
    sh -c "cd /src && go version | cut -d' ' -f3 && go run . https://api.tienda.test:$1/" 2>&1 \
    | grep -v '^exit status' | paste -sd' ' -
}
echo "  bueno:   $(go_get 4431)"
echo "  sin SAN: $(go_get 4433)"

titulo "4.4 · Caducado"
probar 4434 "caducado"
titulo "4.5 · Nombre equivocado"
probar 4435 "para otra.tienda.test"

titulo "4.6 · Antes de que pase: cuántos días le quedan"
docker run --rm -v red-certs:/c:ro $IMG sh -c '
for f in bueno caducado; do
  fin=$(openssl x509 -in /c/$f.pem -noout -enddate | cut -d= -f2)
  dias=$(( ( $(date -d "$fin" +%s) - $(date +%s) ) / 86400 ))
  printf "  %-9s caduca: %s -> %s días\n" "$f" "$fin" "$dias"
  openssl x509 -in /c/$f.pem -noout -checkend $((30*86400)) >/dev/null || echo "            checkend 30 días: ALARMA"
done'
limpiar
docker volume rm red-certs >/dev/null
