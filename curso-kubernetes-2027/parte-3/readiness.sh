#!/bin/sh
# Corre DENTRO del nodo k8s-a-control-plane. Mide qué pasa con el tráfico cuando un pod deja de estar Ready.
#  - un bucle hace curl a la ClusterIP sin parar y apunta «ms pod-que-contestó»
#  - otro bucle mira la EndpointSlice del Service y apunta cada cambio de ready
#  - a los 3 s se borra listo.html en el pod elegido; a los 23 s se vuelve a crear
# Uso: sh readiness.sh <ns> <clusterIP> <pod>
ns=$1; ip=$2; pod=$3
export KUBECONFIG=/etc/kubernetes/admin.conf
R=/tmp/k8sa-resp.txt; E=/tmp/k8sa-eps.txt; rm -f $R $E
t0=$(date +%s%3N)
( while [ $(( $(date +%s%3N) - t0 )) -lt 45000 ]; do
    b=$(curl -s -m 2 http://$ip/ || echo ERROR); echo "$(( $(date +%s%3N) - t0 )) $b" >> $R
    sleep 0.02
  done ) &
( prev=""; while [ $(( $(date +%s%3N) - t0 )) -lt 45000 ]; do
    l=$(kubectl get endpointslices -n $ns -l kubernetes.io/service-name=web -o jsonpath='{range .items[*].endpoints[*]}{.targetRef.name}={.conditions.ready} {end}' | tr ' ' '\n' | grep "^$pod=")
    [ "$l" != "$prev" ] && { echo "$(( $(date +%s%3N) - t0 )) $l" >> $E; prev="$l"; }
    sleep 0.1
  done ) &
sleep 3
t_rm=$(( $(date +%s%3N) - t0 )); kubectl exec -n $ns $pod -- rm /usr/share/nginx/html/listo.html
sleep 20
t_ok=$(( $(date +%s%3N) - t0 )); kubectl exec -n $ns $pod -- touch /usr/share/nginx/html/listo.html
wait
echo "rm listo.html en $pod: a los $t_rm ms · touch listo.html: a los $t_ok ms"
echo "EndpointSlice (cambios de ready de $pod):"; sed 's/^/  /' $E
ult=$(awk -v p="$pod" -v a="$t_rm" -v b="$t_ok" '$2==p && $1>a && $1<b {u=$1} END {print u+0}' $R)
pri=$(awk -v p="$pod" -v b="$t_ok" '$2==p && $1>b {print $1; exit}' $R)
echo "última respuesta de $pod tras el rm: $ult ms ($(( ult - t_rm )) ms después del rm)"
echo "primera respuesta de $pod tras el touch: $pri ms ($(( pri - t_ok )) ms después del touch)"
echo "peticiones totales: $(wc -l < $R) · errores: $(grep -c ERROR $R)"
awk -v a="$t_rm" -v b="$t_ok" '$1>a+8000 && $1<b {c[$2]++} END {printf "reparto entre %d y %d ms (pod caído):", a+8000, b; for (p in c) printf " %s=%d", p, c[p]; print ""}' $R
