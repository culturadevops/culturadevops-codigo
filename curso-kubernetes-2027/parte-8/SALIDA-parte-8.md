# SALIDA de la parte 8 · Curso de Kubernetes 2027 (cultura-devops)

Generado: 2026-11-23 00:47:28 UTC · script: correr-parte-8.sh
Clúster: kind v0.30.0 · servidor v1.34.0 · nodos: 3
Contenedores de Docker vivos al empezar (ajenos a k8s-b): 
(ninguno)

```

### 1 · Namespace, configuración y base de datos
$ kubectl apply -f manifiestos/1-namespace.yaml
namespace/tienda created
$ kubectl apply -f manifiestos/2-config.yaml
secret/postgres-cred created
configmap/api-config created
$ kubectl apply -f manifiestos/3-postgres.yaml
Warning: spec.SessionAffinity is ignored for headless services
service/postgres created
statefulset.apps/postgres created
$ kubectl get pods -l app=postgres -o custom-columns=POD:.metadata.name,LISTO:.status.containerStatuses[0].ready,NODO:.spec.nodeName
POD          LISTO   NODO
postgres-0   true    k8s-b-worker
$ kubectl get pvc -o custom-columns=PVC:.metadata.name,ESTADO:.status.phase,TAMANO:.status.capacity.storage,CLASE:.spec.storageClassName
PVC                ESTADO   TAMANO   CLASE
datos-postgres-0   Bound    1Gi      standard
$ kubectl exec postgres-0 -- psql -U postgres -tAc "select version()"
PostgreSQL 18.6 on x86_64-pc-linux-musl,

### 2 · RBAC mínimo para la API
$ kubectl apply -f manifiestos/4-rbac.yaml
serviceaccount/api created
role.rbac.authorization.k8s.io/leer-config created
rolebinding.rbac.authorization.k8s.io/api-leer-config created
$ kubectl auth can-i get configmaps --as=system:serviceaccount:tienda:api -n tienda
yes
$ kubectl auth can-i list configmaps --as=system:serviceaccount:tienda:api -n tienda
yes
$ kubectl auth can-i get secrets --as=system:serviceaccount:tienda:api -n tienda
no
$ kubectl auth can-i list pods --as=system:serviceaccount:tienda:api -n tienda
no
$ kubectl auth can-i delete pods --as=system:serviceaccount:tienda:api -n tienda
no
$ kubectl auth can-i create deployments --as=system:serviceaccount:tienda:api -n tienda
no
$ kubectl auth can-i get configmaps --as=system:serviceaccount:tienda:api -n default
no
$ kubectl get secrets --as=system:serviceaccount:tienda:api -n tienda
Error from server (Forbidden): secrets is forbidden: User "system:serviceaccount:tienda:api" cannot list resource "secrets" in API group "" in the namespace "tienda"

### 3 · La API: Deployment con probes y recursos, Service y HPA
$ kubectl apply -f 0-metrics-server-v0.8.0.yaml   # el de la parte 7
apiservice.apiregistration.k8s.io/v1beta1.metrics.k8s.io unchanged
$ kubectl apply -f manifiestos/5-api.yaml
deployment.apps/api created
service/api created
horizontalpodautoscaler.autoscaling/api created
$ kubectl get pods -l app=api -o custom-columns=POD:.metadata.name,LISTO:.status.containerStatuses[0].ready,REINICIOS:.status.containerStatuses[0].restartCount,NODO:.spec.nodeName,CUENTA:.spec.serviceAccountName
POD                    LISTO   REINICIOS   NODO            CUENTA
api-7c8db96d8c-g5dcn   true    0           k8s-b-worker    api
api-7c8db96d8c-hxd4s   true    0           k8s-b-worker2   api
$ kubectl get hpa api
NAME   REFERENCE        TARGETS       MINPODS   MAXPODS   REPLICAS   AGE
api    Deployment/api   cpu: 1%/70%   2         5         2          35s
$ kubectl exec deploy/api -- ls /var/run/secrets/kubernetes.io/serviceaccount   # el token de la cuenta api
ca.crt
namespace
token

### 4 · La entrada: Gateway API con Envoy Gateway v1.10.0
$ kubectl apply --server-side -f envoy-gateway-v1.10.0-install.yaml
43 objetos aplicados
# envoy-gateway disponible 4482 ms después del apply
$ kubectl apply -f manifiestos/6-gateway.yaml
envoyproxy.gateway.envoyproxy.io/clusterip created
gatewayclass.gateway.networking.k8s.io/envoy-tienda created
gateway.gateway.networking.k8s.io/entrada created
httproute.gateway.networking.k8s.io/api created
$ kubectl get gateway,httproute
NAME                                        CLASS          ADDRESS        PROGRAMMED   AGE
gateway.gateway.networking.k8s.io/entrada   envoy-tienda   10.96.193.78   True         12s

NAME                                      HOSTNAMES               AGE
httproute.gateway.networking.k8s.io/api   ["tienda.curso.test"]   12s
$ kubectl get svc -n envoy-gateway-system envoy-tienda-entrada-18fae084
SERVICIO                        TIPO        CLUSTER-IP
envoy-tienda-entrada-18fae084   ClusterIP   10.96.193.78
# el Envoy se publica como ClusterIP (EnvoyProxy en 6-gateway.yaml): las pruebas salen del nodo control-plane hacia 10.96.193.78

### 5 · Prueba de punta a punta
$ curl -H 'Host: tienda.curso.test' http://10.96.193.78/
{"mensaje":"tienda del curso, parte 8","pod":"api-7c8db96d8c-g5dcn","version":"1"}

$ curl -X POST -H 'Host: tienda.curso.test' 'http://10.96.193.78/items?nombre=teclado'
{"id":1,"pod":"api-7c8db96d8c-g5dcn"}
$ curl -X POST -H 'Host: tienda.curso.test' 'http://10.96.193.78/items?nombre=raton'
{"id":2,"pod":"api-7c8db96d8c-g5dcn"}
$ curl -X POST -H 'Host: tienda.curso.test' 'http://10.96.193.78/items?nombre=monitor'
{"id":3,"pod":"api-7c8db96d8c-g5dcn"}
$ curl -H 'Host: tienda.curso.test' http://10.96.193.78/items
{"items":[{"id":1,"nombre":"teclado"},{"id":2,"nombre":"raton"},{"id":3,"nombre":"monitor"}],"pod":"api-7c8db96d8c-hxd4s"}

$ for i in $(seq 20); do curl -s -H 'Host: tienda.curso.test' http://10.96.193.78/; done | contar pods   # reparte entre las 2 réplicas
      7 "pod":"api-7c8db96d8c-g5dcn"
     13 "pod":"api-7c8db96d8c-hxd4s"
$ curl -s -o /dev/null -w "%{http_code}" -H "Host: otra.cosa.test" http://10.96.193.78/   # un host que el HTTPRoute no conoce
404

### 6 · Fallo provocado 1: matar un pod de la API con tráfico
# candado banco.lock tomado 00:48:33 UTC tras esperar 0 s · contenedores ajenos vivos: 
$ kubectl delete pod api-7c8db96d8c-g5dcn   # con peticiones cada 0,1 s por el Gateway
pod "api-7c8db96d8c-g5dcn" deleted from tienda namespace
# peticiones por código HTTP:
    300 200
# duración de la prueba: 31.9 s
$ kubectl get pods -l app=api -o custom-columns=POD:.metadata.name,LISTO:.status.containerStatuses[0].ready,REINICIOS:.status.containerStatuses[0].restartCount
POD                    LISTO   REINICIOS
api-7c8db96d8c-gjlt5   true    0
api-7c8db96d8c-hxd4s   true    0

### 7 · Fallo provocado 2: tirar la base de datos
# items antes: 3
$ kubectl delete pod postgres-0
pod "postgres-0" deleted from tienda namespace
# peticiones por código HTTP:
    593 200
      7 500
# primer fallo 0.2 s después del delete · último fallo 1.5 s después · 7 peticiones fallidas
  t=-5.2 s → 200
  t=+0.2 s → 500
  t=+1.7 s → 200

### 7b · Fallo provocado 3: la base de datos caída 30 s
# Envoy antes de la caída:
cluster.httproute/tienda/api/rule/0.lb_healthy_panic: 0
cluster.httproute/tienda/api/rule/0.membership_healthy: 2
cluster.httproute/tienda/api/rule/0.membership_total: 2
$ kubectl scale statefulset postgres --replicas=0 ; sleep 30 ; kubectl scale statefulset postgres --replicas=1
statefulset.apps/postgres scaled
$ kubectl get pods -l app=api   # 12 s sin base de datos
POD                    LISTO   REINICIOS
api-7c8db96d8c-gjlt5   false   0
api-7c8db96d8c-hxd4s   false   0
$ kubectl get endpointslice -l kubernetes.io/service-name=api
api-7c8db96d8c-hxd4s ready=false
api-7c8db96d8c-gjlt5 ready=false
$ curl -s -H 'Host: tienda.curso.test' http://10.96.193.78/items   # por el Gateway
failed to connect to `user=postgres database=postgres`: hostname resolving error: lookup postgres-0.postgres on 10.96.0.10:53: no such host
 · HTTP 500
$ curl -s -m 2 http://10.96.50.23/items   # directo al Service api (ClusterIP), sin el Gateway
HTTP 000 · exit 7
# Envoy: contadores del clúster del HTTPRoute (lb_healthy_panic = peticiones repartidas en modo pánico)
cluster.httproute/tienda/api/rule/0.lb_healthy_panic: 54
cluster.httproute/tienda/api/rule/0.membership_healthy: 0
cluster.httproute/tienda/api/rule/0.membership_total: 2
statefulset.apps/postgres scaled
# peticiones por código HTTP:
    307 200
    143 500
# cambios de código (t=0: scale a 0 · la BD vuelve a pedirse en t=+29 s):
  t=-5.2 s → 200
  t=+0.2 s → 500
  t=+30.4 s → 200
# candado banco.lock soltado 00:52:54 UTC
$ kubectl get pods   # la API no se reinició: la liveness solo mira el proceso
POD                    LISTO   REINICIOS
api-7c8db96d8c-gjlt5   true    0
api-7c8db96d8c-hxd4s   true    0
postgres-0             true    0
$ curl -H 'Host: tienda.curso.test' http://10.96.193.78/items   # los datos siguen: estaban en el PVC
{"items":[{"id":1,"nombre":"teclado"},{"id":2,"nombre":"raton"},{"id":3,"nombre":"monitor"}],"pod":"api-7c8db96d8c-gjlt5"}

# items antes: 3 · después: 3

### 8 · Todo junto
$ kubectl get deploy,statefulset,svc,hpa,gateway,httproute,pvc,sa -n tienda
deployment.apps/api
statefulset.apps/postgres
service/api
service/postgres
horizontalpodautoscaler.autoscaling/api
persistentvolumeclaim/datos-postgres-0
serviceaccount/api
gateway.gateway.networking.k8s.io/entrada
httproute.gateway.networking.k8s.io/api

### 9 · Limpiar
$ kubectl delete namespace tienda
Warning: deleting cluster-scoped resources, not scoped to the provided namespace
namespace "tienda" deleted
```
