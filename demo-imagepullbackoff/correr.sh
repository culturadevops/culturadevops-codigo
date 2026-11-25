#!/bin/sh
# Demo de «ImagePullBackOff en Kubernetes» (cultura-devops, 2026-10-20). Corre DENTRO del contenedor de k3s.
# Junto a él, en la misma red de Docker, hay un registro privado con usuario y clave: registro:5000.
set -u
k() { kubectl "$@" 2>&1; }
motivo() { kubectl get pod "$1" -o jsonpath='{.status.containerStatuses[0].state.waiting.reason}'; echo; }
espera_falla() { for i in $(seq 1 60); do r=$(kubectl get pod "$1" -o jsonpath='{.status.containerStatuses[0].state.waiting.reason}' 2>/dev/null); [ "$r" = "ImagePullBackOff" ] && break; sleep 2; done; }
mensaje() { kubectl get events --field-selector involvedObject.name="$1",reason=Failed -o jsonpath='{.items[0].message}'; echo; }
cd /trabajo
k create namespace demo >/dev/null
k config set-context --current --namespace=demo >/dev/null

echo "### 1 · Una etiqueta que no existe"
echo "\$ kubectl run web --image=nginx:1.30.99-alpine"
k run web --image=nginx:1.30.99-alpine
sleep 4
echo "\$ kubectl get pod web"
k get pod web
espera_falla web
echo "\$ kubectl get pod web   # unos segundos después"
k get pod web
echo "\$ kubectl describe pod web   # la parte de Events"
kubectl describe pod web | sed -n '/^Events:/,$p'

echo
echo "### 2 · El nombre de la imagen mal escrito"
echo "\$ kubectl run web2 --image=ngnix:1.30.5-alpine"
k run web2 --image=ngnix:1.30.5-alpine
espera_falla web2
echo "\$ kubectl get events --field-selector involvedObject.name=web2,reason=Failed"
mensaje web2

echo
echo "### 3 · Un registro que no existe (o mal escrito)"
echo "\$ kubectl run web3 --image=registor:5000/tienda/web:1.0"
k run web3 --image=registor:5000/tienda/web:1.0
espera_falla web3
echo "\$ kubectl get events --field-selector involvedObject.name=web3,reason=Failed"
mensaje web3

echo
echo "### 4 · Un registro privado sin credenciales"
echo "\$ kubectl run web4 --image=registro:5000/tienda/web:1.0"
k run web4 --image=registro:5000/tienda/web:1.0
espera_falla web4
echo "\$ kubectl get events --field-selector involvedObject.name=web4,reason=Failed"
mensaje web4

echo
echo "### 5 · El arreglo: un secreto de tipo docker-registry"
echo "\$ kubectl create secret docker-registry registro-cred --docker-server=registro:5000 --docker-username=tienda --docker-password=********"
k create secret docker-registry registro-cred --docker-server=registro:5000 --docker-username=tienda --docker-password="$CLAVE_REGISTRO"
echo "\$ kubectl apply -f pod-con-secreto.yaml"
k apply -f pod-con-secreto.yaml
kubectl wait --for=condition=Ready pod/web5 --timeout=120s >/dev/null 2>&1
echo "\$ kubectl get pod web5"
k get pod web5
echo "\$ kubectl describe pod web5   # la parte de Events"
kubectl describe pod web5 | sed -n '/^Events:/,$p'

echo
echo "### 6 · El back-off: cada vez espera más"
echo "\$ kubectl get events --field-selector involvedObject.name=web,reason=BackOff"
k get events --field-selector involvedObject.name=web,reason=BackOff -o custom-columns=MOTIVO:.reason,VECES:.count,MENSAJE:.message
echo "\$ kubectl get pods"
k get pods

echo
echo "### 7 · Arreglar la etiqueta en un Deployment"
echo "\$ kubectl create deployment tienda --image=nginx:1.30.99-alpine"
k create deployment tienda --image=nginx:1.30.99-alpine
sleep 20
echo "\$ kubectl get pods -l app=tienda"
k get pods -l app=tienda
echo "\$ kubectl set image deployment/tienda nginx=nginx:1.30.5-alpine"
k set image deployment/tienda nginx=nginx:1.30.5-alpine
k rollout status deployment/tienda --timeout=120s
echo "\$ kubectl get pods -l app=tienda"
k get pods -l app=tienda
