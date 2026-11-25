# SALIDA — ImagePullBackOff en Kubernetes (cultura-devops)

> Corrida del 2026-10-20 16:40. Kubernetes de un nodo con k3s (rancher/k3s:v1.37.1-k3s1) dentro de Docker,
> y un registro privado (registry:3 con htpasswd) en la misma red con el nombre registro:5000. La clave se oculta con asteriscos.

```
### 1 · Una etiqueta que no existe
$ kubectl run web --image=nginx:1.30.99-alpine
pod/web created
$ kubectl get pod web
NAME   READY   STATUS              RESTARTS   AGE
web    0/1     ContainerCreating   0          4s
$ kubectl get pod web   # unos segundos después
NAME   READY   STATUS             RESTARTS   AGE
web    0/1     ImagePullBackOff   0          20s
$ kubectl describe pod web   # la parte de Events
Events:
  Type     Reason     Age               From               Message
  ----     ------     ----              ----               -------
  Normal   Scheduled  20s               default-scheduler  Successfully assigned demo/web to 1a9c6bdc8e65
  Normal   BackOff    15s               kubelet            spec.containers{web}: Back-off pulling image "nginx:1.30.99-alpine"
  Warning  Failed     15s               kubelet            spec.containers{web}: Error: ImagePullBackOff
  Normal   Pulling    1s (x2 over 17s)  kubelet            spec.containers{web}: Pulling image "nginx:1.30.99-alpine"
  Warning  Failed     0s (x2 over 16s)  kubelet            spec.containers{web}: Failed to pull image "nginx:1.30.99-alpine": rpc error: code = NotFound desc = failed to pull and unpack image "docker.io/library/nginx:1.30.99-alpine": failed to resolve reference "docker.io/library/nginx:1.30.99-alpine": docker.io/library/nginx:1.30.99-alpine: not found
  Warning  Failed     0s (x2 over 16s)  kubelet            spec.containers{web}: Error: ErrImagePull

### 2 · El nombre de la imagen mal escrito
$ kubectl run web2 --image=ngnix:1.30.5-alpine
pod/web2 created
$ kubectl get events --field-selector involvedObject.name=web2,reason=Failed
Failed to pull image "ngnix:1.30.5-alpine": failed to pull and unpack image "docker.io/library/ngnix:1.30.5-alpine": failed to resolve reference "docker.io/library/ngnix:1.30.5-alpine": pull access denied, repository does not exist or may require authorization: server message: insufficient_scope: authorization failed

### 3 · Un registro que no existe (o mal escrito)
$ kubectl run web3 --image=registor:5000/tienda/web:1.0
pod/web3 created
$ kubectl get events --field-selector involvedObject.name=web3,reason=Failed
Failed to pull image "registor:5000/tienda/web:1.0": failed to pull and unpack image "registor:5000/tienda/web:1.0": failed to resolve reference "registor:5000/tienda/web:1.0": failed to do request: Head "https://registor:5000/v2/tienda/web/manifests/1.0": dial tcp: lookup registor: Try again

### 4 · Un registro privado sin credenciales
$ kubectl run web4 --image=registro:5000/tienda/web:1.0
pod/web4 created
$ kubectl get events --field-selector involvedObject.name=web4,reason=Failed
Failed to pull image "registro:5000/tienda/web:1.0": failed to pull and unpack image "registro:5000/tienda/web:1.0": failed to resolve reference "registro:5000/tienda/web:1.0": pull access denied, repository does not exist or may require authorization: authorization failed: no basic auth credentials

### 5 · El arreglo: un secreto de tipo docker-registry
$ kubectl create secret docker-registry registro-cred --docker-server=registro:5000 --docker-username=tienda --docker-password=********
secret/registro-cred created
$ kubectl apply -f pod-con-secreto.yaml
pod/web5 created
$ kubectl get pod web5
NAME   READY   STATUS    RESTARTS   AGE
web5   1/1     Running   0          1s
$ kubectl describe pod web5   # la parte de Events
Events:
  Type    Reason     Age   From               Message
  ----    ------     ----  ----               -------
  Normal  Scheduled  1s    default-scheduler  Successfully assigned demo/web5 to 1a9c6bdc8e65
  Normal  Pulling    1s    kubelet            spec.containers{web}: Pulling image "registro:5000/tienda/web:1.0"
  Normal  Pulled     0s    kubelet            spec.containers{web}: Successfully pulled image "registro:5000/tienda/web:1.0" in 505ms (505ms including waiting). Image size: 26088311 bytes.
  Normal  Created    0s    kubelet            spec.containers{web}: Container created
  Normal  Started    0s    kubelet            spec.containers{web}: Container started

### 6 · El back-off: cada vez espera más
$ kubectl get events --field-selector involvedObject.name=web,reason=BackOff
MOTIVO    VECES   MENSAJE
BackOff   3       Back-off pulling image "nginx:1.30.99-alpine"
$ kubectl get pods
NAME   READY   STATUS             RESTARTS   AGE
web    0/1     ErrImagePull       0          78s
web2   0/1     ErrImagePull       0          58s
web3   0/1     ErrImagePull       0          41s
web4   0/1     ImagePullBackOff   0          18s
web5   1/1     Running            0          1s

### 7 · Arreglar la etiqueta en un Deployment
$ kubectl create deployment tienda --image=nginx:1.30.99-alpine
deployment.apps/tienda created
$ kubectl get pods -l app=tienda
NAME                      READY   STATUS             RESTARTS   AGE
tienda-558c7cd745-fz8dm   0/1     ImagePullBackOff   0          20s
$ kubectl set image deployment/tienda nginx=nginx:1.30.5-alpine
deployment.apps/tienda image updated
Waiting for deployment "tienda" rollout to finish: 1 old replicas are pending termination...
Waiting for deployment "tienda" rollout to finish: 1 old replicas are pending termination...
Waiting for deployment "tienda" rollout to finish: 1 old replicas are pending termination...
deployment "tienda" successfully rolled out
$ kubectl get pods -l app=tienda
NAME                      READY   STATUS        RESTARTS   AGE
tienda-558c7cd745-fz8dm   0/1     Terminating   0          28s
tienda-6fdcc6bcdd-w6c7k   1/1     Running       0          8s
```
