#!/usr/bin/env bash
# Parte 7 · Salud y escala: probes, requests/limits, QoS y HPA. Escribe SALIDA-parte-7.md.
#   bash correr-parte-7.sh       (clúster k8s-b: bash ../parte-5/cluster-k8s-b.sh up)
set -u
cd "$(dirname "$0")"
source ../parte-5/lib-k8s-b.sh
M=manifiestos
SALIDA=SALIDA-parte-7.md
NS=curso7
N_CPU=${N_CPU:-25000000}   # rondas de sha256 del trabajo de CPU fijo

listo() { k get pod "$1" -o jsonpath='{.status.conditions[?(@.type=="Ready")].status}'; }
reinicios() { k get pod "$1" -o jsonpath='{.status.containerStatuses[0].restartCount}'; }
post() { k exec "$1" -- wget -qO- --post-data= "http://localhost:8080$2"; }

{
encabezado 7 correr-parte-7.sh
k delete namespace curso7 --ignore-not-found --wait=true >/dev/null
k create namespace curso7 >/dev/null

titulo "1 · Una app que tarda 30 s en arrancar, solo con livenessProbe"
aplicar $M/1-sin-startup.yaml
aplicar $M/2-con-startup.yaml
nota "espero 75 s"
sleep 75
echo '$ kubectl get pods   # a los 75 s'
k get pods -o custom-columns=POD:.metadata.name,LISTO:.status.containerStatuses[0].ready,REINICIOS:.status.containerStatuses[0].restartCount,ESTADO:.status.phase
echo '$ kubectl get events --field-selector involvedObject.name=sin-startup | grep -E "Unhealthy|Killing"'
k get events --field-selector involvedObject.name=sin-startup -o custom-columns=MOTIVO:.reason,VECES:.count,MENSAJE:.message | grep -E "MOTIVO|Unhealthy|Killing"
echo '$ kubectl logs sin-startup --previous'
k logs sin-startup --previous
c=$(date -d "$(k get pod con-startup -o jsonpath='{.status.startTime}')" +%s)
r=$(date -d "$(k get pod con-startup -o jsonpath='{.status.conditions[?(@.type=="Ready")].lastTransitionTime}')" +%s)
echo "# con-startup: listo $((r-c)) s después de arrancar el pod, 0 reinicios esperados: $(reinicios con-startup)"
echo '$ kubectl logs con-startup'
k logs con-startup
k delete pod sin-startup con-startup --wait=false >/dev/null

titulo "2 · readinessProbe: sacar un pod del Service sin reiniciarlo"
aplicar $M/3-probes.yaml
k rollout status deployment/api --timeout=180s >/dev/null
A=$(k get pods -l app=api -o jsonpath='{.items[0].metadata.name}')
B=$(k get pods -l app=api -o jsonpath='{.items[1].metadata.name}')
k run cliente --image=busybox:1.37 --restart=Never -- sleep 3600 >/dev/null
k wait --for=condition=Ready pod/cliente --timeout=120s >/dev/null
echo '$ kubectl get endpointslice -l kubernetes.io/service-name=api   # direcciones listas'
k get endpointslice -l kubernetes.io/service-name=api -o jsonpath='{range .items[*].endpoints[*]}{.targetRef.name} ready={.conditions.ready}{"\n"}{end}'
echo "\$ kubectl exec $A -- wget -qO- --post-data= http://localhost:8080/fuera   # /listo empieza a dar 503"
t0=$(ms); post "$A" /fuera
for i in $(seq 1 100); do
  e=$(k get endpointslice -l kubernetes.io/service-name=api -o jsonpath="{range .items[*].endpoints[?(@.targetRef.name==\"$A\")]}{.conditions.ready}{end}")
  [ "$e" = "false" ] && break
  sleep 0.2
done
t1=$(ms)
echo "# $A salió del Service $(( (t1-t0) )) ms después (readiness cada 2 s, 2 fallos)"
k get endpointslice -l kubernetes.io/service-name=api -o jsonpath='{range .items[*].endpoints[*]}{.targetRef.name} ready={.conditions.ready}{"\n"}{end}'
echo '$ kubectl exec cliente -- sh -c "for i in $(seq 20); do wget -qO- http://api/; done" | contar pods'
k exec cliente -- sh -c 'for i in $(seq 20); do wget -qO- http://api/; echo; done' | grep -o '"pod":"[^"]*"' | sort | uniq -c
echo '$ kubectl get pods -l app=api   # 20 s después'
sleep 20
k get pods -l app=api -o custom-columns=POD:.metadata.name,LISTO:.status.containerStatuses[0].ready,REINICIOS:.status.containerStatuses[0].restartCount
nota "readiness NO reinicia: el pod se queda fuera hasta que /listo vuelva a dar 200"

titulo "3 · livenessProbe: reiniciar un proceso colgado"
echo "\$ kubectl exec $B -- wget -qO- --post-data= http://localhost:8080/colgar   # /salud deja de contestar"
t0=$(ms); post "$B" /colgar
for i in $(seq 1 300); do [ "$(reinicios "$B")" = "1" ] && break; sleep 0.2; done
t1=$(ms)
for i in $(seq 1 300); do [ "$(listo "$B")" = "True" ] && break; sleep 0.2; done
t2=$(ms)
echo "# $B reiniciado $(( t1-t0 )) ms después de colgarse (liveness cada 3 s, timeout 1 s, 3 fallos); listo otra vez a los $(( t2-t0 )) ms"
echo "\$ kubectl get events --field-selector involvedObject.name=$B | grep -E 'Unhealthy|Killing'"
k get events --field-selector involvedObject.name="$B" -o custom-columns=MOTIVO:.reason,MENSAJE:.message | grep -E "Unhealthy|Killing"
k get pods -l app=api -o custom-columns=POD:.metadata.name,LISTO:.status.containerStatuses[0].ready,REINICIOS:.status.containerStatuses[0].restartCount
k delete deployment api >/dev/null; k delete service api >/dev/null

titulo "4 · Límite de CPU: el mismo trabajo, tres límites (medido)"
aplicar $M/4-cpu.yaml
k wait --for=condition=Ready pod/cpu-200m pod/cpu-500m pod/cpu-1 --timeout=120s >/dev/null
candado_tomar
for p in cpu-1 cpu-500m cpu-200m; do
  k exec "$p" -- wget -qO- "http://localhost:8080/cpu?n=100000" >/dev/null   # calentar
  a=$(k exec "$p" -- cat /sys/fs/cgroup/cpu.stat | tr '\n' ' ')
  for r in 1 2 3; do
    echo "\$ kubectl exec $p -- wget -qO- http://localhost:8080/cpu?n=$N_CPU   # corrida $r"
    k exec "$p" -- wget -qO- "http://localhost:8080/cpu?n=$N_CPU"
  done
  b=$(k exec "$p" -- cat /sys/fs/cgroup/cpu.stat | tr '\n' ' ')
  na=$(echo "$a" | sed 's/.*nr_throttled \([0-9]*\).*/\1/'); nb=$(echo "$b" | sed 's/.*nr_throttled \([0-9]*\).*/\1/')
  ta=$(echo "$a" | sed 's/.*throttled_usec \([0-9]*\).*/\1/'); tb=$(echo "$b" | sed 's/.*throttled_usec \([0-9]*\).*/\1/')
  echo "# $p · cpu.stat en las 3 corridas: nr_throttled +$((nb-na)) · throttled_usec +$((tb-ta)) ($(( (tb-ta)/1000 )) ms frenado)"
done
candado_soltar
echo '$ kubectl exec cpu-200m -- cat /sys/fs/cgroup/cpu.max   # cuota y periodo en microsegundos'
k exec cpu-200m -- cat /sys/fs/cgroup/cpu.max
k delete pod cpu-200m cpu-500m cpu-1 --wait=false >/dev/null

titulo "5 · Límite de memoria: OOMKilled"
aplicar $M/5-memoria.yaml
k wait --for=condition=Ready pod/memoria --timeout=120s >/dev/null
echo '$ kubectl exec memoria -- wget -qO- "http://localhost:8080/mem?mb=30"'
k exec memoria -- wget -qO- "http://localhost:8080/mem?mb=30"
echo '$ kubectl exec memoria -- cat /sys/fs/cgroup/memory.max /sys/fs/cgroup/memory.current'
k exec memoria -- cat /sys/fs/cgroup/memory.max /sys/fs/cgroup/memory.current
echo '$ kubectl exec memoria -- wget -qO- "http://localhost:8080/mem?mb=60"   # 30 + 60 > 64 MiB'
k exec memoria -- wget -qO- "http://localhost:8080/mem?mb=60"
sleep 5
echo "\$ kubectl get pod memoria -o jsonpath='{...lastState.terminated.reason} {...exitCode} · reinicios {...restartCount}'"
k get pod memoria -o jsonpath='{.status.containerStatuses[0].lastState.terminated.reason} {.status.containerStatuses[0].lastState.terminated.exitCode} · reinicios {.status.containerStatuses[0].restartCount}'; echo
k delete pod memoria --wait=false >/dev/null

titulo "6 · Clases QoS"
aplicar $M/6-qos.yaml
k wait --for=condition=Ready pod/qos-guaranteed pod/qos-burstable pod/qos-besteffort --timeout=120s >/dev/null
echo '$ kubectl get pods -o custom-columns=POD:.metadata.name,QOS:.status.qosClass ; cat /proc/1/oom_score_adj en cada uno'
for p in qos-guaranteed qos-burstable qos-besteffort; do
  echo "$p $(k get pod $p -o jsonpath='{.status.qosClass}') oom_score_adj=$(k exec $p -- cat /proc/1/oom_score_adj)"
done
k delete pod qos-guaranteed qos-burstable qos-besteffort --wait=false >/dev/null

titulo "7 · HPA con carga real (medido)"
echo '$ kubectl apply -f 0-metrics-server-v0.8.0.yaml   # con --kubelet-insecure-tls para kind'
docker exec -i "$CP" kubectl -n "$NS" apply -f - < $M/0-metrics-server-v0.8.0.yaml 2>&1 | tail -1
k -n kube-system rollout status deployment/metrics-server --timeout=180s >/dev/null
for i in $(seq 1 60); do k top nodes >/dev/null 2>&1 && break; sleep 3; done
x top nodes
aplicar $M/7-hpa.yaml
k rollout status deployment/web --timeout=180s >/dev/null
for i in $(seq 1 60); do u=$(k get hpa web -o jsonpath='{.status.currentMetrics[0].resource.current.averageUtilization}'); [ -n "$u" ] && break; sleep 5; done
x get hpa web
candado_tomar
echo '$ kubectl apply -f 8-carga.yaml   # 4 bucles pidiendo trabajo de CPU'
T0=$(date +%s)
docker exec -i "$CP" kubectl -n "$NS" apply -f - < $M/8-carga.yaml 2>&1
echo "# segundo · réplicas (listas) · uso medio de CPU sobre el request"
primero=""; maximo=0; t_max=""
while [ $(( $(date +%s) - T0 )) -lt 300 ]; do
  rep=$(k get deployment web -o jsonpath='{.status.replicas}'); lis=$(k get deployment web -o jsonpath='{.status.readyReplicas}')
  u=$(k get hpa web -o jsonpath='{.status.currentMetrics[0].resource.current.averageUtilization}')
  t=$(( $(date +%s) - T0 ))
  echo "t=${t}s · réplicas $rep ($lis listas) · CPU ${u}%"
  [ -z "$primero" ] && [ "${rep:-1}" -gt 1 ] && primero=$t
  [ "${rep:-1}" -gt "$maximo" ] && { maximo=$rep; t_max=$t; }
  sleep 15
done
echo "# primera réplica nueva a los ${primero:-?} s · máximo $maximo réplicas, alcanzado a los ${t_max:-?} s"
echo '$ kubectl delete deployment carga   # se acaba la carga'
k delete deployment carga
T1=$(date +%s)
abajo=""
while [ $(( $(date +%s) - T1 )) -lt 720 ]; do
  rep=$(k get deployment web -o jsonpath='{.status.replicas}')
  u=$(k get hpa web -o jsonpath='{.status.currentMetrics[0].resource.current.averageUtilization}')
  t=$(( $(date +%s) - T1 ))
  echo "t=${t}s sin carga · réplicas $rep · CPU ${u}%"
  [ "$rep" = "1" ] && { abajo=$t; break; }
  sleep 10
done
echo "# volvió a 1 réplica ${abajo:-(no en 720)} s después de quitar la carga"
candado_soltar
echo '$ kubectl describe hpa web | grep SuccessfulRescale'
k describe hpa web | grep SuccessfulRescale | sed 's/^ *//'

titulo "8 · Limpiar"
echo '$ kubectl delete namespace curso7'
k delete namespace curso7
pie
} 2>&1 | tee "$SALIDA"
