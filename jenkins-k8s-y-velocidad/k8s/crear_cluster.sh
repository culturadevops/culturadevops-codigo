#!/usr/bin/env bash
# Red propia (las redes por defecto de Docker de esta máquina están agotadas) + clúster kind fijado + RBAC.
set -euo pipefail
cd "$(dirname "$0")"
docker network inspect jk-b-net >/dev/null 2>&1 || docker network create --subnet 10.211.50.0/24 -o com.docker.network.driver.mtu=1500 jk-b-net
KIND_EXPERIMENTAL_DOCKER_NETWORK=jk-b-net kind create cluster --config kind.yaml --kubeconfig ./kubeconfig
KUBECONFIG=./kubeconfig kubectl apply -f rbac.yaml
KUBECONFIG=./kubeconfig kubectl wait --for=condition=Ready node --all --timeout=180s
