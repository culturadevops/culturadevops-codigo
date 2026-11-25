#!/bin/sh
# Lección 2 · Las redes de Docker y quién ve a quién.
#
# En docker compose, «db» resuelve solo. Con docker run a secas, no: la red por defecto (bridge)
# NO tiene DNS por nombre de contenedor. Solo las redes que creas tú. Y dos redes distintas no se
# ven entre sí, aunque estén en la misma máquina.
. /curso/comun.sh
limpiar

titulo "2.1 · La red por defecto: sin DNS por nombre"
docker run -d --name red-db $IMG sleep 300 >/dev/null
echo "  la db tiene la IP $(docker inspect -f '{{range .NetworkSettings.Networks}}{{.IPAddress}}{{end}}' red-db)"
docker run --rm $IMG sh -c 'getent hosts red-db || echo "  getent hosts red-db -> (nada: no resuelve)"'

titulo "2.2 · Una red creada por ti: el DNS de Docker en 127.0.0.11"
docker network create red-tienda >/dev/null
docker network connect red-tienda red-db
docker run --rm --network red-tienda $IMG sh -c '
  echo "  /etc/resolv.conf -> $(grep nameserver /etc/resolv.conf)"
  echo "  getent hosts red-db -> $(getent hosts red-db)"'

titulo "2.3 · Dos redes no se ven entre sí"
docker network create red-otra >/dev/null
docker run --rm --network red-otra $IMG sh -c '
  getent hosts red-db >/dev/null && echo "  resuelve" || echo "  desde red-otra: red-db no resuelve"'
IP=$(docker inspect -f '{{(index .NetworkSettings.Networks "red-tienda").IPAddress}}' red-db)
docker run --rm --network red-otra $IMG sh -c "ping -c1 -W1 $IP >/dev/null 2>&1 && echo '  ping a $IP: responde' || echo '  ping a $IP (por IP): sin respuesta'"

titulo "2.4 · Una red interna: sin salida a internet, a propósito"
docker network create --internal red-interna >/dev/null
r=$(docker run --rm --network red-interna $IMG curl -sS -m 4 -o /dev/null -w '%{http_code}' https://deb.debian.org/ 2>&1 | head -1)
echo "  curl a internet desde red-interna -> $r"
r=$(docker run --rm --network red-tienda $IMG curl -sS -m 6 -o /dev/null -w '%{http_code}' https://deb.debian.org/ 2>&1 | head -1)
echo "  curl a internet desde red-tienda  -> HTTP $r"
limpiar
