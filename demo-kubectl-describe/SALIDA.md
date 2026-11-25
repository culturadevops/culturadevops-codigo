# SALIDA — kubectl describe pod: cómo leerlo (cultura-devops)

> Corrida del 2026-10-20 16:54. Kubernetes de un nodo con k3s (rancher/k3s:v1.37.1-k3s1) dentro de Docker.

```
### 1 · Los pods
$ kubectl apply -f pods.yaml && kubectl get pods
NAME         READY   STATUS              RESTARTS      AGE
no-listo     0/1     Running             0             64s
pendiente    0/1     Pending             0             64s
sano         1/1     Running             0             64s
se-cae       0/1     Error               3 (41s ago)   64s
sin-config   0/1     ContainerCreating   0             64s

### 2 · Un pod sano, completo
$ kubectl describe pod sano
Name:             sano
Namespace:        demo
Priority:         0
Service Account:  default
Node:             41ee11f12037/172.17.0.2
Start Time:       Tue, 20 Oct 2026 21:54:47 +0000
Labels:           app=tienda
Annotations:      <none>
Status:           Running
IP:               10.42.0.6
IPs:
  IP:  10.42.0.6
Containers:
  web:
    Container ID:   containerd://db0354fa433dc18aa8b3ee224840184c66e52dec5ff2329b8a0f409ad25f2f56
    Image:          nginx:1.30.5-alpine
    Image ID:       docker.io/library/nginx@sha256:0985e772fb9f729e6fa0980da05fca5d9c468e870eed43071545afa9d2e27d94
    Port:           80/TCP
    Host Port:      0/TCP
    State:          Running
      Started:      Tue, 20 Oct 2026 21:54:57 +0000
    Ready:          True
    Restart Count:  0
    Limits:
      memory:  64Mi
    Requests:
      cpu:        50m
      memory:     32Mi
    Readiness:    http-get http://:80/ delay=0s timeout=1s period=10s successThreshold=1 failureThreshold=3
    Environment:  <none>
    Mounts:
      /var/run/secrets/kubernetes.io/serviceaccount from kube-api-access-nn58s (ro)
Conditions:
  Type                        Status
  PodReadyToStartContainers   True 
  Initialized                 True 
  Ready                       True 
  ContainersReady             True 
  PodScheduled                True 
Volumes:
  kube-api-access-nn58s:
    Type:                    Projected (a volume that contains injected data from multiple sources)
    TokenExpirationSeconds:  3607
    ConfigMapName:           kube-root-ca.crt
    Optional:                false
    DownwardAPI:             true
QoS Class:                   Burstable
Node-Selectors:              <none>
Tolerations:                 node.kubernetes.io/not-ready:NoExecute op=Exists for 300s
                             node.kubernetes.io/unreachable:NoExecute op=Exists for 300s
Events:
  Type     Reason     Age   From               Message
  ----     ------     ----  ----               -------
  Normal   Scheduled  63s   default-scheduler  Successfully assigned demo/sano to 41ee11f12037
  Normal   Pulling    61s   kubelet            spec.containers{web}: Pulling image "nginx:1.30.5-alpine"
  Normal   Pulled     54s   kubelet            spec.containers{web}: Successfully pulled image "nginx:1.30.5-alpine" in 6.899s (6.899s including waiting). Image size: 26098628 bytes.
  Normal   Created    54s   kubelet            spec.containers{web}: Container created
  Normal   Started    54s   kubelet            spec.containers{web}: Container started
  Warning  Unhealthy  54s   kubelet            spec.containers{web}: Readiness probe failed: Get "http://10.42.0.6:80/": dial tcp 10.42.0.6:80: connect: connection refused

### 3 · Pending: ningún nodo tiene sitio
$ kubectl describe pod pendiente   # solo Status y Events
Node:             <none>
Status:           Pending
Events:
  Type     Reason            Age   From               Message
  ----     ------            ----  ----               -------
  Warning  FailedScheduling  64s   default-scheduler  0/1 nodes are available: 1 Insufficient cpu. preemption: 0/1 nodes are available: 1 Preemption is not helpful for scheduling.
  Warning  FailedScheduling  47s   default-scheduler  0/1 nodes are available: 1 Insufficient cpu. preemption: 0/1 nodes are available: 1 Preemption is not helpful for scheduling.
$ kubectl describe node | sed -n '/Allocatable/,/System Info/p'
Allocatable:
  cpu:                24
  memory:             16101052Ki

### 4 · CrashLoopBackOff: el contenedor arranca y se muere
$ kubectl get pod se-cae
NAME     READY   STATUS             RESTARTS      AGE
se-cae   0/1     CrashLoopBackOff   4 (63s ago)   2m43s
$ kubectl describe pod se-cae   # la parte de Containers
    State:          Waiting
      Reason:       CrashLoopBackOff
    Last State:     Terminated
      Reason:       Error
      Exit Code:    1
      Started:      Tue, 20 Oct 2026 21:56:27 +0000
      Finished:     Tue, 20 Oct 2026 21:56:27 +0000
    Ready:          False
    Restart Count:  4
Events:
  Type     Reason     Age                  From               Message
  ----     ------     ----                 ----               -------
  Normal   Scheduled  2m43s                default-scheduler  Successfully assigned demo/se-cae to 41ee11f12037
  Normal   Pulling    2m40s                kubelet            spec.containers{app}: Pulling image "busybox:1.37"
  Normal   Pulled     2m33s                kubelet            spec.containers{app}: Successfully pulled image "busybox:1.37" in 7.177s (7.177s including waiting). Image size: 2222118 bytes.
  Normal   Created    63s (x5 over 2m33s)  kubelet            spec.containers{app}: Container created
  Normal   Started    63s (x5 over 2m33s)  kubelet            spec.containers{app}: Container started
  Normal   Pulled     63s (x4 over 2m32s)  kubelet            spec.containers{app}: Container image "busybox:1.37" already present on machine and can be accessed by the pod
  Warning  BackOff    1s (x5 over 2m31s)   kubelet            spec.containers{app}: Back-off restarting failed container app in pod se-cae_demo(8c3912b6-e2d7-4a53-b27a-d03feba77d88)
$ kubectl logs se-cae
conectando a la base de datos...
ERROR: no encuentro DB_HOST

### 5 · Running pero no Ready: falla la readiness probe
$ kubectl get pod no-listo
NAME       READY   STATUS    RESTARTS   AGE
no-listo   0/1     Running   0          2m43s
$ kubectl describe pod no-listo   # Readiness, Conditions y Events
    Ready:          False
    Readiness:      http-get http://:80/salud delay=0s timeout=1s period=3s successThreshold=1 failureThreshold=3
Conditions:
  Type                        Status
  PodReadyToStartContainers   True 
  Initialized                 True 
  Ready                       False 
  ContainersReady             False 
  PodScheduled                True 
Events:
  Type     Reason     Age                   From               Message
  ----     ------     ----                  ----               -------
  Normal   Scheduled  2m43s                 default-scheduler  Successfully assigned demo/no-listo to 41ee11f12037
  Normal   Pulling    2m41s                 kubelet            spec.containers{web}: Pulling image "nginx:1.30.5-alpine"
  Normal   Pulled     2m34s                 kubelet            spec.containers{web}: Successfully pulled image "nginx:1.30.5-alpine" in 6.906s (6.906s including waiting). Image size: 26098628 bytes.
  Normal   Created    2m34s                 kubelet            spec.containers{web}: Container created
  Normal   Started    2m34s                 kubelet            spec.containers{web}: Container started
  Warning  Unhealthy  2m34s                 kubelet            spec.containers{web}: Readiness probe failed: Get "http://10.42.0.8:80/salud": dial tcp 10.42.0.8:80: connect: connection refused
  Warning  Unhealthy  86s (x24 over 2m34s)  kubelet            spec.containers{web}: Readiness probe failed: HTTP probe failed with statuscode: 404

### 6 · ContainerCreating para siempre: falta un ConfigMap
$ kubectl get pod sin-config
NAME         READY   STATUS              RESTARTS   AGE
sin-config   0/1     ContainerCreating   0          2m44s
$ kubectl describe pod sin-config   # la parte de Events
Events:
  Type     Reason       Age                  From               Message
  ----     ------       ----                 ----               -------
  Normal   Scheduled    2m43s                default-scheduler  Successfully assigned demo/sin-config to 41ee11f12037
  Warning  FailedMount  36s (x9 over 2m44s)  kubelet            MountVolume.SetUp failed for volume "config" : configmap "config-app" not found
$ kubectl create configmap config-app --from-literal=modo=produccion
configmap/config-app created
$ kubectl get pod sin-config
NAME         READY   STATUS    RESTARTS   AGE
sin-config   1/1     Running   0          4m10s

### 7 · Los eventos de todo el namespace, en orden
$ kubectl get events --sort-by=.lastTimestamp | tail -8
Warning   FailedMount        sin-config
Normal    Started            se-cae
Normal    Pulled             se-cae
Normal    Created            se-cae
Warning   BackOff            se-cae
Normal    Pulled             sin-config
Normal    Created            sin-config
Normal    Started            sin-config
```
