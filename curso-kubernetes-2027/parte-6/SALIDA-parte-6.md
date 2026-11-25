# SALIDA de la parte 6 · Curso de Kubernetes 2027 (cultura-devops)

Generado: 2026-11-22 23:58:36 UTC · script: correr-parte-6.sh
Clúster: kind v0.30.0 · servidor v1.34.0 · nodos: 3
Contenedores de Docker vivos al empezar (ajenos a k8s-b): k8s-a-control-plane k8s-a-worker2 k8s-a-worker

```

### 1 · StatefulSet: nombres estables y arranque en orden
$ kubectl apply -f manifiestos/1-statefulset.yaml
Warning: spec.SessionAffinity is ignored for headless services
service/web created
statefulset.apps/web created
$ kubectl get pods -l app=web   # con la hora en que se creó y en que quedó listo cada uno
POD     NODO            CREADO                 LISTO
web-0   k8s-b-worker    2026-11-22T23:58:37Z   2026-11-22T23:58:46Z
web-1   k8s-b-worker2   2026-11-22T23:58:46Z   2026-11-22T23:58:55Z
web-2   k8s-b-worker    2026-11-22T23:58:55Z   2026-11-22T23:59:05Z
# web-0 listo a los 9 s · web-1 creado 0 s después de que web-0 quedara listo · web-2 creado 0 s después de web-1 listo
# de web-0 creado a web-2 creado: 18 s

### 2 · Un PVC por réplica
$ kubectl get pvc -o custom-columns=PVC:.metadata.name,ESTADO:.status.phase,TAMANO:.status.capacity.storage
PVC           ESTADO   TAMANO
datos-web-0   Bound    100Mi
datos-web-1   Bound    100Mi
datos-web-2   Bound    100Mi
$ kubectl exec web-0 -- cat /datos/index.html
soy web-0, naci a las 23:58:41
$ kubectl exec web-1 -- cat /datos/index.html
soy web-1, naci a las 23:58:50
$ kubectl exec web-2 -- cat /datos/index.html
soy web-2, naci a las 23:58:59

### 3 · DNS por pod con el Service headless
$ kubectl get service web -o custom-columns=NOMBRE:.metadata.name,CLUSTER-IP:.spec.clusterIP
NOMBRE   CLUSTER-IP
web      None
$ kubectl exec dns -- nslookup web.curso6.svc.cluster.local   # el headless devuelve las IP de los pods
Name:	web.curso6.svc.cluster.local
Address: 10.244.1.12
Name:	web.curso6.svc.cluster.local
Address: 10.244.2.8
Name:	web.curso6.svc.cluster.local
Address: 10.244.2.6
$ kubectl exec dns -- nslookup web-1.web.curso6.svc.cluster.local
Name:	web-1.web.curso6.svc.cluster.local
Address: 10.244.1.12
$ kubectl exec dns -- wget -qO- http://web-1.web
soy web-1, naci a las 23:58:50

### 4 · Borrar web-1: vuelve con el mismo nombre y el mismo disco
$ kubectl delete pod web-1
pod "web-1" deleted from curso6 namespace
$ kubectl get pod web-1 -o custom-columns=POD:.metadata.name,IP:.status.podIP,UID:.metadata.uid
POD     IP            UID
web-1   10.244.1.13   a0664173-d649-4ca0-bd06-dddf9a5230f1
# antes: IP 10.244.1.12 · UID c0703acb-2e35-4cc0-abbf-48f17d8c6d04
$ kubectl exec dns -- wget -qO- http://web-1.web   # mismo PVC: conserva la hora en que nació la primera vez
soy web-1, naci a las 23:58:50

### 5 · Escalar: baja en orden inverso y los PVC se quedan
$ kubectl scale statefulset web --replicas=1
statefulset.apps/web scaled
# quedó 1 pod en 62 s
  MENSAJE
  delete Pod web-2 in StatefulSet web successful
  delete Pod web-1 in StatefulSet web successful
$ kubectl get pods -l app=web -o custom-columns=POD:.metadata.name
POD
web-0
$ kubectl get pvc -o custom-columns=PVC:.metadata.name,ESTADO:.status.phase
PVC           ESTADO
datos-web-0   Bound
datos-web-1   Bound
datos-web-2   Bound
$ kubectl scale statefulset web --replicas=3
statefulset.apps/web scaled
$ kubectl exec dns -- wget -qO- http://web-2.web   # web-2 vuelve a su PVC de antes
soy web-2, naci a las 23:58:59

### 6 · Comparar con un Deployment
$ kubectl apply -f manifiestos/2-deployment-comparar.yaml
deployment.apps/web-deploy created
$ kubectl get pods -l app=web-deploy -o custom-columns=POD:.metadata.name
POD
web-deploy-6c66cbb6df-44hrn
web-deploy-6c66cbb6df-k2vcg
web-deploy-6c66cbb6df-zqj87

### 7 · DaemonSet: uno por nodo
$ kubectl apply -f manifiestos/3-daemonset.yaml
daemonset.apps/agente-nodo created
$ kubectl get daemonset agente-nodo -o custom-columns=NOMBRE:.metadata.name,DESEADOS:.status.desiredNumberScheduled,LISTOS:.status.numberReady
NOMBRE        DESEADOS   LISTOS
agente-nodo   2          2
$ kubectl get pods -l app=agente-nodo -o custom-columns=POD:.metadata.name,NODO:.spec.nodeName
POD                 NODO
agente-nodo-mcvhn   k8s-b-worker
agente-nodo-sp8dz   k8s-b-worker2
$ kubectl get node k8s-b-control-plane -o jsonpath='{.spec.taints[*].key}'
node-role.kubernetes.io/control-plane
$ kubectl apply -f manifiestos/4-daemonset-tolera.yaml
daemonset.apps/agente-nodo configured
$ kubectl get pods -l app=agente-nodo -o custom-columns=POD:.metadata.name,NODO:.spec.nodeName
POD                 NODO
agente-nodo-gdtn4   k8s-b-worker
agente-nodo-qznjd   k8s-b-worker2
agente-nodo-w9rs5   k8s-b-control-plane
$ kubectl logs agente-nodo-gdtn4
vigilo el nodo k8s-b-worker

### 8 · Job: completions y parallelism
$ kubectl apply -f manifiestos/5-job.yaml
job.batch/lote created
$ kubectl get job lote -o custom-columns=JOB:.metadata.name,COMPLETADOS:.status.succeeded,INICIO:.status.startTime,FIN:.status.completionTime
JOB    COMPLETADOS   INICIO                 FIN
lote   6             2026-11-23T00:02:13Z   2026-11-23T00:02:36Z
# 6 tareas de 5 s, de 2 en 2: el Job tardó 23 s
$ kubectl get pods -l job-name=lote   # de dos en dos
POD          CREADO                 ESTADO
lote-jzq27   2026-11-23T00:02:13Z   Succeeded
lote-mjsbs   2026-11-23T00:02:13Z   Succeeded
lote-8mt5v   2026-11-23T00:02:20Z   Succeeded
lote-flm4c   2026-11-23T00:02:20Z   Succeeded
lote-67zw5   2026-11-23T00:02:28Z   Succeeded
lote-hb77m   2026-11-23T00:02:28Z   Succeeded

### 9 · Job que falla: backoffLimit
$ kubectl apply -f manifiestos/6-job-falla.yaml
job.batch/roto created
$ kubectl get job roto -o custom-columns=JOB:.metadata.name,FALLIDOS:.status.failed,COMPLETADOS:.status.succeeded
JOB    FALLIDOS   COMPLETADOS
roto   3          <none>
$ kubectl get job roto -o jsonpath='{.status.conditions[?(@.type=="Failed")].reason}'
BackoffLimitExceeded
$ kubectl get pods -l job-name=roto   # 1 intento + 2 reintentos, cada vez con más espera
POD          CREADO                 ESTADO
roto-4xgr5   2026-11-23T00:02:37Z   Failed
roto-l7bd2   2026-11-23T00:02:48Z   Failed
roto-hlz6d   2026-11-23T00:03:09Z   Failed
# entre intentos: 11 s
# entre intentos: 21 s
$ kubectl logs roto-4xgr5
no encuentro el archivo de entrada

### 10 · CronJob: concurrencyPolicy e historial
$ kubectl apply -f manifiestos/7-cronjobs.yaml
cronjob.batch/rapido created
cronjob.batch/lento-forbid created
cronjob.batch/lento-allow created
# espero 5 minutos y 10 segundos
$ kubectl get cronjobs
CRONJOB        HORARIO     CONCURRENCIA   ACTIVOS
lento-allow    * * * * *   Allow          lento-allow-29923207
lento-forbid   * * * * *   Forbid         lento-forbid-29923207
rapido         * * * * *   Allow          <none>
$ kubectl get jobs   # cuántos Job creó cada CronJob y cuántos siguen corriendo
rapido: jobs guardados 2 · corriendo ahora 0
lento-forbid: jobs guardados 3 · corriendo ahora 1
lento-allow: jobs guardados 5 · corriendo ahora 2
$ kubectl get jobs -o custom-columns=JOB:.metadata.name,INICIO:.status.startTime,FIN:.status.completionTime
JOB                     INICIO                 FIN
lote                    2026-11-23T00:02:13Z   2026-11-23T00:02:36Z
roto                    2026-11-23T00:02:37Z   <none>
lento-allow-29923204    2026-11-23T00:04:00Z   2026-11-23T00:05:32Z
lento-forbid-29923204   2026-11-23T00:04:00Z   2026-11-23T00:05:33Z
lento-allow-29923205    2026-11-23T00:05:00Z   2026-11-23T00:06:33Z
lento-forbid-29923205   2026-11-23T00:05:33Z   2026-11-23T00:07:06Z
lento-allow-29923206    2026-11-23T00:06:00Z   2026-11-23T00:07:33Z
lento-allow-29923207    2026-11-23T00:07:00Z   <none>
rapido-29923207         2026-11-23T00:07:00Z   2026-11-23T00:07:05Z
lento-forbid-29923207   2026-11-23T00:07:06Z   <none>
lento-allow-29923208    2026-11-23T00:08:00Z   <none>
rapido-29923208         2026-11-23T00:08:00Z   2026-11-23T00:08:05Z
$ kubectl get pods -l batch.kubernetes.io/controller-uid --field-selector=status.phase=Running   # lento-allow apila
POD
lento-allow-29923207-25hlx
lento-allow-29923208-qt8br
lento-forbid-29923207-z6zmq

### 11 · Limpiar
$ kubectl delete namespace curso6
namespace "curso6" deleted
```
