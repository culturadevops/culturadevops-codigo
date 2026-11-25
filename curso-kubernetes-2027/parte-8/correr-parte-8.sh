#!/usr/bin/env bash
# Parte 8 · Proyecto final: API + Postgres con todo el curso. Escribe SALIDA-parte-8.md.
#   bash correr-parte-8.sh       (clúster k8s-b: bash ../parte-5/cluster-k8s-b.sh up; imagen k8s-b-api:1 cargada)
# Las peticiones de punta a punta salen del nodo control-plane (curl) hacia la ClusterIP del Service del Envoy
# del Gateway (publicado como ClusterIP con un EnvoyProxy), con la cabecera Host: tienda.curso.test.
set -u
cd "$(dirname "$0")"
source ../parte-5/lib-k8s-b.sh
M=manifiestos
SALIDA=SALIDA-parte-8.md
NS=tienda
H="Host: tienda.curso.test"
nodo() { docker exec -i "$CP" bash -c "$1" 2>&1; }

{
encabezado 8 correr-parte-8.sh
k delete namespace tienda --ignore-not-found --wait=true >/dev/null

titulo "1 · Namespace, configuración y base de datos"
aplicar $M/1-namespace.yaml
aplicar $M/2-config.yaml
aplicar $M/3-postgres.yaml
k rollout status statefulset/postgres --timeout=300s >/dev/null
x get pods -l app=postgres -o custom-columns=POD:.metadata.name,LISTO:.status.containerStatuses[0].ready,NODO:.spec.nodeName
x get pvc -o custom-columns=PVC:.metadata.name,ESTADO:.status.phase,TAMANO:.status.capacity.storage,CLASE:.spec.storageClassName
echo '$ kubectl exec postgres-0 -- psql -U postgres -tAc "select version()"'
k exec postgres-0 -- psql -U postgres -tAc "select version()" | cut -c1-40

titulo "2 · RBAC mínimo para la API"
aplicar $M/4-rbac.yaml
SA=system:serviceaccount:tienda:api
for q in "get configmaps" "list configmaps" "get secrets" "list pods" "delete pods" "create deployments"; do
  echo "\$ kubectl auth can-i $q --as=$SA -n tienda"
  k auth can-i $q --as=$SA
done
echo "\$ kubectl auth can-i get configmaps --as=$SA -n default"
k auth can-i get configmaps --as=$SA -n default
echo "\$ kubectl get secrets --as=$SA -n tienda"
k get secrets --as=$SA

titulo "3 · La API: Deployment con probes y recursos, Service y HPA"
echo '$ kubectl apply -f 0-metrics-server-v0.8.0.yaml   # el de la parte 7'
docker exec -i "$CP" kubectl apply -f - < ../parte-7/manifiestos/0-metrics-server-v0.8.0.yaml 2>&1 | tail -1
aplicar $M/5-api.yaml
k rollout status deployment/api --timeout=300s >/dev/null
x get pods -l app=api -o custom-columns=POD:.metadata.name,LISTO:.status.containerStatuses[0].ready,REINICIOS:.status.containerStatuses[0].restartCount,NODO:.spec.nodeName,CUENTA:.spec.serviceAccountName
for i in $(seq 1 40); do u=$(k get hpa api -o jsonpath='{.status.currentMetrics[0].resource.current.averageUtilization}'); [ -n "$u" ] && break; sleep 5; done
x get hpa api
echo '$ kubectl exec deploy/api -- ls /var/run/secrets/kubernetes.io/serviceaccount   # el token de la cuenta api'
k exec deploy/api -- ls /var/run/secrets/kubernetes.io/serviceaccount

titulo "4 · La entrada: Gateway API con Envoy Gateway v1.10.0"
echo '$ kubectl apply --server-side -f envoy-gateway-v1.10.0-install.yaml'
T0=$(ms)
docker exec -i "$CP" kubectl apply --server-side -f - < descargas/envoy-gateway-v1.10.0-install.yaml 2>&1 | wc -l | sed 's/$/ objetos aplicados/'
k -n envoy-gateway-system wait --for=condition=Available deployment/envoy-gateway --timeout=300s >/dev/null
echo "# envoy-gateway disponible $(( $(ms) - T0 )) ms después del apply"
echo "\$ kubectl apply -f $M/6-gateway.yaml"
docker exec -i "$CP" kubectl apply -f - < $M/6-gateway.yaml 2>&1   # sin -n: el EnvoyProxy va en envoy-gateway-system
k wait --for=condition=Programmed gateway/entrada --timeout=300s >/dev/null
for i in $(seq 1 60); do
  [ "$(k -n envoy-gateway-system get pods -l gateway.envoyproxy.io/owning-gateway-name=entrada -o jsonpath='{.items[0].status.containerStatuses[*].ready}')" = "true true" ] && break; sleep 3
done
x get gateway,httproute
GWSVC=$(k -n envoy-gateway-system get svc -l gateway.envoyproxy.io/owning-gateway-name=entrada -o jsonpath='{.items[0].metadata.name}')
GW=$(k get gateway entrada -o jsonpath='{.status.addresses[0].value}')
echo "\$ kubectl get svc -n envoy-gateway-system $GWSVC"
k -n envoy-gateway-system get svc "$GWSVC" -o custom-columns=SERVICIO:.metadata.name,TIPO:.spec.type,CLUSTER-IP:.spec.clusterIP
echo "# el Envoy se publica como ClusterIP (EnvoyProxy en 6-gateway.yaml): las pruebas salen del nodo control-plane hacia $GW"
APISVC=$(k get svc api -o jsonpath='{.spec.clusterIP}')
ENVOY=$(k -n envoy-gateway-system get pods -l gateway.envoyproxy.io/owning-gateway-name=entrada -o jsonpath='{.items[0].metadata.name}')
# contadores del Envoy (admin en 127.0.0.1:19000 del pod, vía port-forward dentro del nodo)
panico() { nodo "kubectl -n envoy-gateway-system port-forward pod/$ENVOY 19001:19000 >/dev/null 2>&1 & p=\$!; sleep 2; curl -s localhost:19001/stats | grep -E 'tienda/api.*(lb_healthy_panic|membership_healthy|membership_total):'; kill \$p"; }
for i in $(seq 1 60); do [ "$(nodo "curl -s -o /dev/null -w '%{http_code}' -H '$H' http://$GW/")" = "200" ] && break; sleep 2; done

titulo "5 · Prueba de punta a punta"
echo "\$ curl -H '$H' http://$GW/"
nodo "curl -s -H '$H' http://$GW/"; echo
for n in teclado raton monitor; do
  echo "\$ curl -X POST -H '$H' 'http://$GW/items?nombre=$n'"
  nodo "curl -s -X POST -H '$H' 'http://$GW/items?nombre=$n'"
done
echo "\$ curl -H '$H' http://$GW/items"
nodo "curl -s -H '$H' http://$GW/items"; echo
echo "\$ for i in \$(seq 20); do curl -s -H '$H' http://$GW/; done | contar pods   # reparte entre las 2 réplicas"
nodo "for i in \$(seq 20); do curl -s -H '$H' http://$GW/; echo; done" | grep -o '"pod":"[^"]*"' | sort | uniq -c
echo '$ curl -s -o /dev/null -w "%{http_code}" -H "Host: otra.cosa.test" http://'"$GW"'/   # un host que el HTTPRoute no conoce'
nodo "curl -s -o /dev/null -w '%{http_code}' -H 'Host: otra.cosa.test' http://$GW/"; echo

titulo "6 · Fallo provocado 1: matar un pod de la API con tráfico"
candado_tomar
nodo "rm -f /tmp/f1.txt; (for i in \$(seq 1 300); do echo \"\$(date +%s%3N) \$(curl -s -o /dev/null -m 2 -w '%{http_code}' -H '$H' http://$GW/items)\" >> /tmp/f1.txt; sleep 0.1; done) >/dev/null 2>&1 &"
sleep 5
VICTIMA=$(k get pods -l app=api -o jsonpath='{.items[0].metadata.name}')
echo "\$ kubectl delete pod $VICTIMA   # con peticiones cada 0,1 s por el Gateway"
k delete pod "$VICTIMA" --wait=false
for i in $(seq 1 120); do [ "$(nodo 'wc -l < /tmp/f1.txt')" -ge 300 ] && break; sleep 1; done
echo "# peticiones por código HTTP:"
nodo "awk '{print \$2}' /tmp/f1.txt | sort | uniq -c"
nodo "awk 'NR==1{a=\$1} {b=\$1} END{printf \"# duración de la prueba: %.1f s\\n\", (b-a)/1000}' /tmp/f1.txt"
k rollout status deployment/api --timeout=180s >/dev/null
x get pods -l app=api -o custom-columns=POD:.metadata.name,LISTO:.status.containerStatuses[0].ready,REINICIOS:.status.containerStatuses[0].restartCount

titulo "7 · Fallo provocado 2: tirar la base de datos"
ANTES=$(nodo "curl -s -H '$H' http://$GW/items" | grep -o '"id"' | wc -l)
echo "# items antes: $ANTES"
nodo "rm -f /tmp/f2.txt; (for i in \$(seq 1 600); do echo \"\$(date +%s%3N) \$(curl -s -o /dev/null -m 2 -w '%{http_code}' -H '$H' http://$GW/items)\" >> /tmp/f2.txt; sleep 0.2; done) >/dev/null 2>&1 &"
sleep 5
T_BD=$(ms)
echo '$ kubectl delete pod postgres-0'
k delete pod postgres-0 --wait=false
for i in $(seq 1 200); do [ "$(nodo 'wc -l < /tmp/f2.txt')" -ge 600 ] && break; sleep 1; done
echo "# peticiones por código HTTP:"
nodo "awk '{print \$2}' /tmp/f2.txt | sort | uniq -c"
nodo "awk -v t=$T_BD '\$2!=\"200\"{if(!p)p=\$1; u=\$1; n++} END{if(n) printf \"# primer fallo %.1f s después del delete · último fallo %.1f s después · %d peticiones fallidas\\n\", (p-t)/1000, (u-t)/1000, n; else print \"# ningún fallo\"}' /tmp/f2.txt"
nodo "awk -v t=$T_BD '{c=\$2; if(c!=prev){printf \"  t=%+.1f s → %s\\n\", (\$1-t)/1000, c; prev=c}}' /tmp/f2.txt"
k rollout status statefulset/postgres --timeout=300s >/dev/null
sleep 5

titulo "7b · Fallo provocado 3: la base de datos caída 30 s"
echo '# Envoy antes de la caída:'
panico
nodo "rm -f /tmp/f3.txt; (for i in \$(seq 1 450); do echo \"\$(date +%s%3N) \$(curl -s -o /dev/null -m 2 -w '%{http_code}' -H '$H' http://$GW/items)\" >> /tmp/f3.txt; sleep 0.2; done) >/dev/null 2>&1 &"
sleep 5
T_BD=$(ms)
echo '$ kubectl scale statefulset postgres --replicas=0 ; sleep 30 ; kubectl scale statefulset postgres --replicas=1'
k scale statefulset postgres --replicas=0
sleep 12
echo '$ kubectl get pods -l app=api   # 12 s sin base de datos'
k get pods -l app=api -o custom-columns=POD:.metadata.name,LISTO:.status.containerStatuses[0].ready,REINICIOS:.status.containerStatuses[0].restartCount
echo '$ kubectl get endpointslice -l kubernetes.io/service-name=api'
k get endpointslice -l kubernetes.io/service-name=api -o jsonpath='{range .items[*].endpoints[*]}{.targetRef.name} ready={.conditions.ready}{"\n"}{end}'
echo "\$ curl -s -H '$H' http://$GW/items   # por el Gateway"
nodo "curl -s -w ' · HTTP %{http_code}' -H '$H' http://$GW/items"; echo
echo "\$ curl -s -m 2 http://$APISVC/items   # directo al Service api (ClusterIP), sin el Gateway"
nodo "curl -s -m 2 -o /dev/null -w 'HTTP %{http_code} · exit ' http://$APISVC/items; echo \$?"
echo '# Envoy: contadores del clúster del HTTPRoute (lb_healthy_panic = peticiones repartidas en modo pánico)'
panico
sleep 14
T_UP=$(ms)
k scale statefulset postgres --replicas=1
for i in $(seq 1 200); do [ "$(nodo 'wc -l < /tmp/f3.txt')" -ge 450 ] && break; sleep 1; done
echo "# peticiones por código HTTP:"
nodo "awk '{print \$2}' /tmp/f3.txt | sort | uniq -c"
echo "# cambios de código (t=0: scale a 0 · la BD vuelve a pedirse en t=+$(( (T_UP-T_BD)/1000 )) s):"
nodo "awk -v t=$T_BD '{c=\$2; if(c!=prev){printf \"  t=%+.1f s → %s\n\", (\$1-t)/1000, c; prev=c}}' /tmp/f3.txt"
candado_soltar
k rollout status statefulset/postgres --timeout=300s >/dev/null
k rollout status deployment/api --timeout=300s >/dev/null
echo '$ kubectl get pods   # la API no se reinició: la liveness solo mira el proceso'
k get pods -o custom-columns=POD:.metadata.name,LISTO:.status.containerStatuses[0].ready,REINICIOS:.status.containerStatuses[0].restartCount | grep -E "POD|api|postgres"
echo "\$ curl -H '$H' http://$GW/items   # los datos siguen: estaban en el PVC"
nodo "curl -s -H '$H' http://$GW/items"; echo
DESPUES=$(nodo "curl -s -H '$H' http://$GW/items" | grep -o '"id"' | wc -l)
echo "# items antes: $ANTES · después: $DESPUES"

titulo "8 · Todo junto"
echo '$ kubectl get deploy,statefulset,svc,hpa,gateway,httproute,pvc,sa -n tienda'
k get deploy,statefulset,svc,hpa,pvc,serviceaccount -o name | grep -v "serviceaccount/default"
k get gateway,httproute -o name

titulo "9 · Limpiar"
echo '$ kubectl delete namespace tienda'
k delete namespace tienda
docker exec -i "$CP" kubectl delete -f - --wait=true < $M/6-gateway.yaml >/dev/null 2>&1
pie
} 2>&1 | tee "$SALIDA"
