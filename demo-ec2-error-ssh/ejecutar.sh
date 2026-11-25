#!/bin/bash
# Levanta «instancia», «pc» y «moto», corre la demo y deja la salida literal en SALIDA.md. Desde Git Bash:
#   bash canales/cultura-devops/recursos/demo-ec2-error-ssh/ejecutar.sh
# Las llaves se crean dentro de los contenedores y se borran con ellos: no hay credenciales reales.
cd "$(dirname "$0")" || exit 1
export MSYS_NO_PATHCONV=1
RED=demo-ec2
MOTO=motoserver/moto@sha256:120b1589c6df7e35d2092935f6ff724486bb2c4189d0e36ce795baba1400ffd2
limpiar() { docker rm -f instancia pc moto >/dev/null 2>&1; docker network rm $RED >/dev/null 2>&1; }
limpiar
docker build -q -t demo-ec2ssh:1 . >/dev/null || exit 1
docker network create $RED >/dev/null
docker run -d --name instancia --hostname instancia --network $RED --cap-add NET_ADMIN demo-ec2ssh:1 >/dev/null
docker run -d --name pc --hostname pc --network $RED demo-ec2ssh:1 >/dev/null
docker run -d --name moto --network $RED $MOTO >/dev/null
# La llave del «key pair» (formato PEM, como la que descarga la consola) y otra que no es.
docker exec -u ana -w /home/ana pc sh -c "ssh-keygen -q -t rsa -b 2048 -m PEM -N '' -f mi-llave.pem -C mi-llave && mv mi-llave.pem.pub mi-llave.pub && chmod 400 mi-llave.pem"
docker exec -u ana -w /home/ana pc sh -c "ssh-keygen -q -t rsa -b 2048 -m PEM -N '' -f otra-llave.pem -C otra-llave && rm otra-llave.pem.pub && chmod 400 otra-llave.pem"
docker exec -u ana pc cat /home/ana/mi-llave.pub | docker exec -i -u ubuntu instancia sh -c "mkdir -p ~/.ssh && cat > ~/.ssh/authorized_keys && chmod 600 ~/.ssh/authorized_keys"
docker exec instancia /usr/sbin/sshd -E /var/log/sshd.log
sleep 4
{
  echo "# SALIDA — AWS: error establishing SSH connection to your instance (cultura-devops)"
  echo
  echo "> Corrida del $(date '+%Y-%m-%d %H:%M'). «instancia» y «pc»: Debian trixie, $(docker exec pc ssh -V 2>&1). AWS simulado con moto $(docker exec moto python -c 'import moto;print(moto.__version__)') y aws-cli 2.38.5."
  echo "> ip-ranges.json es el archivo público y oficial de AWS, descargado en esta corrida."
  echo
  echo '```'
  bash ./correr.sh
  echo '```'
} > SALIDA.md
limpiar
cat SALIDA.md
