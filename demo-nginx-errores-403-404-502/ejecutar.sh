#!/bin/bash
# Levanta «web», «app» y «cliente», corre la demo y deja la salida literal en SALIDA.md. Desde Git Bash:
#   bash canales/cultura-devops/recursos/demo-nginx-errores-403-404-502/ejecutar.sh
cd "$(dirname "$0")" || exit 1
export MSYS_NO_PATHCONV=1
RED=demo-nginx-err
limpiar() { docker rm -f web app cliente >/dev/null 2>&1; docker network rm $RED >/dev/null 2>&1; }
limpiar
docker network create $RED >/dev/null
docker run -d --name app --network $RED python:3.13-alpine sleep infinity >/dev/null
docker exec app sh -c "mkdir -p /srv && echo '{\"ok\": true}' > /srv/index.html"
docker run -d --name web --network $RED nginx:1.31.8-alpine >/dev/null
docker run -d --name cliente --network $RED --entrypoint sleep curlimages/curl:8.23.0 infinity >/dev/null
sleep 2
{
  echo "# SALIDA — Nginx: errores 403, 404 y 502 y cómo arreglarlos (cultura-devops)"
  echo
  echo "> Corrida del $(date '+%Y-%m-%d %H:%M'). $(docker exec web nginx -v 2>&1) (nginx:1.31.8-alpine), backend python:3.13-alpine, cliente curlimages/curl:8.23.0, en una red de Docker propia."
  echo
  echo '```'
  bash ./correr.sh
  echo '```'
} > SALIDA.md
limpiar
cat SALIDA.md
