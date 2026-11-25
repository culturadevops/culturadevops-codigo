#!/usr/bin/env bash
# Clúster del banco de las partes 5-8 del «Curso de Kubernetes 2027» (cultura-devops).
# kind v0.30.0 · kindest/node v1.34.0 · 1 control-plane + 2 workers · nombre k8s-b (contenedores k8s-b-*).
#   bash cluster-k8s-b.sh up      crea el clúster (si no existe) y carga las imágenes del banco
#   bash cluster-k8s-b.sh down    lo borra
# Las demos corren DENTRO del control-plane con su kubectl (v1.34, la misma versión que el servidor).
set -euo pipefail
export MSYS_NO_PATHCONV=1
NODO="kindest/node:v1.34.0@sha256:7416a61b42b1662ca6ca89f02028ac133a309a2a30ba309614e8ec94d976dc5a"
IMAGENES="busybox:1.37 postgres:18.6-alpine k8s-b-api:1 registry.k8s.io/metrics-server/metrics-server:v0.8.0"

case "${1:-up}" in
up)
  if ! kind get clusters 2>/dev/null | grep -qx k8s-b; then
    kind create cluster --name k8s-b --image "$NODO" --config "$(cd "$(dirname "$0")" && pwd -W)/kind-k8s-b.yaml" --wait 180s
  fi
  # «kind load» falla con el almacén de imágenes de containerd de Docker Desktop (digest not found):
  # se exporta solo linux/amd64 y se importa a mano en cada nodo.
  for i in $IMAGENES; do
    for n in $(kind get nodes --name k8s-b); do
      docker save --platform linux/amd64 "$i" | docker exec -i "$n" ctr --namespace=k8s.io images import --digests --snapshotter=overlayfs - >/dev/null
    done
  done
  echo "k8s-b listo"
  ;;
down)
  kind delete cluster --name k8s-b
  ;;
esac
