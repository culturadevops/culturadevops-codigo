#!/usr/bin/env bash
# Levanta el controlador del 877 en la red de kind (jk-b-net). Requiere el clúster jk-b-k8s (crear_cluster.sh).
set -euo pipefail
cd "$(dirname "$0")"
export MSYS_NO_PATHCONV=1 KUBECONFIG=./kubeconfig
TOKEN=$(kubectl -n jenkins-agentes create token jenkins --duration=24h)
docker rm -f jk-b-jenkins-877 >/dev/null 2>&1 || true
docker run -d --rm --ulimit core=1 --name jk-b-jenkins-877 --network jk-b-net -p 28077:8080 \
  -e K8S_TOKEN="$TOKEN" -v "$(cygpath -w "$PWD/../jenkins/casc-877.yaml"):/casc/casc.yaml:ro" \
  jk-b-jenkins:2.580.2 >/dev/null
echo "jk-b-jenkins-877 en http://localhost:28077"
