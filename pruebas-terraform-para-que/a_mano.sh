#!/usr/bin/env sh
# a_mano.sh — el mismo entorno, levantado a golpe de órdenes sueltas.
#
# Esto NO es un hombre de paja: es exactamente lo que hace todo el mundo antes de tener
# infraestructura como código, y hace muchísimo tiempo que funciona. Un entorno pequeño:
# una red, un volumen, una base de datos, una caché y dos copias de la aplicación.
set -e
E=${ENTORNO:-pruebas}

docker network create ${E}-red >/dev/null
docker volume create ${E}-datos >/dev/null
docker run -d --name ${E}-db --network ${E}-red \
  -v ${E}-datos:/var/lib/postgresql/data \
  -e POSTGRES_PASSWORD=secreto postgres:17-alpine >/dev/null
docker run -d --name ${E}-cache --network ${E}-red redis:7-alpine >/dev/null
docker run -d --name ${E}-app-1 --network ${E}-red \
  -e DB=${E}-db -e CACHE=${E}-cache nginx:alpine >/dev/null
docker run -d --name ${E}-app-2 --network ${E}-red \
  -e DB=${E}-db -e CACHE=${E}-cache nginx:alpine >/dev/null
