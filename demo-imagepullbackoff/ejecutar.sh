#!/bin/bash
# Levanta un registro privado con clave + un k3s en la misma red, corre la demo y deja la salida literal en SALIDA.md. Desde Git Bash:
#   bash canales/cultura-devops/recursos/demo-imagepullbackoff/ejecutar.sh
cd "$(dirname "$0")" || exit 1
export MSYS_NO_PATHCONV=1
AQUI=$(cygpath -w "$PWD")
RED=demo-ipbo
CLAVE=$(od -An -N8 -tx1 /dev/urandom | tr -d ' \n')
docker rm -f k3s-ipbo registro >/dev/null 2>&1
docker network rm $RED >/dev/null 2>&1
docker network create $RED >/dev/null

# Registro privado: usuario «tienda» con clave aleatoria (htpasswd con bcrypt).
mkdir -p _auth
docker run --rm --entrypoint htpasswd httpd:2.4-alpine -Bbn tienda "$CLAVE" > _auth/htpasswd
docker run -d --name registro --network $RED -p 5099:5000 -v "$AQUI\\_auth:/auth" \
  -e REGISTRY_AUTH=htpasswd -e REGISTRY_AUTH_HTPASSWD_REALM=privado -e REGISTRY_AUTH_HTPASSWD_PATH=/auth/htpasswd registry:3 >/dev/null
sleep 3
echo "$CLAVE" | docker login localhost:5099 -u tienda --password-stdin >/dev/null
docker tag nginx:1.30.5-alpine localhost:5099/tienda/web:1.0
docker push -q localhost:5099/tienda/web:1.0 >/dev/null
docker logout localhost:5099 >/dev/null

docker run -d --name k3s-ipbo --network $RED --privileged -v "$AQUI:/trabajo" \
  -v "$AQUI\\registries.yaml:/etc/rancher/k3s/registries.yaml" rancher/k3s:v1.37.1-k3s1 server --disable traefik >/dev/null
until docker exec k3s-ipbo kubectl get nodes 2>/dev/null | grep -q " Ready"; do sleep 2; done
until docker exec k3s-ipbo kubectl get serviceaccount default >/dev/null 2>&1; do sleep 2; done
{
  echo "# SALIDA — ImagePullBackOff en Kubernetes (cultura-devops)"
  echo
  echo "> Corrida del $(date '+%Y-%m-%d %H:%M'). Kubernetes de un nodo con k3s (rancher/k3s:v1.37.1-k3s1) dentro de Docker,"
  echo "> y un registro privado (registry:3 con htpasswd) en la misma red con el nombre registro:5000. La clave se oculta con asteriscos."
  echo
  echo '```'
  docker exec -e CLAVE_REGISTRO="$CLAVE" k3s-ipbo sh /trabajo/correr.sh
  echo '```'
} > SALIDA.md
docker rm -f k3s-ipbo registro >/dev/null 2>&1
docker network rm $RED >/dev/null 2>&1
docker rmi localhost:5099/tienda/web:1.0 >/dev/null 2>&1
cat SALIDA.md
