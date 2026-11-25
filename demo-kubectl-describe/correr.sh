#!/bin/sh
# Demo de «kubectl describe pod: cómo leerlo» (cultura-devops, 2026-10-20). Corre DENTRO del contenedor de k3s.
set -u
k() { kubectl "$@" 2>&1; }
eventos() { kubectl describe pod "$1" | sed -n '/^Events:/,$p'; }
cd /trabajo
k create namespace demo >/dev/null
k config set-context --current --namespace=demo >/dev/null
k apply -f pods.yaml >/dev/null
kubectl wait --for=condition=Ready pod/sano --timeout=180s >/dev/null 2>&1
for i in $(seq 1 90); do [ "$(kubectl get pod se-cae -o jsonpath='{.status.containerStatuses[0].restartCount}')" -ge 3 ] 2>/dev/null && break; sleep 2; done
sleep 10

echo "### 1 · Los pods"
echo "\$ kubectl apply -f pods.yaml && kubectl get pods"
k get pods

echo
echo "### 2 · Un pod sano, completo"
echo "\$ kubectl describe pod sano"
k describe pod sano

echo
echo "### 3 · Pending: ningún nodo tiene sitio"
echo "\$ kubectl describe pod pendiente   # solo Status y Events"
kubectl describe pod pendiente | grep -E '^(Status|Node):'
eventos pendiente
echo "\$ kubectl describe node | sed -n '/Allocatable/,/System Info/p'"
kubectl describe node | sed -n '/^Allocatable:/,/^System Info:/p' | grep -E 'Allocatable|cpu|memory'

echo
echo "### 4 · CrashLoopBackOff: el contenedor arranca y se muere"
for i in $(seq 1 300); do [ "$(kubectl get pod se-cae -o jsonpath='{.status.containerStatuses[0].state.waiting.reason}')" = "CrashLoopBackOff" ] && break; sleep 1; done
echo "\$ kubectl get pod se-cae"
k get pod se-cae
echo "\$ kubectl describe pod se-cae   # la parte de Containers"
kubectl describe pod se-cae | sed -n '/^    State:/,/^    Ready:/p;/Restart Count/p'
eventos se-cae
echo "\$ kubectl logs se-cae"
k logs se-cae

echo
echo "### 5 · Running pero no Ready: falla la readiness probe"
echo "\$ kubectl get pod no-listo"
k get pod no-listo
echo "\$ kubectl describe pod no-listo   # Readiness, Conditions y Events"
kubectl describe pod no-listo | grep -E '^    Readiness:|^    Ready:'
kubectl describe pod no-listo | sed -n '/^Conditions:/,/^Volumes:/p' | grep -v '^Volumes:'
eventos no-listo

echo
echo "### 6 · ContainerCreating para siempre: falta un ConfigMap"
echo "\$ kubectl get pod sin-config"
k get pod sin-config
echo "\$ kubectl describe pod sin-config   # la parte de Events"
eventos sin-config
echo "\$ kubectl create configmap config-app --from-literal=modo=produccion"
k create configmap config-app --from-literal=modo=produccion
kubectl wait --for=condition=Ready pod/sin-config --timeout=120s >/dev/null 2>&1
echo "\$ kubectl get pod sin-config"
k get pod sin-config

echo
echo "### 7 · Los eventos de todo el namespace, en orden"
echo "\$ kubectl get events --sort-by=.lastTimestamp | tail -8"
k get events --sort-by=.lastTimestamp -o custom-columns=TIPO:.type,MOTIVO:.reason,OBJETO:.involvedObject.name | tail -8
