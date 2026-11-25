# SALIDA — Curso de Kubernetes 2027 · Parte 1: el Pod

> Corrida del 2026-11-22 18:44. kind v0.30.0, clúster k8s-a (1 plano de control + 2 workers), kindest/node:v1.34.0.
> Imágenes ya descargadas en los nodos antes de correr (no se mide la descarga).
> Contenedores ajenos vivos al empezar: k8s-b-control-plane k8s-b-worker k8s-b-worker2 

```

### 1 · El clúster
$ kubectl version
Client Version: v1.34.0
Server Version: v1.34.0
$ kubectl get nodes
NAME                  STATUS   ROLES           AGE     VERSION
k8s-a-control-plane   Ready    control-plane   5m57s   v1.34.0
k8s-a-worker          Ready    <none>          5m47s   v1.34.0
k8s-a-worker2         Ready    <none>          5m47s   v1.34.0
$ kubectl create namespace parte1 && kubectl config set-context --current --namespace=parte1

### 2 · Un pod
$ kubectl apply -f 1-pod.yaml
pod/web created
$ kubectl get pod web -o wide
NAME   READY   STATUS    RESTARTS   AGE   IP           NODE            NOMINATED NODE   READINESS GATES
web    1/1     Running   0          1s    10.244.2.3   k8s-a-worker2   <none>           <none>
$ kubectl get pod web -o jsonpath='{.metadata.uid}'
6815b66e-4d3a-4059-ab60-bc0cc36a5ed5

### 3 · Qué hay dentro: el contenedor pause
$ crictl pods --name web   # dentro del nodo k8s-a-worker2
POD STATE NAME
af713437daaa5 Ready web
$ crictl ps --pod af713437daaa5eb74121ceb931d57b7dde75ea1cc6310a4a22abdf76177f788f
CONTAINER NAME ATTEMPT
1f2d391e65fdc Running nginx
$ crictl inspectp af713437daaa5eb74121ceb931d57b7dde75ea1cc6310a4a22abdf76177f788f | jq -r '.info.runtimeSpec.annotations["io.kubernetes.cri.podsandbox.image-name"]'
registry.k8s.io/pause:3.10
$ cat /proc/1419/comm /proc/1444/comm ; readlink /proc/1419/ns/net /proc/1444/ns/net
pause
nginx
net:[4026533538]
net:[4026533538]

### 4 · Multicontenedor: init + sidecar nativo
$ kubectl apply -f 2-sidecar.yaml
pod/con-sidecar created
$ kubectl get pod con-sidecar
NAME          READY   STATUS    RESTARTS   AGE
con-sidecar   2/2     Running   0          3s
$ kubectl get pod con-sidecar -o jsonpath='{range .status.initContainerStatuses[*]}{.name} {.state}{"\n"}{end}'
preparar terminated (Completed)
lector-logs running
$ kubectl exec con-sidecar -c lector-logs -- wget -qO- http://localhost   # otro contenedor, mismo localhost
hola desde el pod
$ kubectl exec con-sidecar -c lector-logs -- hostname ; kubectl exec con-sidecar -c nginx -- hostname
con-sidecar
con-sidecar
$ kubectl logs con-sidecar -c lector-logs
127.0.0.1 - - [fecha] "GET / HTTP/1.1" 200 18 "-" "Wget" "-"

### 5 · Fases y restartPolicy
$ kubectl apply -f 3-fases.yaml
pod/termina-bien created
pod/termina-mal created
pod/reintenta created
pod/siempre created
--- termina-bien, cada cambio de READY STATUS RESTARTS:
      0 ms  (no existe)
    460 ms  0/1 ContainerCreating 0
   1149 ms  1/1 Running 0
   4135 ms  0/1 Completed 0
$ kubectl get pods termina-bien termina-mal reintenta siempre
NAME           READY   STATUS      RESTARTS   AGE
termina-bien   0/1     Completed   0          14s
termina-mal    0/1     Error       0          14s
reintenta      0/1     Error       1          14s
siempre        0/1     Completed   1          14s
$ kubectl get pods -o custom-columns=POD:.metadata.name,FASE:.status.phase,POLITICA:.spec.restartPolicy,SALIDA:.status.containerStatuses[0].state.terminated.exitCode,ULTIMA:.status.containerStatuses[0].lastState.terminated.exitCode
POD            FASE        POLITICA    SALIDA   ULTIMA
termina-bien   Succeeded   Never       0        <none>
termina-mal    Failed      Never       3        <none>
reintenta      Running     OnFailure   <none>   1
siempre        Running     Always      <none>   0

### 6 · Back-off de reinicios: pod reintenta (sale con 1 cada vez), 150 s mirando
      0 ms  0/1 CrashLoopBackOff 1
    529 ms  1/1 Running 2
   1590 ms  0/1 Error 2
  14306 ms  0/1 CrashLoopBackOff 2
  27596 ms  1/1 Running 3
  28713 ms  0/1 Error 3
  40247 ms  0/1 CrashLoopBackOff 3
  74778 ms  1/1 Running 4
  75836 ms  0/1 Error 4
  85901 ms  0/1 CrashLoopBackOff 4
$ kubectl get pod reintenta
NAME        READY   STATUS             RESTARTS      AGE
reintenta   0/1     CrashLoopBackOff   4 (75s ago)   2m44s
$ kubectl describe pod reintenta | grep -i back-off
 Warning BackOff 8s (x13 over 2m41s) kubelet Back-off restarting failed container tarea in pod reintenta_parte1(0d5af722-106e-4a37-bbb8-0f51beb45bc3)

### 7 · Muere el proceso: el pod sigue, el contenedor se reinicia
$ kubectl exec web -- sh -c 'echo hola > /tmp/marca; echo hola > /datos/marca'
$ kubectl exec web -- kill 1   # señal TERM al proceso principal (nginx)
(el contenedor volvió a estar listo 1686 ms después del kill, medido desde la máquina)
$ kubectl get pod web -o wide
NAME   READY   STATUS    RESTARTS     AGE     IP           NODE            NOMINATED NODE   READINESS GATES
web    1/1     Running   1 (2s ago)   2m57s   10.244.2.3   k8s-a-worker2   <none>           <none>
IP antes: 10.244.2.3 · después: 10.244.2.3
UID: el mismo (6815b66e-4d3a-4059-ab60-bc0cc36a5ed5)
$ kubectl get pod web -o jsonpath='{.status.containerStatuses[0].lastState.terminated}'
Completed exitCode=0
$ kubectl exec web -- cat /tmp/marca   # el sistema de archivos del contenedor
cat: can't open '/tmp/marca': No such file or directory
command terminated with exit code 1
$ kubectl exec web -- cat /datos/marca   # el volumen emptyDir del pod
hola
$ kubectl logs web --previous | tail -3
[fecha] [notice] 1#1: signal 17 (SIGCHLD) received from 48
[fecha] [notice] 1#1: worker process 48 exited with code 0
[fecha] [notice] 1#1: exit
$ kubectl describe pod web   # la sección Events
Events:
 Type Reason Age From Message
 ---- ------ ---- ---- -------
 Normal Scheduled 2m58s default-scheduler Successfully assigned parte1/web to k8s-a-worker2
 Normal Pulled 2s (x2 over 2m57s) kubelet Container image "nginx:1.29.8-alpine" already present on machine
 Normal Created 2s (x2 over 2m57s) kubelet Created container: nginx
 Normal Started 2s (x2 over 2m57s) kubelet Started container nginx

### 8 · Borrar el pod: nadie lo vuelve a crear
$ kubectl delete pod web
pod "web" deleted from parte1 namespace
(kubectl delete tardó 1260 ms)
$ kubectl get pod web
Error from server (NotFound): pods "web" not found

### 9 · Muere el NODO (docker kill k8s-a-worker2: corte de luz, sin apagado ordenado)
$ kubectl apply -f 4-en-worker2.yaml
pod/huerfano created
NAME READY STATUS NODE
huerfano 1/1 Running k8s-a-worker2
$ kubectl get pod huerfano -o jsonpath='{.spec.tolerations}'   # las que pone Kubernetes solo
node.kubernetes.io/not-ready NoExecute 300
node.kubernetes.io/unreachable NoExecute 300
$ docker kill k8s-a-worker2
   0 s  nodo=Ready · pod=1/1 Running · Ready=True · taints=
  49 s  nodo=NotReady · pod=1/1 Running · Ready=False · taints=unreachable:NoSchedule unreachable:NoExecute 
 347 s  nodo=NotReady · pod=1/1 Terminating · Ready=False · taints=unreachable:NoSchedule unreachable:NoExecute 
$ kubectl get pod huerfano
NAME       READY   STATUS        RESTARTS   AGE
huerfano   1/1     Terminating   0          7m3s
$ docker start k8s-a-worker2   # vuelve la luz
(nodo Ready otra vez 2 s después de encenderlo)
$ kubectl get pod huerfano
Error from server (NotFound): pods "huerfano" not found
```

> Contenedores ajenos vivos al terminar: k8s-b-control-plane k8s-b-worker k8s-b-worker2 
