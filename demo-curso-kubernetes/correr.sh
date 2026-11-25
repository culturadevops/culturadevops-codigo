#!/bin/sh
# Demo de «Kubernetes: curso completo en un vídeo» (cultura-devops, 2026-10-20). Corre DENTRO del contenedor de k3s.
set -u
k() { kubectl "$@" 2>&1; }
cd /trabajo
echo "### 1 · El clúster"
echo "\$ kubectl get nodes -o wide"
k get nodes -o custom-columns=NOMBRE:.metadata.name,ESTADO:.status.conditions[-1].type,VERSION:.status.nodeInfo.kubeletVersion
kubectl wait --for=condition=Ready pod -l k8s-app=kube-dns -n kube-system --timeout=180s >/dev/null 2>&1
kubectl wait --for=condition=Ready pod -l k8s-app=metrics-server -n kube-system --timeout=180s >/dev/null 2>&1
echo "\$ kubectl get pods -n kube-system   # los ayudantes del clúster"
k get pods -n kube-system -o custom-columns=POD:.metadata.name,ESTADO:.status.phase | grep -v helm-install

echo
echo "### 2 · Un Deployment"
echo "\$ kubectl create namespace curso && kubectl config set-context --current --namespace=curso"
k create namespace curso
k config set-context --current --namespace=curso >/dev/null
echo "\$ kubectl apply -f 1-deployment.yaml"
k apply -f 1-deployment.yaml
k rollout status deployment/web --timeout=180s >/dev/null
echo "\$ kubectl get deployment,pods"
k get deployment web
k get pods -o custom-columns=POD:.metadata.name,ESTADO:.status.phase,IMAGEN:.spec.containers[0].image

echo
echo "### 3 · Actualizar y volver atrás"
echo "\$ kubectl set image deployment/web nginx=nginx:1.29.1-alpine"
k set image deployment/web nginx=nginx:1.29.1-alpine
k rollout status deployment/web --timeout=180s
echo "\$ kubectl set image deployment/web nginx=nginx:no-existe   # una versión rota"
k set image deployment/web nginx=nginx:no-existe
sleep 25
echo "\$ kubectl get pods"
k get pods -o custom-columns=POD:.metadata.name,ESTADO:.status.containerStatuses[0].state.waiting.reason,LISTO:.status.containerStatuses[0].ready
echo "\$ kubectl rollout undo deployment/web"
k rollout undo deployment/web
k rollout status deployment/web --timeout=180s
echo "\$ kubectl rollout history deployment/web"
k rollout history deployment/web

echo
echo "### 4 · Un Service delante"
echo "\$ kubectl apply -f 2-service.yaml && kubectl get service web"
k apply -f 2-service.yaml
k get service web -o custom-columns=NOMBRE:.metadata.name,TIPO:.spec.type,PUERTO:.spec.ports[0].port
echo "\$ kubectl run prueba --rm -i --image=busybox:1.37 --restart=Never -- wget -qO- http://web | grep title"
kubectl run prueba --rm -i --image=busybox:1.37 --restart=Never -- wget -qO- http://web 2>/dev/null | grep -i "<title>" | head -1

echo
echo "### 5 · Configuración: ConfigMap y Secret"
echo "\$ kubectl create configmap app --from-literal=ENTORNO=produccion"
k create configmap app --from-literal=ENTORNO=produccion
echo "\$ kubectl create secret generic db --from-literal=CLAVE=s3cr3to"
k create secret generic db --from-literal=CLAVE=s3cr3to
echo "\$ kubectl get secret db -o jsonpath='{.data.CLAVE}'   # NO está cifrado: es base64"
k get secret db -o jsonpath='{.data.CLAVE}'; echo
echo "\$ kubectl get secret db -o jsonpath='{.data.CLAVE}' | base64 -d"
kubectl get secret db -o jsonpath='{.data.CLAVE}' | base64 -d; echo
echo "\$ kubectl apply -f 3-config.yaml && kubectl logs config"
k apply -f 3-config.yaml
sleep 12
k logs config

echo
echo "### 6 · Salud: la liveness probe reinicia lo que se cuelga"
echo "\$ kubectl apply -f 4-probe.yaml"
k apply -f 4-probe.yaml
for i in $(seq 1 60); do [ "$(kubectl get pod colgado -o jsonpath='{.status.containerStatuses[0].restartCount}')" -ge 1 ] 2>/dev/null && break; sleep 2; done
echo "\$ kubectl get pod colgado   # el contenedor borra su archivo de salud a los 15 s"
k get pod colgado -o custom-columns=POD:.metadata.name,REINICIOS:.status.containerStatuses[0].restartCount
echo "\$ kubectl get events --field-selector involvedObject.name=colgado | grep -i liveness"
k get events --field-selector involvedObject.name=colgado -o custom-columns=MOTIVO:.reason,MENSAJE:.message | grep -i liveness | head -2

echo
echo "### 7 · Límites: pasar de la memoria pedida"
echo "\$ kubectl apply -f 5-limites.yaml   # límite 64 MiB, el programa pide 128"
k apply -f 5-limites.yaml
sleep 20
echo "\$ kubectl get pod tragon -o jsonpath='{.status.containerStatuses[0].lastState.terminated.reason} {.status.containerStatuses[0].lastState.terminated.exitCode}'"
k get pod tragon -o jsonpath='{.status.containerStatuses[0].lastState.terminated.reason} {.status.containerStatuses[0].lastState.terminated.exitCode}'; echo

echo
echo "### 8 · Limpiar: borrar el namespace borra todo lo de dentro"
echo "\$ kubectl delete namespace curso"
k delete namespace curso
echo "\$ kubectl get all -n curso"
k get all -n curso
