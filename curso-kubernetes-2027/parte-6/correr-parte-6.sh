#!/usr/bin/env bash
# Parte 6 · Otros controladores: StatefulSet, DaemonSet, Job y CronJob. Escribe SALIDA-parte-6.md.
#   bash correr-parte-6.sh       (clúster k8s-b: bash ../parte-5/cluster-k8s-b.sh up)
set -u
cd "$(dirname "$0")"
source ../parte-5/lib-k8s-b.sh
M=manifiestos
SALIDA=SALIDA-parte-6.md
NS=curso6
seg() { date -d "$1" +%s; }   # ISO 8601 -> epoch

# columnas: pod, nodo, creado, listo (horas del API)
filas() {
  k get pods -l "$1" --sort-by=.metadata.creationTimestamp \
    -o custom-columns='POD:.metadata.name,NODO:.spec.nodeName,CREADO:.metadata.creationTimestamp,LISTO:.status.conditions[?(@.type=="Ready")].lastTransitionTime'
}

{
encabezado 6 correr-parte-6.sh
k delete namespace curso6 --ignore-not-found --wait=true >/dev/null
k create namespace curso6 >/dev/null

titulo "1 · StatefulSet: nombres estables y arranque en orden"
aplicar $M/1-statefulset.yaml
k rollout status statefulset/web --timeout=300s >/dev/null
echo '$ kubectl get pods -l app=web   # con la hora en que se creó y en que quedó listo cada uno'
filas app=web
c0=$(seg "$(k get pod web-0 -o jsonpath='{.metadata.creationTimestamp}')")
r0=$(seg "$(k get pod web-0 -o jsonpath='{.status.conditions[?(@.type=="Ready")].lastTransitionTime}')")
c1=$(seg "$(k get pod web-1 -o jsonpath='{.metadata.creationTimestamp}')")
r1=$(seg "$(k get pod web-1 -o jsonpath='{.status.conditions[?(@.type=="Ready")].lastTransitionTime}')")
c2=$(seg "$(k get pod web-2 -o jsonpath='{.metadata.creationTimestamp}')")
echo "# web-0 listo a los $((r0-c0)) s · web-1 creado $((c1-r0)) s después de que web-0 quedara listo · web-2 creado $((c2-r1)) s después de web-1 listo"
echo "# de web-0 creado a web-2 creado: $((c2-c0)) s"

titulo "2 · Un PVC por réplica"
x get pvc -o custom-columns=PVC:.metadata.name,ESTADO:.status.phase,TAMANO:.status.capacity.storage
for p in web-0 web-1 web-2; do echo "\$ kubectl exec $p -- cat /datos/index.html"; k exec $p -- cat /datos/index.html; done

titulo "3 · DNS por pod con el Service headless"
x get service web -o custom-columns=NOMBRE:.metadata.name,CLUSTER-IP:.spec.clusterIP
k run dns --image=busybox:1.37 --restart=Never -- sleep 600 >/dev/null
k wait --for=condition=Ready pod/dns --timeout=120s >/dev/null
echo '$ kubectl exec dns -- nslookup web.curso6.svc.cluster.local   # el headless devuelve las IP de los pods'
k exec dns -- nslookup web.curso6.svc.cluster.local | grep -E '^Name|^Address' | grep -v ':53'
echo '$ kubectl exec dns -- nslookup web-1.web.curso6.svc.cluster.local'
k exec dns -- nslookup web-1.web.curso6.svc.cluster.local | grep -E '^Name|^Address' | grep -v ':53'
echo '$ kubectl exec dns -- wget -qO- http://web-1.web'
k exec dns -- wget -qO- http://web-1.web

titulo "4 · Borrar web-1: vuelve con el mismo nombre y el mismo disco"
IP_ANTES=$(k get pod web-1 -o jsonpath='{.status.podIP}')
UID_ANTES=$(k get pod web-1 -o jsonpath='{.metadata.uid}')
echo '$ kubectl delete pod web-1'
k delete pod web-1 --wait=true
k wait --for=condition=Ready pod/web-1 --timeout=180s >/dev/null
echo "\$ kubectl get pod web-1 -o custom-columns=POD:.metadata.name,IP:.status.podIP,UID:.metadata.uid"
k get pod web-1 -o custom-columns=POD:.metadata.name,IP:.status.podIP,UID:.metadata.uid
echo "# antes: IP $IP_ANTES · UID $UID_ANTES"
echo '$ kubectl exec dns -- wget -qO- http://web-1.web   # mismo PVC: conserva la hora en que nació la primera vez'
k exec dns -- wget -qO- http://web-1.web

titulo "5 · Escalar: baja en orden inverso y los PVC se quedan"
echo '$ kubectl scale statefulset web --replicas=1'
k scale statefulset web --replicas=1
t0=$(date +%s)
for i in $(seq 1 120); do
  [ "$(k get pods -l app=web --no-headers 2>/dev/null | wc -l)" -le 1 ] && break
  sleep 1
done
echo "# quedó 1 pod en $(( $(date +%s) - t0 )) s"
k get events --sort-by=.lastTimestamp --field-selector reason=SuccessfulDelete,involvedObject.kind=StatefulSet -o custom-columns=MENSAJE:.message | sed 's/^/  /'
x get pods -l app=web -o custom-columns=POD:.metadata.name
x get pvc -o custom-columns=PVC:.metadata.name,ESTADO:.status.phase
echo '$ kubectl scale statefulset web --replicas=3'
k scale statefulset web --replicas=3
k rollout status statefulset/web --timeout=300s >/dev/null
echo '$ kubectl exec dns -- wget -qO- http://web-2.web   # web-2 vuelve a su PVC de antes'
k exec dns -- wget -qO- http://web-2.web

titulo "6 · Comparar con un Deployment"
aplicar $M/2-deployment-comparar.yaml
k rollout status deployment/web-deploy --timeout=180s >/dev/null
x get pods -l app=web-deploy -o custom-columns=POD:.metadata.name
k delete deployment web-deploy >/dev/null

titulo "7 · DaemonSet: uno por nodo"
aplicar $M/3-daemonset.yaml
k rollout status daemonset/agente-nodo --timeout=180s >/dev/null
x get daemonset agente-nodo -o custom-columns=NOMBRE:.metadata.name,DESEADOS:.status.desiredNumberScheduled,LISTOS:.status.numberReady
x get pods -l app=agente-nodo -o custom-columns=POD:.metadata.name,NODO:.spec.nodeName
echo "\$ kubectl get node k8s-b-control-plane -o jsonpath='{.spec.taints[*].key}'"
k get node k8s-b-control-plane -o jsonpath='{.spec.taints[*].key}'; echo
aplicar $M/4-daemonset-tolera.yaml
k rollout status daemonset/agente-nodo --timeout=180s >/dev/null
x get pods -l app=agente-nodo -o custom-columns=POD:.metadata.name,NODO:.spec.nodeName
P1=$(k get pods -l app=agente-nodo -o jsonpath='{.items[0].metadata.name}')
echo "\$ kubectl logs $P1"
k logs "$P1"
k delete daemonset agente-nodo >/dev/null

titulo "8 · Job: completions y parallelism"
aplicar $M/5-job.yaml
k wait --for=condition=Complete job/lote --timeout=300s >/dev/null
x get job lote -o custom-columns=JOB:.metadata.name,COMPLETADOS:.status.succeeded,INICIO:.status.startTime,FIN:.status.completionTime
s=$(seg "$(k get job lote -o jsonpath='{.status.startTime}')"); f=$(seg "$(k get job lote -o jsonpath='{.status.completionTime}')")
echo "# 6 tareas de 5 s, de 2 en 2: el Job tardó $((f-s)) s"
echo '$ kubectl get pods -l job-name=lote   # de dos en dos'
k get pods -l job-name=lote --sort-by=.metadata.creationTimestamp -o custom-columns=POD:.metadata.name,CREADO:.metadata.creationTimestamp,ESTADO:.status.phase

titulo "9 · Job que falla: backoffLimit"
aplicar $M/6-job-falla.yaml
k wait --for=condition=Failed job/roto --timeout=300s >/dev/null
x get job roto -o custom-columns=JOB:.metadata.name,FALLIDOS:.status.failed,COMPLETADOS:.status.succeeded
echo "\$ kubectl get job roto -o jsonpath='{.status.conditions[?(@.type==\"Failed\")].reason}'"
k get job roto -o jsonpath='{.status.conditions[?(@.type=="Failed")].reason}'; echo
echo '$ kubectl get pods -l job-name=roto   # 1 intento + 2 reintentos, cada vez con más espera'
k get pods -l job-name=roto --sort-by=.metadata.creationTimestamp -o custom-columns=POD:.metadata.name,CREADO:.metadata.creationTimestamp,ESTADO:.status.phase
prev=""
for c in $(k get pods -l job-name=roto --sort-by=.metadata.creationTimestamp -o jsonpath='{range .items[*]}{.metadata.creationTimestamp}{"\n"}{end}'); do
  t=$(seg "$c"); [ -n "$prev" ] && echo "# entre intentos: $((t-prev)) s"; prev=$t
done
P1=$(k get pods -l job-name=roto -o jsonpath='{.items[0].metadata.name}')
echo "\$ kubectl logs $P1"
k logs "$P1"

titulo "10 · CronJob: concurrencyPolicy e historial"
aplicar $M/7-cronjobs.yaml
T0=$(date +%s)
nota "espero 5 minutos y 10 segundos"
sleep 310
echo '$ kubectl get cronjobs'
k get cronjobs -o custom-columns=CRONJOB:.metadata.name,HORARIO:.spec.schedule,CONCURRENCIA:.spec.concurrencyPolicy,ACTIVOS:.status.active[*].name | sed 's/,[^ ]*//'
echo '$ kubectl get jobs   # cuántos Job creó cada CronJob y cuántos siguen corriendo'
for cj in rapido lento-forbid lento-allow; do
  tot=$(k get jobs --no-headers -o custom-columns=N:.metadata.ownerReferences[0].name 2>/dev/null | grep -cx "$cj")
  act=$(k get cronjob "$cj" -o jsonpath='{.status.active[*].name}' | wc -w)
  echo "$cj: jobs guardados $tot · corriendo ahora $act"
done
echo '$ kubectl get jobs -o custom-columns=JOB:.metadata.name,INICIO:.status.startTime,FIN:.status.completionTime'
k get jobs --sort-by=.metadata.creationTimestamp -o custom-columns=JOB:.metadata.name,INICIO:.status.startTime,FIN:.status.completionTime
echo '$ kubectl get pods -l batch.kubernetes.io/controller-uid --field-selector=status.phase=Running   # lento-allow apila'
k get pods --field-selector=status.phase=Running -o custom-columns=POD:.metadata.name | grep -E 'POD|lento'
k delete cronjob --all >/dev/null

titulo "11 · Limpiar"
echo '$ kubectl delete namespace curso6'
k delete namespace curso6
pie
} 2>&1 | tee "$SALIDA"
