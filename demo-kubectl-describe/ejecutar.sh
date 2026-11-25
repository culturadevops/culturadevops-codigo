#!/bin/bash
# Levanta un k3s, corre la demo de kubectl describe y deja la salida literal en SALIDA.md. Desde Git Bash:
#   bash canales/cultura-devops/recursos/demo-kubectl-describe/ejecutar.sh
cd "$(dirname "$0")" || exit 1
export MSYS_NO_PATHCONV=1
AQUI=$(cygpath -w "$PWD")
docker rm -f k3s-describe >/dev/null 2>&1
docker run -d --name k3s-describe --privileged -v "$AQUI:/trabajo" rancher/k3s:v1.37.1-k3s1 server --disable traefik >/dev/null
until docker exec k3s-describe kubectl get nodes 2>/dev/null | grep -q " Ready"; do sleep 2; done
until docker exec k3s-describe kubectl get serviceaccount default >/dev/null 2>&1; do sleep 2; done
{
  echo "# SALIDA — kubectl describe pod: cómo leerlo (cultura-devops)"
  echo
  echo "> Corrida del $(date '+%Y-%m-%d %H:%M'). Kubernetes de un nodo con k3s (rancher/k3s:v1.37.1-k3s1) dentro de Docker."
  echo
  echo '```'
  docker exec k3s-describe sh /trabajo/correr.sh
  echo '```'
} > SALIDA.md
docker rm -f k3s-describe >/dev/null 2>&1
cat SALIDA.md
