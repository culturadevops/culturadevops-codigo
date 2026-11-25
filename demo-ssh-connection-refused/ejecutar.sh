#!/bin/bash
# Construye la imagen, levanta «cliente» y «servidor», corre la demo y deja la salida literal en SALIDA.md. Desde Git Bash:
#   bash canales/cultura-devops/recursos/demo-ssh-connection-refused/ejecutar.sh
cd "$(dirname "$0")" || exit 1
export MSYS_NO_PATHCONV=1
RED=demo-ssh
docker build -q -t demo-ssh:1 . >/dev/null || exit 1
docker rm -f cliente servidor >/dev/null 2>&1
docker network rm $RED >/dev/null 2>&1
docker network create $RED >/dev/null
docker run -d --name servidor --hostname servidor --network $RED --cap-add NET_ADMIN demo-ssh:1 >/dev/null
docker run -d --name cliente --hostname cliente --network $RED demo-ssh:1 >/dev/null
# La clave de ana: se crea en el cliente y su parte pública va al servidor.
docker exec -u ana cliente sh -c "ssh-keygen -q -t ed25519 -N '' -f ~/.ssh/id_ed25519"
docker exec -u ana cliente cat /home/ana/.ssh/id_ed25519.pub | docker exec -i -u ana servidor sh -c "mkdir -p ~/.ssh && cat > ~/.ssh/authorized_keys && chmod 600 ~/.ssh/authorized_keys"
{
  echo "# SALIDA — SSH: connection refused en el puerto 22 (cultura-devops)"
  echo
  echo "> Corrida del $(date '+%Y-%m-%d %H:%M'). Dos contenedores Debian trixie en una red de Docker propia; $(docker exec cliente ssh -V 2>&1)."
  echo
  echo '```'
  IP_VACIA=$(docker inspect -f '{{range .NetworkSettings.Networks}}{{.IPAddress}}{{end}}' servidor | sed 's/\.[0-9]*$/.200/') bash ./correr.sh
  echo '```'
} > SALIDA.md
docker rm -f cliente servidor >/dev/null 2>&1
docker network rm $RED >/dev/null 2>&1
cat SALIDA.md
