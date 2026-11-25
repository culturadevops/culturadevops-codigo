# SALIDA — Curso de Kubernetes 2027 · Parte 2: ReplicaSet y Deployment

> Corrida del 2026-11-22 19:04. kind v0.30.0, clúster k8s-a (1 plano de control + 2 workers), kindest/node:v1.34.0.
> Imágenes ya descargadas en los nodos. Contenedores ajenos vivos al empezar: k8s-b-control-plane k8s-b-worker k8s-b-worker2 

```

### 1 · ReplicaSet: etiquetas y selector
$ kubectl apply -f 1-replicaset.yaml
replicaset.apps/web-rs created
$ kubectl get rs web-rs
NAME     DESIRED   CURRENT   READY   AGE
web-rs   3         3         3       1s
$ kubectl get pods --show-labels
NAME           READY   STATUS    RESTARTS   AGE   LABELS
web-rs-rzmzg   1/1     Running   0          2s    app=web-rs
web-rs-tzk49   1/1     Running   0          2s    app=web-rs
web-rs-wtqf6   1/1     Running   0          2s    app=web-rs
$ kubectl get pods -l app=web-rs -o name
pod/web-rs-rzmzg
pod/web-rs-tzk49
pod/web-rs-wtqf6

### 2 · Borro un pod: el ReplicaSet crea otro
$ kubectl delete pod web-rs-rzmzg --wait=false
pod "web-rs-rzmzg" deleted from parte2 namespace
(3 pods listos otra vez 1080 ms después del delete, medido desde la máquina)
$ kubectl get pods -l app=web-rs
NAME           READY   STATUS    RESTARTS   AGE
web-rs-nzj85   1/1     Running   0          1s
web-rs-tzk49   1/1     Running   0          3s
web-rs-wtqf6   1/1     Running   0          3s

### 3 · Le cambio la etiqueta a un pod: deja de contar
$ kubectl label pod web-rs-nzj85 app=fuera --overwrite
pod/web-rs-nzj85 labeled
$ kubectl get pods -L app
NAME           READY   STATUS    RESTARTS   AGE   APP
web-rs-j285v   1/1     Running   0          4s    web-rs
web-rs-nzj85   1/1     Running   0          6s    fuera
web-rs-tzk49   1/1     Running   0          8s    web-rs
web-rs-wtqf6   1/1     Running   0          8s    web-rs
$ kubectl get pod web-rs-nzj85 -o jsonpath='{.metadata.ownerReferences}'   # ¿de quién es?
(vacío: ya no es de nadie)

### 4 · Un pod suelto con la misma etiqueta: el ReplicaSet lo adopta y sobra uno
$ kubectl apply -f 2-intruso.yaml
pod/intruso created
$ kubectl get pods -l app=web-rs
NAME           READY   STATUS    RESTARTS   AGE
web-rs-j285v   1/1     Running   0          9s
web-rs-tzk49   1/1     Running   0          13s
web-rs-wtqf6   1/1     Running   0          13s
$ kubectl get events --field-selector reason=SuccessfulDelete -o custom-columns=MOTIVO:.reason,MENSAJE:.message
SuccessfulDelete   Deleted pod: intruso

### 5 · El ReplicaSet NO actualiza los pods que ya existen
$ kubectl set image rs/web-rs nginx=nginx:1.30.6-alpine
replicaset.apps/web-rs image updated
$ kubectl get pods -l app=web-rs -o custom-columns=POD:.metadata.name,IMAGEN:.spec.containers[0].image
POD            IMAGEN
web-rs-j285v   nginx:1.29.8-alpine
web-rs-tzk49   nginx:1.29.8-alpine
web-rs-wtqf6   nginx:1.29.8-alpine
$ kubectl delete pod web-rs-j285v
POD            IMAGEN
web-rs-tzk49   nginx:1.29.8-alpine
web-rs-vdj2f   nginx:1.30.6-alpine
web-rs-wtqf6   nginx:1.29.8-alpine

### 6 · Deployment → ReplicaSet → pods
$ kubectl apply -f 3-deployment.yaml
deployment.apps/web created
service/web created
pod/cliente created
$ kubectl get deployment,rs,pods -l app=web
NAME   READY   UP-TO-DATE   AVAILABLE   AGE
web    4/4     4            4           4s
NAME            DESIRED   CURRENT   READY   AGE
web-6c85658fb   4         4         4       4s
NAME                  READY   STATUS    RESTARTS   AGE
web-6c85658fb-48x44   1/1     Running   0          4s
web-6c85658fb-57s6b   1/1     Running   0          4s
web-6c85658fb-64ffb   1/1     Running   0          4s
web-6c85658fb-jvghc   1/1     Running   0          4s
$ kubectl get pod web-6c85658fb-48x44 -o jsonpath='{.metadata.ownerReferences[0].kind}/{.metadata.ownerReferences[0].name}'
ReplicaSet/web-6c85658fb
$ kubectl get deployment web -o jsonpath='{.spec.strategy}'   # la estrategia por defecto
{"rollingUpdate":{"maxSurge":"25%","maxUnavailable":"25%"},"type":"RollingUpdate"}
$ kubectl logs cliente --tail=3   # el cliente ya está pidiendo
1795392324 nginx/1.29.8
1795392324 nginx/1.29.8
1795392324 nginx/1.29.8
línea base, 30 s sin tocar nada → peticiones: 1285 · nginx/1.29.8: 1285

### 7 · Rollout A: por defecto (maxSurge 25 %, maxUnavailable 25 %) · 4 réplicas · 1.29.8 → 1.30.6
$ kubectl set image deployment/web nginx=nginx:1.30.6-alpine
     1 ms  viejos 4 listos + 0 no · nuevos 0 listos + 0 no · terminando 0
   566 ms  viejos 3 listos + 0 no · nuevos 0 listos + 2 no · terminando 1
   850 ms  viejos 3 listos + 0 no · nuevos 0 listos + 2 no · terminando 0
  3678 ms  viejos 2 listos + 0 no · nuevos 1 listos + 2 no · terminando 1
  3963 ms  viejos 1 listos + 0 no · nuevos 2 listos + 2 no · terminando 2
  4817 ms  viejos 1 listos + 0 no · nuevos 2 listos + 2 no · terminando 0
  6801 ms  viejos 0 listos + 0 no · nuevos 4 listos + 0 no · terminando 1
  7646 ms  viejos 0 listos + 0 no · nuevos 4 listos + 0 no · terminando 0
RESUMEN: completo en 7646 ms · máximo de pods a la vez: 7 · mínimo de pods listos: 3
tráfico durante el rollout → peticiones: 365 · nginx/1.30.6: 165 · ERROR-rechazada: 5 · nginx/1.29.8: 194 · ERROR-tiempo: 1

### 8 · Rollout B: maxSurge 1, maxUnavailable 0 · 1.30.6 → 1.29.8
$ kubectl patch deployment web -p '{"spec":{"strategy":{"rollingUpdate":{"maxSurge":1,"maxUnavailable":0}}}}'
deployment.apps/web patched
$ kubectl set image deployment/web nginx=nginx:1.29.8-alpine
     0 ms  viejos 4 listos + 0 no · nuevos 0 listos + 0 no · terminando 0
   564 ms  viejos 4 listos + 0 no · nuevos 0 listos + 1 no · terminando 0
  3667 ms  viejos 3 listos + 0 no · nuevos 1 listos + 1 no · terminando 1
  4514 ms  viejos 3 listos + 0 no · nuevos 1 listos + 1 no · terminando 0
  7334 ms  viejos 2 listos + 0 no · nuevos 2 listos + 1 no · terminando 1
  8468 ms  viejos 2 listos + 0 no · nuevos 2 listos + 1 no · terminando 0
 10731 ms  viejos 1 listos + 0 no · nuevos 3 listos + 1 no · terminando 1
 11579 ms  viejos 1 listos + 0 no · nuevos 3 listos + 1 no · terminando 0
 14396 ms  viejos 0 listos + 0 no · nuevos 4 listos + 0 no · terminando 1
 15527 ms  viejos 0 listos + 0 no · nuevos 4 listos + 0 no · terminando 0
RESUMEN: completo en 15527 ms · máximo de pods a la vez: 6 · mínimo de pods listos: 4
tráfico durante el rollout → peticiones: 458 · nginx/1.30.6: 287 · ERROR-rechazada: 7 · nginx/1.29.8: 160 · ERROR-tiempo: 4

### 9 · Rollout C: maxSurge 100 %, maxUnavailable 0 · 1.29.8 → 1.30.6
deployment.apps/web patched
$ kubectl patch … maxSurge "100%", maxUnavailable 0
$ kubectl set image deployment/web nginx=nginx:1.30.6-alpine
     0 ms  viejos 4 listos + 0 no · nuevos 0 listos + 0 no · terminando 0
   563 ms  viejos 4 listos + 0 no · nuevos 0 listos + 4 no · terminando 0
  4253 ms  viejos 2 listos + 0 no · nuevos 2 listos + 2 no · terminando 2
  4537 ms  viejos 0 listos + 0 no · nuevos 4 listos + 0 no · terminando 4
  5103 ms  viejos 0 listos + 0 no · nuevos 4 listos + 0 no · terminando 2
  5385 ms  viejos 0 listos + 0 no · nuevos 4 listos + 0 no · terminando 0
RESUMEN: completo en 5385 ms · máximo de pods a la vez: 8 · mínimo de pods listos: 4
tráfico durante el rollout → peticiones: 251 · nginx/1.30.6: 62 · ERROR-rechazada: 2 · nginx/1.29.8: 186 · ERROR-tiempo: 1

### 10 · Rollout D: strategy Recreate · 1.30.6 → 1.29.8
deployment.apps/web patched
$ kubectl patch deployment web -p '{"spec":{"strategy":{"type":"Recreate","rollingUpdate":null}}}'
$ kubectl set image deployment/web nginx=nginx:1.29.8-alpine
     1 ms  viejos 4 listos + 0 no · nuevos 0 listos + 0 no · terminando 0
   562 ms  viejos 0 listos + 0 no · nuevos 0 listos + 0 no · terminando 4
  1129 ms  viejos 0 listos + 0 no · nuevos 0 listos + 0 no · terminando 2
  1409 ms  viejos 0 listos + 0 no · nuevos 0 listos + 4 no · terminando 0
  5082 ms  viejos 0 listos + 0 no · nuevos 2 listos + 2 no · terminando 0
  5364 ms  viejos 0 listos + 0 no · nuevos 4 listos + 0 no · terminando 0
RESUMEN: completo en 5364 ms · máximo de pods a la vez: 4 · mínimo de pods listos: 0
tráfico durante el rollout → peticiones: 124 · nginx/1.30.6: 32 · ERROR-rechazada: 8 · nginx/1.29.8: 83 · ERROR-tiempo: 1

### 11 · Rollout E: igual que B + preStop sleep 5 s · 1.29.8 → 1.30.6
    lifecycle:
      preStop:
        sleep:
          seconds: 5
$ kubectl patch deployment web -p '{…containers:[{name: nginx, image: nginx:1.30.6-alpine, lifecycle: {preStop: {sleep: {seconds: 5}}}}]}'
     1 ms  viejos 4 listos + 0 no · nuevos 0 listos + 0 no · terminando 0
   568 ms  viejos 4 listos + 0 no · nuevos 0 listos + 1 no · terminando 0
  4244 ms  viejos 3 listos + 0 no · nuevos 1 listos + 1 no · terminando 1
  5376 ms  viejos 3 listos + 0 no · nuevos 1 listos + 1 no · terminando 0
  8198 ms  viejos 2 listos + 0 no · nuevos 2 listos + 1 no · terminando 1
  9048 ms  viejos 2 listos + 0 no · nuevos 2 listos + 1 no · terminando 0
 11299 ms  viejos 1 listos + 0 no · nuevos 3 listos + 1 no · terminando 1
 12429 ms  viejos 1 listos + 0 no · nuevos 3 listos + 1 no · terminando 0
 15248 ms  viejos 0 listos + 0 no · nuevos 4 listos + 0 no · terminando 1
 16097 ms  viejos 0 listos + 0 no · nuevos 4 listos + 0 no · terminando 0
RESUMEN: completo en 16097 ms · máximo de pods a la vez: 6 · mínimo de pods listos: 4
tráfico durante el rollout → peticiones: 454 · nginx/1.30.6: 155 · ERROR-rechazada: 3 · nginx/1.29.8: 292 · ERROR-tiempo: 4

### 11b · Rollout F: igual que E, ahora que los pods VIEJOS ya tienen el preStop · 1.30.6 → 1.29.8
$ kubectl get deployment web -o jsonpath='{.spec.template.spec.containers[0].lifecycle}'
{"preStop":{"sleep":{"seconds":5}}}
$ kubectl set image deployment/web nginx=nginx:1.29.8-alpine
     1 ms  viejos 4 listos + 0 no · nuevos 0 listos + 0 no · terminando 0
   566 ms  viejos 4 listos + 0 no · nuevos 0 listos + 1 no · terminando 0
  3661 ms  viejos 3 listos + 0 no · nuevos 1 listos + 1 no · terminando 1
  7359 ms  viejos 2 listos + 0 no · nuevos 2 listos + 1 no · terminando 2
  9635 ms  viejos 2 listos + 0 no · nuevos 2 listos + 1 no · terminando 1
 10483 ms  viejos 1 listos + 0 no · nuevos 3 listos + 1 no · terminando 2
 13311 ms  viejos 1 listos + 0 no · nuevos 3 listos + 1 no · terminando 1
 14442 ms  viejos 0 listos + 0 no · nuevos 4 listos + 0 no · terminando 2
 16698 ms  viejos 0 listos + 0 no · nuevos 4 listos + 0 no · terminando 1
 20365 ms  viejos 0 listos + 0 no · nuevos 4 listos + 0 no · terminando 0
RESUMEN: completo en 20365 ms · máximo de pods a la vez: 7 · mínimo de pods listos: 4
tráfico durante el rollout → peticiones: 964 · nginx/1.30.6: 408 · nginx/1.29.8: 556

### 12 · Historia de revisiones
$ kubectl rollout history deployment/web
deployment.apps/web 
REVISION  CHANGE-CAUSE
4         C: surge 100% a 1.30.6
5         D: Recreate a 1.29.8
6         E: B + preStop 5 s a 1.30.6
7         F: preStop en viejos y nuevos a 1.29.8

$ kubectl get rs -l app=web
NAME             DESIRED   CURRENT   READY   AGE
web-6c85658fb    0         0         0       2m2s
web-6cccd74dd7   4         4         4       23s
web-76594894d8   0         0         0       86s
web-98c48c79     0         0         0       42s

### 13 · Una versión rota con maxUnavailable 0 (y progressDeadlineSeconds 30)
$ kubectl set image deployment/web nginx=nginx:1.99.0-alpine   # esa versión no existe
deployment.apps/web image updated
     0 ms  viejos 4 listos + 0 no · nuevos 0 listos + 0 no · terminando 0
   563 ms  viejos 4 listos + 0 no · nuevos 0 listos + 1 no · terminando 0
RESUMEN: (se acabó el tiempo: 50 s) · máximo de pods a la vez: 5 · mínimo de pods listos: 4
tráfico durante los 50 s → peticiones: 1985 · nginx/1.29.8: 1983 · ERROR-tiempo: 2
$ kubectl get pods -l app=web
NAME                   READY   STATUS             RESTARTS   AGE
web-5d7bd554b4-kswb9   0/1     ImagePullBackOff   0          51s
web-6cccd74dd7-drhk6   1/1     Running            0          71s
web-6cccd74dd7-dsg7t   1/1     Running            0          67s
web-6cccd74dd7-l9gpq   1/1     Running            0          64s
web-6cccd74dd7-mfdnq   1/1     Running            0          74s
$ kubectl rollout status deployment/web
error: deployment "web" exceeded its progress deadline
$ kubectl get deployment web -o jsonpath='{.status.conditions[?(@.type=="Progressing")].reason}'
ProgressDeadlineExceeded
$ kubectl rollout undo deployment/web
deployment.apps/web rolled back
deployment "web" successfully rolled out
(rollout undo completo 391 ms después)
$ kubectl get pods -l app=web -o custom-columns=POD:.metadata.name,IMAGEN:.spec.containers[0].image,LISTO:.status.containerStatuses[0].ready
POD                    IMAGEN                LISTO
web-5d7bd554b4-kswb9   nginx:1.99.0-alpine   false
web-6cccd74dd7-drhk6   nginx:1.29.8-alpine   true
web-6cccd74dd7-dsg7t   nginx:1.29.8-alpine   true
web-6cccd74dd7-l9gpq   nginx:1.29.8-alpine   true
web-6cccd74dd7-mfdnq   nginx:1.29.8-alpine   true
$ kubectl rollout history deployment/web
deployment.apps/web 
REVISION  CHANGE-CAUSE
4         C: surge 100% a 1.30.6
5         D: Recreate a 1.29.8
6         E: B + preStop 5 s a 1.30.6
8         rota: 1.99.0 no existe
9         F: preStop en viejos y nuevos a 1.29.8

```

> Contenedores ajenos vivos al terminar: k8s-b-control-plane k8s-b-worker k8s-b-worker2 
