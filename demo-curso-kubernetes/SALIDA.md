# SALIDA — Kubernetes: curso completo en un vídeo (cultura-devops)

> Corrida del 2026-10-20 13:06. Kubernetes de un nodo con k3s (rancher/k3s:v1.37.1-k3s1) dentro de Docker.

```
### 1 · El clúster
$ kubectl get nodes -o wide
NOMBRE         ESTADO   VERSION
a0ea553b21df   Ready    v1.37.1+k3s1
$ kubectl get pods -n kube-system   # los ayudantes del clúster
POD                                       ESTADO
coredns-577d995dff-nb6bg                  Running
local-path-provisioner-6858d854cf-jhsbf   Running
metrics-server-778c4649b4-7ckx8           Running

### 2 · Un Deployment
$ kubectl create namespace curso && kubectl config set-context --current --namespace=curso
namespace/curso created
$ kubectl apply -f 1-deployment.yaml
deployment.apps/web created
$ kubectl get deployment,pods
NAME   READY   UP-TO-DATE   AVAILABLE   AGE
web    3/3     3            3           5s
POD                    ESTADO    IMAGEN
web-6f7457f7d8-6pb9c   Running   nginx:1.29-alpine
web-6f7457f7d8-9wkrh   Running   nginx:1.29-alpine
web-6f7457f7d8-b42zg   Running   nginx:1.29-alpine

### 3 · Actualizar y volver atrás
$ kubectl set image deployment/web nginx=nginx:1.29.1-alpine
deployment.apps/web image updated
Waiting for deployment "web" rollout to finish: 1 out of 3 new replicas have been updated...
Waiting for deployment "web" rollout to finish: 1 out of 3 new replicas have been updated...
Waiting for deployment "web" rollout to finish: 1 out of 3 new replicas have been updated...
Waiting for deployment "web" rollout to finish: 2 out of 3 new replicas have been updated...
Waiting for deployment "web" rollout to finish: 2 out of 3 new replicas have been updated...
Waiting for deployment "web" rollout to finish: 2 out of 3 new replicas have been updated...
Waiting for deployment "web" rollout to finish: 2 out of 3 new replicas have been updated...
Waiting for deployment "web" rollout to finish: 1 old replicas are pending termination...
Waiting for deployment "web" rollout to finish: 1 old replicas are pending termination...
Waiting for deployment "web" rollout to finish: 1 old replicas are pending termination...
deployment "web" successfully rolled out
$ kubectl set image deployment/web nginx=nginx:no-existe   # una versión rota
deployment.apps/web image updated
$ kubectl get pods
POD                    ESTADO             LISTO
web-5d5df66859-dqzmb   <none>             true
web-5d5df66859-gwd9d   <none>             true
web-5d5df66859-r5vxk   <none>             true
web-5dc56b857d-7mh9t   ImagePullBackOff   false
$ kubectl rollout undo deployment/web
Warning: resource deployments/web was previously managed with 'kubectl apply'. Rolling back will not update the kubectl.kubernetes.io/last-applied-configuration annotation, which may cause unexpected behavior on future 'kubectl apply' operations. Consider using 'kubectl apply' with your previous configuration file instead.
deployment.apps/web rolled back
deployment "web" successfully rolled out
$ kubectl rollout history deployment/web
deployment.apps/web 
REVISION  CHANGE-CAUSE
1         <none>
3         <none>
4         <none>


### 4 · Un Service delante
$ kubectl apply -f 2-service.yaml && kubectl get service web
service/web created
NOMBRE   TIPO        PUERTO
web      ClusterIP   80
$ kubectl run prueba --rm -i --image=busybox:1.37 --restart=Never -- wget -qO- http://web | grep title
<title>Welcome to nginx!</title>

### 5 · Configuración: ConfigMap y Secret
$ kubectl create configmap app --from-literal=ENTORNO=produccion
configmap/app created
$ kubectl create secret generic db --from-literal=CLAVE=s3cr3to
secret/db created
$ kubectl get secret db -o jsonpath='{.data.CLAVE}'   # NO está cifrado: es base64
czNjcjN0bw==
$ kubectl get secret db -o jsonpath='{.data.CLAVE}' | base64 -d
s3cr3to
$ kubectl apply -f 3-config.yaml && kubectl logs config
pod/config created
entorno=produccion
longitud de la clave=7

### 6 · Salud: la liveness probe reinicia lo que se cuelga
$ kubectl apply -f 4-probe.yaml
pod/colgado created
$ kubectl get pod colgado   # el contenedor borra su archivo de salud a los 15 s
POD       REINICIOS
colgado   1
$ kubectl get events --field-selector involvedObject.name=colgado | grep -i liveness
Unhealthy   Liveness probe failed: cat: can't open '/tmp/sano': No such file or directory
Killing     Container app failed liveness probe, will be restarted

### 7 · Límites: pasar de la memoria pedida
$ kubectl apply -f 5-limites.yaml   # límite 64 MiB, el programa pide 128
pod/tragon created
$ kubectl get pod tragon -o jsonpath='{.status.containerStatuses[0].lastState.terminated.reason} {.status.containerStatuses[0].lastState.terminated.exitCode}'
OOMKilled 137

### 8 · Limpiar: borrar el namespace borra todo lo de dentro
$ kubectl delete namespace curso
namespace "curso" deleted
$ kubectl get all -n curso
No resources found in curso namespace.
```
