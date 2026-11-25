#!/bin/sh
# Corre DENTRO del contenedor de k3s (rancher/k3s:v1.37.1-k3s1; lo lanza ejecutar.sh). Salida literal → SALIDA.md.
set -u
k() { kubectl "$@" 2>&1; }
echo "\$ kubectl version"
kubectl version 2>/dev/null | grep -E "Server Version"
echo "\$ kubectl get nodes"
k get nodes -o custom-columns=NOMBRE:.metadata.name,ESTADO:.status.conditions[-1].type
echo
echo "\$ kubectl apply -f app.yaml"
k apply -f /trabajo/app.yaml
k rollout status deployment/web --timeout=180s >/dev/null
echo "\$ kubectl get deployment web"
k get deployment web
echo "\$ kubectl get pods -l app=web"
k get pods -l app=web -o custom-columns=POD:.metadata.name,ESTADO:.status.phase
echo
VICTIMA=$(kubectl get pods -l app=web -o jsonpath='{.items[0].metadata.name}')
echo "\$ kubectl delete pod $VICTIMA   # matar uno a propósito"
k delete pod "$VICTIMA" --wait=true
sleep 3
k rollout status deployment/web --timeout=120s >/dev/null
echo "\$ kubectl get pods -l app=web"
k get pods -l app=web -o custom-columns=POD:.metadata.name,ESTADO:.status.phase
echo
echo "\$ kubectl scale deployment web --replicas=5"
k scale deployment web --replicas=5
k rollout status deployment/web --timeout=120s >/dev/null
echo "\$ kubectl get deployment web"
k get deployment web
echo
echo "\$ kubectl get service web"
k get service web -o custom-columns=NOMBRE:.metadata.name,TIPO:.spec.type,PUERTO:.spec.ports[0].port
echo "\$ kubectl run prueba --rm -i --image=busybox:1.37 --restart=Never -- wget -qO- http://web | grep title"
kubectl run prueba --rm -i --image=busybox:1.37 --restart=Never -- wget -qO- http://web 2>/dev/null | grep -i "<title>"
