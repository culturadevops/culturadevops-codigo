# SALIDA — Argo CD (vídeo 328)

Generado 2026-10-07 21:44 UTC con `python correr.py`. k3s (rancher/k3s:latest) + Gitea en Docker; Argo CD de https://raw.githubusercontent.com/argoproj/argo-cd/stable/manifests/install.yaml.

## 1 · Laboratorio: k3s + Gitea en Docker

### nodo

`$ kubectl get nodes`

```
NAME           STATUS   ROLES           AGE   VERSION
e910c2b17ebe   Ready    control-plane   2s    v1.34.1+k3s1
(clúster listo en 10 s)
```

## 2 · Instalar Argo CD

### kubectl apply install.yaml

`$ kubectl apply -n argocd --server-side -f https://raw.githubusercontent.com/argoproj/argo-cd/stable/manifests/install.yaml`

```
59 objetos aplicados
customresourcedefinition.apiextensions.k8s.io/applications.argoproj.io serverside-applied
customresourcedefinition.apiextensions.k8s.io/applicationsets.argoproj.io serverside-applied
customresourcedefinition.apiextensions.k8s.io/appprojects.argoproj.io serverside-applied
deployment.apps/argocd-applicationset-controller serverside-applied
deployment.apps/argocd-dex-server serverside-applied
deployment.apps/argocd-notifications-controller serverside-applied
deployment.apps/argocd-redis serverside-applied
deployment.apps/argocd-repo-server serverside-applied
deployment.apps/argocd-server serverside-applied
statefulset.apps/argocd-application-controller serverside-applied
```

### pods de Argo CD

`$ kubectl get pods -n argocd`

```
NAME                                                READY   STATUS    RESTARTS   AGE
argocd-application-controller-0                     1/1     Running   0          51s
argocd-applicationset-controller-587567d8c9-w6jdn   1/1     Running   0          51s
argocd-dex-server-5f8dcd7cb9-vnwg2                  1/1     Running   0          51s
argocd-notifications-controller-7495ff777d-95sbj    1/1     Running   0          51s
argocd-redis-869ffc4dd6-jlkfw                       1/1     Running   0          51s
argocd-repo-server-855594f74d-hv2hz                 1/1     Running   0          51s
argocd-server-6d9dd9f68-6bq4s                       1/1     Running   0          51s
(todo listo en 54 s)
```

### versión

`$ argocd version --client --short`

```
argocd: v3.5.4
```

### memoria de Argo CD

`$ kubectl top pods -n argocd`

```
NAME                                                CPU(cores)   MEMORY(bytes)   
argocd-application-controller-0                     1m           25Mi            
argocd-applicationset-controller-587567d8c9-w6jdn   1m           22Mi            
argocd-dex-server-5f8dcd7cb9-vnwg2                  1m           21Mi            
argocd-notifications-controller-7495ff777d-95sbj    1m           20Mi            
argocd-redis-869ffc4dd6-jlkfw                       4m           6Mi             
argocd-repo-server-855594f74d-hv2hz                 1m           20Mi            
argocd-server-6d9dd9f68-6bq4s                       4m           44Mi
```

### la contraseña inicial

`$ kubectl get secret argocd-initial-admin-secret ...`

```
(una cadena de 16 caracteres)
```

## 3 · El repositorio y la Application (sincronización manual)

### el repo

`$ git log --oneline; ls`

```
7b03c3a web: nginx con 1 réplica
configmap.yaml
deployment.yaml
service.yaml
```

### recién creada, sin syncPolicy

`$ kubectl get application web -n argocd`

```
sync=OutOfSync  health=Missing  revision=7b03c3a
```

### y en el clúster

`$ kubectl get deploy,svc,cm -n default`

```
NAME                 TYPE        CLUSTER-IP   EXTERNAL-IP   PORT(S)   AGE
service/kubernetes   ClusterIP   10.43.0.1    <none>        443/TCP   83s

NAME                         DATA   AGE
configmap/kube-root-ca.crt   1      75s
```

### después de sincronizar a mano

`$ argocd app sync web  (aquí: operation.sync)`

```
sync=Synced  health=Healthy  revision=7b03c3a
(Synced y Healthy en 7 s)
NAME   READY   UP-TO-DATE   AVAILABLE   AGE
web    1/1     1            1           8s
```

## 4 · Sincronización automática y cuánto tarda en ver un cambio

### el cambio

`$ git commit -m 'web: 3 réplicas' && git push`

```
commit 8f37b2b subido a las 21:37:22 UTC
```

### ¿cuándo lo vio Argo?

`$ kubectl get application web (cada 3 s)`

```
sync=Synced  health=Healthy  revision=8f37b2b
(Argo aplicó 8f37b2b 189 s después del push)
```

### réplicas

`$ kubectl get deploy web`

```
NAME   READY   UP-TO-DATE   AVAILABLE   AGE
web    3/3     3            3           3m31s
```

## 5 · Borrar un manifiesto en Git: sin prune y con prune

### sin prune

`$ kubectl get application web; kubectl get cm web-config`

```
sync=OutOfSync  health=Healthy  revision=7e3e18f
NAME         DATA   AGE
web-config   1      3m40s
ConfigMap/web-config OutOfSync requiresPruning=true
Service/web Synced requiresPruning=
Deployment/web Synced requiresPruning=
```

### historial

`$ status.history`

```
0 7b03c3afb8d14d4397a73b784594e197c54a99f8 2026-10-07T21:37:01Z
1 8f37b2b2a85efae07a4262e918ced9af2413131e 2026-10-07T21:40:28Z
```

### activar prune después del commit

`$ syncPolicy.automated.prune: true (y esperar 240 s)`

```
web-config borrado a los 103 s
sync=Synced  health=Healthy  revision=7e3e18f
0 7b03c3afb8d14d4397a73b784594e197c54a99f8 2026-10-07T21:37:01Z
1 8f37b2b2a85efae07a4262e918ced9af2413131e 2026-10-07T21:40:28Z
2 7e3e18fdf5b21d7eb9196f3e0f2bc3ecca0112f8 2026-10-07T21:42:35Z
```

## 6 · Alguien cambia el clúster a mano (selfHeal)

### sin selfHeal: escalar a 1 y mirar 60 s

`$ kubectl scale deploy/web --replicas=1`

```
t=  0s  spec.replicas=1  sync=OutOfSync  health=Healthy  revision=7e3e18f
t= 11s  spec.replicas=1  sync=OutOfSync  health=Healthy  revision=7e3e18f
t= 21s  spec.replicas=1  sync=OutOfSync  health=Healthy  revision=7e3e18f
t= 32s  spec.replicas=1  sync=OutOfSync  health=Healthy  revision=7e3e18f
t= 42s  spec.replicas=1  sync=OutOfSync  health=Healthy  revision=7e3e18f
t= 53s  spec.replicas=1  sync=OutOfSync  health=Healthy  revision=7e3e18f
```

### activar selfHeal: true

`$ kubectl get deploy web`

```
NAME   READY   UP-TO-DATE   AVAILABLE   AGE
web    1/3     3            1           6m41s
(volvió a 3 réplicas 0 s después de activar selfHeal)
```

### otro cambio a mano, ya con selfHeal

`$ kubectl scale deploy/web --replicas=1`

```
revertido a 3 réplicas en 1 s
```

### historial

`$ status.history`

```
0 7b03c3afb8d14d4397a73b784594e197c54a99f8 2026-10-07T21:37:01Z
1 8f37b2b2a85efae07a4262e918ced9af2413131e 2026-10-07T21:40:28Z
2 7e3e18fdf5b21d7eb9196f3e0f2bc3ecca0112f8 2026-10-07T21:42:35Z
```
