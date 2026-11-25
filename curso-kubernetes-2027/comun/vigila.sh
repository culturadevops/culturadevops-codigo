#!/bin/sh
# Corre DENTRO del nodo k8s-a-control-plane. Vigila un pod y escribe cada CAMBIO de su línea
# de «kubectl get pod» (READY, STATUS, RESTARTS), con los milisegundos desde que empezó.
# Uso: sh vigila.sh <namespace> <pod> <segundos> [pausa]
ns=$1; pod=$2; dur=$3; pausa=${4:-0.2}
export KUBECONFIG=/etc/kubernetes/admin.conf
t0=$(date +%s%3N); prev=""
while :; do
  ahora=$(date +%s%3N); dt=$((ahora - t0))
  [ $dt -gt $((dur * 1000)) ] && break
  l=$(kubectl get pod -n "$ns" "$pod" --no-headers 2>&1 | awk '{print $2, $3, $4}')
  case "$l" in *NotFound*|*"not found"*) l="(no existe)";; esac
  if [ "$l" != "$prev" ]; then printf '%7d ms  %s\n' "$dt" "$l"; prev="$l"; fi
  sleep "$pausa"
done
