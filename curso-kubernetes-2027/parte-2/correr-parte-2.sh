#!/bin/bash
# Curso de Kubernetes 2027 · Parte 2: ReplicaSet y Deployment. Git Bash en la máquina; kubectl dentro
# del nodo k8s-a-control-plane (v1.34.0). Escribe SALIDA-parte-2.md. Todo dentro del clúster kind.
# Uso: bash correr-parte-2.sh
set -u
cd "$(dirname "$0")"
. ../comun/lib.sh
SAL=SALIDA-parte-2.md
docker exec "$NODO" rm -rf /curso; docker cp .. "$NODO":/curso >/dev/null
NS=parte2
# Peticiones del cliente entre dos segundos (época): totales por versión y errores
trafico() {
  k logs cliente | awk -v a="$1" -v b="$2" '$1>=a && $1<=b {n++; c[$2]++} END {printf "peticiones: %d", n; for (v in c) printf " · %s: %d", v, c[v]; printf "\n"}'
}
# Un rollout medido: nombre, imagen nueva, segundos máximo
medir() {
  local img=$1 causa=$2 max=${3:-90}
  local t1; t1=$(date +%s)
  ( nodo_sh "sh /curso/comun/cuenta.sh $NS app=web $img 4 $max" > /tmp/k8sa-cuenta.txt ) &
  local pid=$!
  sleep 0.3
  k set image deployment/web nginx="$img" >/dev/null
  k annotate deployment web kubernetes.io/change-cause="$causa" --overwrite >/dev/null
  wait $pid
  cat /tmp/k8sa-cuenta.txt
  sleep 2
  echo "tráfico durante el rollout → $(trafico "$t1" "$(date +%s)")"
}
{
echo "# SALIDA — Curso de Kubernetes 2027 · Parte 2: ReplicaSet y Deployment"
echo
echo "> Corrida del $(date '+%Y-%m-%d %H:%M'). kind v0.30.0, clúster k8s-a (1 plano de control + 2 workers), kindest/node:v1.34.0."
echo "> Imágenes ya descargadas en los nodos. Contenedores ajenos vivos al empezar: $(ajenos)"
echo
echo '```'
ns_nuevo $NS
k config set-context --current --namespace=$NS >/dev/null

titulo "1 · ReplicaSet: etiquetas y selector"
muestra kubectl apply -f 1-replicaset.yaml
kapply 1-replicaset.yaml
k wait --for=condition=Ready pod -l app=web-rs --timeout=120s >/dev/null
muestra kubectl get rs web-rs
k get rs web-rs
muestra kubectl get pods --show-labels
k get pods --show-labels
muestra "kubectl get pods -l app=web-rs -o name"
k get pods -l app=web-rs -o name

titulo "2 · Borro un pod: el ReplicaSet crea otro"
VICTIMA=$(k get pods -l app=web-rs -o jsonpath='{.items[0].metadata.name}')
muestra kubectl delete pod $VICTIMA --wait=false
T0=$(ms); k delete pod "$VICTIMA" --wait=false
while :; do
  n=$(k get pods -l app=web-rs --field-selector=status.phase=Running -o jsonpath='{range .items[*]}{.metadata.name} {.status.containerStatuses[0].ready} {.metadata.deletionTimestamp}{"\n"}{end}' | awk '$2=="true" && $3=="" {c++} END {print c+0}')
  [ "$n" = "3" ] && ! k get pods -l app=web-rs -o name | grep -q "$VICTIMA" && break
  sleep 0.2
done
echo "(3 pods listos otra vez $(( $(ms) - T0 )) ms después del delete, medido desde la máquina)"
muestra kubectl get pods -l app=web-rs
k get pods -l app=web-rs

titulo "3 · Le cambio la etiqueta a un pod: deja de contar"
SACADO=$(k get pods -l app=web-rs -o jsonpath='{.items[0].metadata.name}')
muestra kubectl label pod $SACADO app=fuera --overwrite
k label pod "$SACADO" app=fuera --overwrite
sleep 4
muestra "kubectl get pods -L app"
k get pods -L app
muestra "kubectl get pod $SACADO -o jsonpath='{.metadata.ownerReferences}'   # ¿de quién es?"
o=$(k get pod "$SACADO" -o jsonpath='{.metadata.ownerReferences}'); echo "${o:-(vacío: ya no es de nadie)}"
k delete pod "$SACADO" --wait=false >/dev/null

titulo "4 · Un pod suelto con la misma etiqueta: el ReplicaSet lo adopta y sobra uno"
muestra kubectl apply -f 2-intruso.yaml
kapply 2-intruso.yaml
sleep 4
muestra "kubectl get pods -l app=web-rs"
k get pods -l app=web-rs
muestra "kubectl get events --field-selector reason=SuccessfulDelete -o custom-columns=MOTIVO:.reason,MENSAJE:.message"
k get events --field-selector reason=SuccessfulDelete -o custom-columns=MOTIVO:.reason,MENSAJE:.message | tail -1

titulo "5 · El ReplicaSet NO actualiza los pods que ya existen"
muestra kubectl set image rs/web-rs nginx=nginx:1.30.6-alpine
k set image rs/web-rs nginx=nginx:1.30.6-alpine
sleep 3
muestra "kubectl get pods -l app=web-rs -o custom-columns=POD:.metadata.name,IMAGEN:.spec.containers[0].image"
k get pods -l app=web-rs -o custom-columns=POD:.metadata.name,IMAGEN:.spec.containers[0].image
OTRO=$(k get pods -l app=web-rs -o jsonpath='{.items[0].metadata.name}')
muestra kubectl delete pod $OTRO
k delete pod "$OTRO" >/dev/null; sleep 5
k get pods -l app=web-rs -o custom-columns=POD:.metadata.name,IMAGEN:.spec.containers[0].image
k delete rs web-rs --wait=true >/dev/null; k delete pod intruso --ignore-not-found >/dev/null

titulo "6 · Deployment → ReplicaSet → pods"
muestra kubectl apply -f 3-deployment.yaml
kapply 3-deployment.yaml
k rollout status deployment/web --timeout=180s >/dev/null
k wait --for=condition=Ready pod/cliente --timeout=120s >/dev/null
k annotate deployment web kubernetes.io/change-cause="primera versión 1.29.8" >/dev/null
muestra kubectl get deployment,rs,pods -l app=web
k get deployment web; k get rs -l app=web; k get pods -l app=web
P1=$(k get pods -l app=web -o jsonpath='{.items[0].metadata.name}')
muestra "kubectl get pod $P1 -o jsonpath='{.metadata.ownerReferences[0].kind}/{.metadata.ownerReferences[0].name}'"
k get pod "$P1" -o jsonpath='{.metadata.ownerReferences[0].kind}/{.metadata.ownerReferences[0].name}'; echo
muestra "kubectl get deployment web -o jsonpath='{.spec.strategy}'   # la estrategia por defecto"
k get deployment web -o jsonpath='{.spec.strategy}'; echo
muestra "kubectl logs cliente --tail=3   # el cliente ya está pidiendo"
k logs cliente --tail=3
T1=$(date +%s); sleep 30
echo "línea base, 30 s sin tocar nada → $(trafico "$T1" "$(date +%s)")"

titulo "7 · Rollout A: por defecto (maxSurge 25 %, maxUnavailable 25 %) · 4 réplicas · 1.29.8 → 1.30.6"
muestra kubectl set image deployment/web nginx=nginx:1.30.6-alpine
medir nginx:1.30.6-alpine "A: 25%/25% a 1.30.6"

titulo "8 · Rollout B: maxSurge 1, maxUnavailable 0 · 1.30.6 → 1.29.8"
muestra "kubectl patch deployment web -p '{\"spec\":{\"strategy\":{\"rollingUpdate\":{\"maxSurge\":1,\"maxUnavailable\":0}}}}'"
k patch deployment web --type=merge -p '{"spec":{"strategy":{"type":"RollingUpdate","rollingUpdate":{"maxSurge":1,"maxUnavailable":0}}}}'
muestra kubectl set image deployment/web nginx=nginx:1.29.8-alpine
medir nginx:1.29.8-alpine "B: surge 1, unavailable 0 a 1.29.8"

titulo "9 · Rollout C: maxSurge 100 %, maxUnavailable 0 · 1.29.8 → 1.30.6"
k patch deployment web --type=merge -p '{"spec":{"strategy":{"type":"RollingUpdate","rollingUpdate":{"maxSurge":"100%","maxUnavailable":0}}}}'
muestra "kubectl patch … maxSurge \"100%\", maxUnavailable 0"
muestra kubectl set image deployment/web nginx=nginx:1.30.6-alpine
medir nginx:1.30.6-alpine "C: surge 100% a 1.30.6"

titulo "10 · Rollout D: strategy Recreate · 1.30.6 → 1.29.8"
k patch deployment web --type=merge -p '{"spec":{"strategy":{"type":"Recreate","rollingUpdate":null}}}'
muestra "kubectl patch deployment web -p '{\"spec\":{\"strategy\":{\"type\":\"Recreate\",\"rollingUpdate\":null}}}'"
muestra kubectl set image deployment/web nginx=nginx:1.29.8-alpine
medir nginx:1.29.8-alpine "D: Recreate a 1.29.8"

titulo "11 · Rollout E: igual que B + preStop sleep 5 s · 1.29.8 → 1.30.6"
k patch deployment web --type=merge -p '{"spec":{"strategy":{"type":"RollingUpdate","rollingUpdate":{"maxSurge":1,"maxUnavailable":0}}}}' >/dev/null
echo "    lifecycle:"
echo "      preStop:"
echo "        sleep:"
echo "          seconds: 5"
muestra "kubectl patch deployment web -p '{…containers:[{name: nginx, image: nginx:1.30.6-alpine, lifecycle: {preStop: {sleep: {seconds: 5}}}}]}'"
T1=$(date +%s)
( nodo_sh "sh /curso/comun/cuenta.sh $NS app=web nginx:1.30.6-alpine 4 120" > /tmp/k8sa-cuenta.txt ) &
PID=$!; sleep 0.3
k patch deployment web --type=strategic -p '{"spec":{"template":{"spec":{"containers":[{"name":"nginx","image":"nginx:1.30.6-alpine","lifecycle":{"preStop":{"sleep":{"seconds":5}}}}]}}}}' >/dev/null
k annotate deployment web kubernetes.io/change-cause="E: B + preStop 5 s a 1.30.6" --overwrite >/dev/null
wait $PID; cat /tmp/k8sa-cuenta.txt; sleep 2
echo "tráfico durante el rollout → $(trafico "$T1" "$(date +%s)")"

titulo "11b · Rollout F: igual que E, ahora que los pods VIEJOS ya tienen el preStop · 1.30.6 → 1.29.8"
muestra "kubectl get deployment web -o jsonpath='{.spec.template.spec.containers[0].lifecycle}'"
k get deployment web -o jsonpath='{.spec.template.spec.containers[0].lifecycle}'; echo
muestra kubectl set image deployment/web nginx=nginx:1.29.8-alpine
medir nginx:1.29.8-alpine "F: preStop en viejos y nuevos a 1.29.8"

titulo "12 · Historia de revisiones"
muestra kubectl rollout history deployment/web
k rollout history deployment/web
muestra kubectl get rs -l app=web
k get rs -l app=web

titulo "13 · Una versión rota con maxUnavailable 0 (y progressDeadlineSeconds 30)"
k patch deployment web --type=merge -p '{"spec":{"progressDeadlineSeconds":30}}' >/dev/null
muestra "kubectl set image deployment/web nginx=nginx:1.99.0-alpine   # esa versión no existe"
T1=$(date +%s)
( nodo_sh "sh /curso/comun/cuenta.sh $NS app=web nginx:1.99.0-alpine 4 50" > /tmp/k8sa-cuenta.txt ) &
PID=$!; sleep 0.3
k set image deployment/web nginx=nginx:1.99.0-alpine
k annotate deployment web kubernetes.io/change-cause="rota: 1.99.0 no existe" --overwrite >/dev/null
wait $PID; cat /tmp/k8sa-cuenta.txt
echo "tráfico durante los 50 s → $(trafico "$T1" "$(date +%s)")"
muestra kubectl get pods -l app=web
k get pods -l app=web
muestra kubectl rollout status deployment/web
k rollout status deployment/web --timeout=10s
muestra "kubectl get deployment web -o jsonpath='{.status.conditions[?(@.type==\"Progressing\")].reason}'"
k get deployment web -o jsonpath='{.status.conditions[?(@.type=="Progressing")].reason}'; echo
muestra kubectl rollout undo deployment/web
T0=$(ms); k rollout undo deployment/web
k rollout status deployment/web --timeout=120s
echo "(rollout undo completo $(( $(ms) - T0 )) ms después)"
muestra "kubectl get pods -l app=web -o custom-columns=POD:.metadata.name,IMAGEN:.spec.containers[0].image,LISTO:.status.containerStatuses[0].ready"
k get pods -l app=web -o custom-columns=POD:.metadata.name,IMAGEN:.spec.containers[0].image,LISTO:.status.containerStatuses[0].ready
muestra kubectl rollout history deployment/web
k rollout history deployment/web
echo '```'
echo
echo "> Contenedores ajenos vivos al terminar: $(ajenos)"
} > "$SAL" 2>&1
echo "listo: $SAL"
