#!/bin/sh
# Demo de «kubectl port-forward» (cultura-devops, 2026-10-20). Corre DENTRO del contenedor de k3s.
# kubectl y el «navegador» (wget) están en la misma máquina, como en tu portátil.
set -u
k() { kubectl "$@" 2>&1; }
pedir() { wget -qO- -T 3 "$1" 2>&1; }
cd /trabajo
k create namespace demo >/dev/null
k config set-context --current --namespace=demo >/dev/null
k apply -f web.yaml >/dev/null
k rollout status deployment/web --timeout=180s >/dev/null
POD=$(kubectl get pods -l app=web -o jsonpath='{.items[0].metadata.name}')
IP=$(hostname -i | cut -d' ' -f1)

echo "### 1 · Los pods y el Service: sin IP de fuera"
echo "\$ kubectl get pods,svc"
k get pods -o custom-columns=POD:.metadata.name,ESTADO:.status.phase,IP:.status.podIP
k get svc web -o custom-columns=SERVICE:.metadata.name,TIPO:.spec.type,PUERTO:.spec.ports[0].port

echo
echo "### 2 · port-forward a un pod"
echo "\$ kubectl port-forward pod/$POD 8080:8080 &"
kubectl port-forward pod/$POD 8080:8080 > pf1.log 2>&1 &
PF1=$!
sleep 2
cat pf1.log
echo "\$ wget -qO- localhost:8080"
pedir http://localhost:8080
sleep 1
echo "(lo que imprime port-forward)"
cat pf1.log

echo
echo "### 3 · El puerto ya está ocupado"
echo "\$ kubectl port-forward pod/$POD 8080:8080"
timeout 5 kubectl port-forward pod/$POD 8080:8080 2>&1 | head -4
echo "\$ kubectl port-forward pod/$POD :8080   # puerto local al azar"
kubectl port-forward pod/$POD :8080 > pf0.log 2>&1 &
PF0=$!
sleep 2
cat pf0.log
kill $PF0 2>/dev/null

echo
echo "### 4 · Solo escucha en 127.0.0.1"
echo "\$ wget -qO- $IP:8080   # desde la IP de la máquina, no localhost"
pedir http://$IP:8080
echo "\$ kubectl port-forward --address 0.0.0.0 pod/$POD 8081:8080 &"
kubectl port-forward --address 0.0.0.0 pod/$POD 8081:8080 > pf2.log 2>&1 &
PF2=$!
sleep 2
cat pf2.log
echo "\$ wget -qO- $IP:8081"
pedir http://$IP:8081
kill $PF2 2>/dev/null

echo
echo "### 5 · port-forward a un Service: elige UN pod y se queda con él"
echo "\$ kubectl port-forward svc/web 9090:80 &"
kubectl port-forward svc/web 9090:80 > pf3.log 2>&1 &
PF3=$!
sleep 2
cat pf3.log
echo "\$ for i in 1 2 3 4 5 6; do wget -qO- localhost:9090; done"
for i in 1 2 3 4 5 6; do pedir http://localhost:9090; done
echo "\$ kubectl run prueba --rm -i --image=busybox:1.37 --restart=Never -- sh -c 'for i in 1 2 3 4 5 6; do wget -qO- web; done'   # desde dentro del clúster"
kubectl run prueba --rm -i --image=busybox:1.37 --restart=Never -- sh -c 'for i in 1 2 3 4 5 6; do wget -qO- web; done' 2>/dev/null | grep hola
kill $PF3 2>/dev/null

echo
echo "### 6 · Si el pod muere, el túnel se rompe"
echo "\$ kubectl delete pod $POD"
k delete pod $POD
sleep 3
echo "\$ wget -qO- localhost:8080"
pedir http://localhost:8080
sleep 2
echo "(lo que imprime port-forward)"
tail -3 pf1.log
echo "\$ jobs   # ¿sigue vivo el port-forward?"
if kill -0 $PF1 2>/dev/null; then echo "sigue corriendo"; else echo "terminó"; fi
echo "\$ kubectl get pods"
k get pods -o custom-columns=POD:.metadata.name,ESTADO:.status.phase
kill $PF1 2>/dev/null
rm -f pf0.log pf1.log pf2.log pf3.log
