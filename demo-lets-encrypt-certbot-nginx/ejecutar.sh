#!/bin/bash
# Levanta «pebble», «web» y «cliente», corre la demo y deja la salida literal en SALIDA.md. Desde Git Bash:
#   bash canales/cultura-devops/recursos/demo-lets-encrypt-certbot-nginx/ejecutar.sh
# Pebble es la CA de prueba de Let's Encrypt: en producción se quita --server y certbot usa la CA real.
cd "$(dirname "$0")" || exit 1
export MSYS_NO_PATHCONV=1
RED=demo-le
limpiar() { docker rm -f pebble web cliente >/dev/null 2>&1; docker network rm $RED >/dev/null 2>&1; }
limpiar
docker build -q -t demo-certbot:1 . >/dev/null || exit 1
docker network create $RED >/dev/null
# Pebble valida contra el puerto 80 (la config de prueba trae 5002) y sin esperas aleatorias.
docker run -d --name pebble --network $RED -e PEBBLE_VA_NOSLEEP=1 -e PEBBLE_WFE_NONCEREJECT=0 \
  -v "$(pwd -W)/pebble-config.json:/test/config/demo.json:ro" ghcr.io/letsencrypt/pebble:2.10.1 -config /test/config/demo.json >/dev/null
docker run -d --name web --network $RED --network-alias tienda.example.com demo-certbot:1 >/dev/null
docker run -d --name cliente --network $RED --entrypoint sleep curlimages/curl:8.23.0 infinity >/dev/null
sleep 3
# La raíz que firma la API de Pebble (para que certbot hable con ella) y la raíz que firma los certificados emitidos.
docker cp pebble:/test/certs/pebble.minica.pem ./_minica.pem >/dev/null
docker cp ./_minica.pem web:/pebble.minica.pem >/dev/null
docker exec web curl -s --cacert /pebble.minica.pem https://pebble:15000/roots/0 > ./_raiz.pem
docker cp ./_raiz.pem cliente:/pebble-raiz.pem >/dev/null
{
  echo "# SALIDA — Certificado SSL gratis con Let's Encrypt (certbot + nginx) (cultura-devops)"
  echo
  echo "> Corrida del $(date '+%Y-%m-%d %H:%M'). CA de prueba: $(docker run --rm ghcr.io/letsencrypt/pebble:2.10.1 -version 2>&1 | head -1) (ghcr.io/letsencrypt/pebble:2.10.1, la CA de prueba oficial de Let's Encrypt)."
  echo "> Servidor: Debian trixie, $(docker exec web nginx -v 2>&1), $(docker exec web certbot --version 2>&1). Cliente: curlimages/curl:8.23.0. En producción se quita --server."
  echo
  echo '```'
  bash ./correr.sh
  echo '```'
} > SALIDA.md
rm -f ./_minica.pem ./_raiz.pem
limpiar
cat SALIDA.md
