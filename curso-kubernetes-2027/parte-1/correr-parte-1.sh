#!/bin/bash
# Curso de Kubernetes 2027 · Parte 1: el Pod. Corre en Git Bash, en la máquina; kubectl va dentro del
# nodo k8s-a-control-plane (v1.34.0). Escribe SALIDA-parte-1.md. Destructivo SOLO dentro de kind:
# apaga de golpe el contenedor k8s-a-worker2 (un nodo del clúster desechable) y lo vuelve a encender.
# Uso: bash correr-parte-1.sh
set -u
cd "$(dirname "$0")"
. ../comun/lib.sh
SAL=SALIDA-parte-1.md
docker exec "$NODO" rm -rf /curso; docker cp .. "$NODO":/curso >/dev/null
NS=parte1
{
echo "# SALIDA — Curso de Kubernetes 2027 · Parte 1: el Pod"
echo
echo "> Corrida del $(date '+%Y-%m-%d %H:%M'). kind v0.30.0, clúster k8s-a (1 plano de control + 2 workers), kindest/node:v1.34.0."
echo "> Imágenes ya descargadas en los nodos antes de correr (no se mide la descarga)."
echo "> Contenedores ajenos vivos al empezar: $(ajenos)"
echo
echo '```'
titulo "1 · El clúster"
muestra kubectl version
k version | grep -v Kustomize
muestra kubectl get nodes
k get nodes
ns_nuevo $NS
k config set-context --current --namespace=$NS >/dev/null
muestra "kubectl create namespace $NS && kubectl config set-context --current --namespace=$NS"

titulo "2 · Un pod"
muestra kubectl apply -f 1-pod.yaml
kapply 1-pod.yaml
k wait --for=condition=Ready pod/web --timeout=120s >/dev/null
muestra kubectl get pod web -o wide
k get pod web -o wide
muestra "kubectl get pod web -o jsonpath='{.metadata.uid}'"
k get pod web -o jsonpath='{.metadata.uid}'; echo
NODOWEB=$(k get pod web -o jsonpath='{.spec.nodeName}')

titulo "3 · Qué hay dentro: el contenedor pause"
muestra "crictl pods --name web   # dentro del nodo $NODOWEB"
docker exec "$NODOWEB" crictl pods --name '^web$' | awk '{print $1, $(NF-4), $(NF-3)}'
POD_ID=$(docker exec "$NODOWEB" crictl pods --name '^web$' -q | head -1)
muestra "crictl ps --pod $POD_ID"
docker exec "$NODOWEB" crictl ps --pod "$POD_ID" | awk '{print $1, $(NF-5), $(NF-4)}'
CID=$(docker exec "$NODOWEB" crictl ps --pod "$POD_ID" -q | head -1)
muestra "crictl inspectp $POD_ID | jq -r '.info.runtimeSpec.annotations[\"io.kubernetes.cri.podsandbox.image-name\"]'"
docker exec "$NODOWEB" sh -c "crictl inspectp $POD_ID | jq -r '.info.runtimeSpec.annotations[\"io.kubernetes.cri.podsandbox.image-name\"]'"
PS=$(docker exec "$NODOWEB" sh -c "crictl inspectp $POD_ID | jq .info.pid"); PC=$(docker exec "$NODOWEB" sh -c "crictl inspect $CID | jq .info.pid")
muestra "cat /proc/$PS/comm /proc/$PC/comm ; readlink /proc/$PS/ns/net /proc/$PC/ns/net"
docker exec "$NODOWEB" sh -c "cat /proc/$PS/comm /proc/$PC/comm; readlink /proc/$PS/ns/net /proc/$PC/ns/net"

titulo "4 · Multicontenedor: init + sidecar nativo"
muestra kubectl apply -f 2-sidecar.yaml
kapply 2-sidecar.yaml
k wait --for=condition=Ready pod/con-sidecar --timeout=120s >/dev/null
muestra kubectl get pod con-sidecar
k get pod con-sidecar
muestra "kubectl get pod con-sidecar -o jsonpath='{range .status.initContainerStatuses[*]}{.name} {.state}{\"\\n\"}{end}'"
k get pod con-sidecar -o jsonpath='{range .status.initContainerStatuses[*]}{.name}{" "}{.state}{"\n"}{end}' | sed -E 's/\{"(running|terminated)":\{.*"reason":"([A-Za-z]+)".*/\1 (\2)/; s/\{"running":\{.*/running/'
muestra "kubectl exec con-sidecar -c lector-logs -- wget -qO- http://localhost   # otro contenedor, mismo localhost"
k exec con-sidecar -c lector-logs -- wget -qO- http://localhost
muestra "kubectl exec con-sidecar -c lector-logs -- hostname ; kubectl exec con-sidecar -c nginx -- hostname"
k exec con-sidecar -c lector-logs -- hostname; k exec con-sidecar -c nginx -- hostname
sleep 1
muestra "kubectl logs con-sidecar -c lector-logs"
k logs con-sidecar -c lector-logs | sed -E 's/\[[^]]*\]/[fecha]/'

titulo "5 · Fases y restartPolicy"
muestra kubectl apply -f 3-fases.yaml
( nodo_sh "sh /curso/comun/vigila.sh $NS termina-bien 12 0.2" > /tmp/k8sa-vigila-bien.txt ) &
VIG=$!
sleep 0.3
kapply 3-fases.yaml
wait $VIG
echo "--- termina-bien, cada cambio de READY STATUS RESTARTS:"
cat /tmp/k8sa-vigila-bien.txt
sleep 2
muestra kubectl get pods termina-bien termina-mal reintenta siempre
k get pods termina-bien termina-mal reintenta siempre
muestra "kubectl get pods -o custom-columns=POD:.metadata.name,FASE:.status.phase,POLITICA:.spec.restartPolicy,SALIDA:.status.containerStatuses[0].state.terminated.exitCode,ULTIMA:.status.containerStatuses[0].lastState.terminated.exitCode"
k get pods termina-bien termina-mal reintenta siempre -o custom-columns=POD:.metadata.name,FASE:.status.phase,POLITICA:.spec.restartPolicy,SALIDA:.status.containerStatuses[0].state.terminated.exitCode,ULTIMA:.status.containerStatuses[0].lastState.terminated.exitCode

titulo "6 · Back-off de reinicios: pod reintenta (sale con 1 cada vez), 150 s mirando"
nodo_sh "sh /curso/comun/vigila.sh $NS reintenta 150 0.5"
muestra kubectl get pod reintenta
k get pod reintenta
muestra "kubectl describe pod reintenta | grep -i back-off"
k describe pod reintenta | grep -i "back-off" | sed -E 's/ +/ /g' | head -2
k delete pod termina-bien termina-mal reintenta siempre --now >/dev/null

titulo "7 · Muere el proceso: el pod sigue, el contenedor se reinicia"
muestra "kubectl exec web -- sh -c 'echo hola > /tmp/marca; echo hola > /datos/marca'"
k exec web -- sh -c 'echo hola > /tmp/marca; echo hola > /datos/marca'
IP1=$(k get pod web -o jsonpath='{.status.podIP}'); UID1=$(k get pod web -o jsonpath='{.metadata.uid}')
muestra "kubectl exec web -- kill 1   # señal TERM al proceso principal (nginx)"
T0=$(ms)
k exec web -- kill 1
until [ "$(k get pod web -o jsonpath='{.status.containerStatuses[0].restartCount}')" = "1" ] && [ "$(k get pod web -o jsonpath='{.status.containerStatuses[0].ready}')" = "true" ]; do sleep 0.2; done
T1=$(ms)
echo "(el contenedor volvió a estar listo $((T1 - T0)) ms después del kill, medido desde la máquina)"
muestra kubectl get pod web -o wide
k get pod web -o wide
IP2=$(k get pod web -o jsonpath='{.status.podIP}'); UID2=$(k get pod web -o jsonpath='{.metadata.uid}')
echo "IP antes: $IP1 · después: $IP2"
[ "$UID1" = "$UID2" ] && echo "UID: el mismo ($UID2)" || echo "UID: cambió ($UID1 -> $UID2)"
muestra "kubectl get pod web -o jsonpath='{.status.containerStatuses[0].lastState.terminated}'"
k get pod web -o jsonpath='{.status.containerStatuses[0].lastState.terminated.reason} exitCode={.status.containerStatuses[0].lastState.terminated.exitCode}'; echo
muestra "kubectl exec web -- cat /tmp/marca   # el sistema de archivos del contenedor"
k exec web -- cat /tmp/marca
muestra "kubectl exec web -- cat /datos/marca   # el volumen emptyDir del pod"
k exec web -- cat /datos/marca
muestra "kubectl logs web --previous | tail -3"
k logs web --previous | tail -3 | sed -E 's#^[0-9/]+ [0-9:]+ #[fecha] #'
muestra "kubectl describe pod web   # la sección Events"
k describe pod web | sed -n '/^Events:/,$p' | sed -E 's/ +/ /g'

titulo "8 · Borrar el pod: nadie lo vuelve a crear"
muestra kubectl delete pod web
T0=$(ms); k delete pod web; T1=$(ms)
echo "(kubectl delete tardó $((T1 - T0)) ms)"
sleep 5
muestra kubectl get pod web
k get pod web

titulo "9 · Muere el NODO (docker kill k8s-a-worker2: corte de luz, sin apagado ordenado)"
muestra kubectl apply -f 4-en-worker2.yaml
kapply 4-en-worker2.yaml
k wait --for=condition=Ready pod/huerfano --timeout=120s >/dev/null
k get pod huerfano -o wide | awk '{print $1, $2, $3, $7}'
muestra "kubectl get pod huerfano -o jsonpath='{.spec.tolerations}'   # las que pone Kubernetes solo"
k get pod huerfano -o jsonpath='{range .spec.tolerations[*]}{.key} {.effect} {.tolerationSeconds}{"\n"}{end}'
muestra "docker kill k8s-a-worker2"
docker kill k8s-a-worker2 >/dev/null
T0=$(ms); prev=""
while :; do
  dt=$(( ($(ms) - T0) / 1000 ))
  [ $dt -gt 420 ] && break
  n=$(k get node k8s-a-worker2 --no-headers | awk '{print $2}')
  p=$(k get pod huerfano --no-headers 2>&1 | awk '{print $2, $3}')
  r=$(k get pod huerfano -o jsonpath='{.status.conditions[?(@.type=="Ready")].status}' 2>/dev/null)
  tn=$(k get node k8s-a-worker2 -o jsonpath='{range .spec.taints[*]}{.key}:{.effect} {end}' | sed 's#node.kubernetes.io/##g')
  l="nodo=$n · pod=$p · Ready=$r · taints=$tn"
  if [ "$l" != "$prev" ]; then printf '%4d s  %s\n' "$dt" "$l"; prev="$l"; fi
  sleep 2
done
muestra kubectl get pod huerfano
k get pod huerfano
muestra "docker start k8s-a-worker2   # vuelve la luz"
docker start k8s-a-worker2 >/dev/null
T0=$(ms)
until [ "$(k get node k8s-a-worker2 --no-headers | awk '{print $2}')" = "Ready" ]; do sleep 2; done
echo "(nodo Ready otra vez $(( ($(ms) - T0) / 1000 )) s después de encenderlo)"
for i in $(seq 1 60); do k get pod huerfano >/dev/null 2>&1 || break; sleep 2; done
muestra kubectl get pod huerfano
k get pod huerfano
echo '```'
echo
echo "> Contenedores ajenos vivos al terminar: $(ajenos)"
} > "$SAL" 2>&1
echo "listo: $SAL"
