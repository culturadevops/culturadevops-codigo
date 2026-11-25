# SALIDA — Argo CD en 5 minutos (cultura-devops)

Generado 2026-10-23 12:55 UTC con `python correr.py`. k3s en Docker, Argo CD v3.5.6 con su manifiesto oficial, Gitea (gitea/gitea:1.25) como repositorio.

## 1 · Instalar Argo CD

### el manifiesto oficial

`$ kubectl apply -n argocd --server-side -f …/argo-cd/v3.5.6/manifests/install.yaml | tail -2`

```
networkpolicy.networking.k8s.io/argocd-repo-server-network-policy serverside-applied
networkpolicy.networking.k8s.io/argocd-server-network-policy serverside-applied
```
(código de salida 0)

> Todo listo a los 46 s (incluye bajar las imágenes).

### lo que instala

`$ kubectl get pods -n argocd`

```
POD                                                 ESTADO
argocd-application-controller-0                     Running
argocd-applicationset-controller-86bcdc46cf-tj5s2   Running
argocd-dex-server-7f65987db5-vvtvm                  Running
argocd-notifications-controller-6885f68ddd-5t72j    Running
argocd-redis-7d5d5cb5b6-llcjf                       Running
argocd-repo-server-7f4759f94-5gfh2                  Running
argocd-server-777cfb8fc4-rnlrh                      Running
```
(código de salida 0)

### la versión

`$ kubectl get deploy argocd-server -n argocd -o jsonpath=…image`

```
quay.io/argoproj/argocd:v3.5.6
```
(código de salida 0)

## 2 · Una aplicación que vive en Git

### lo que hay en el repositorio

`$ git log --oneline; ls web/`

```
c0eda88 web con 2 réplicas
ajustes.yaml
deploy.yaml
```
(código de salida 0)

### la Application

`$ kubectl apply -f app.yaml`

```
application.argoproj.io/web created
apiVersion: argoproj.io/v1alpha1
kind: Application
metadata: {name: web, namespace: argocd}
spec:
  project: default
  source: {repoURL: http://192.168.192.4:3000/lab/apps.git, targetRevision: main, path: web}
  destination: {server: https://kubernetes.default.svc, namespace: tienda}
  syncPolicy:
    automated: {prune: true, selfHeal: true}
    syncOptions: [CreateNamespace=true]
```
(código de salida 0)

> Synced y Healthy a los 6.5 s.

### lo que creó en el clúster

`$ kubectl get deploy,cm -n tienda`

```
NAME   READY   UP-TO-DATE   AVAILABLE   AGE
web    2/2     2            2           6s
NAME      DATA   AGE
ajustes   1      6s
```
(código de salida 0)

## 3 · Alguien lo cambia a mano

### escalar a 5 con kubectl

`$ kubectl scale deploy web -n tienda --replicas=5`

```
deployment.apps/web scaled
```
(código de salida 0)

> selfHeal: volvió a 2 réplicas a los 2.2 s.

## 4 · Un commit en Git

### el commit

`$ git log --oneline | head -1`

```
e217a25 web con 4 réplicas
```
(código de salida 0)

> Sin webhook (sondeo por defecto), el clúster pasó a 4 réplicas a los 223.8 s del push.

## 5 · Volver atrás es un git revert

### git revert

`$ git revert --no-edit HEAD && git push`

```
b64fd84 Revert "web con 4 réplicas"
e217a25 web con 4 réplicas
c0eda88 web con 2 réplicas
remote: . Processing 1 references        
remote: Processed 1 references in total
```
(código de salida 0)

> El clúster volvió a 2 réplicas a los 251.2 s del push.

## 6 · Se borra algo del repositorio

> prune: el ConfigMap desapareció del clúster a los 249.3 s del push.

### lo que queda

`$ kubectl get deploy,cm -n tienda`

```
NAME                  READY   UP-TO-DATE   AVAILABLE   AGE
deployment.apps/web   2/2     2            2           12m

NAME                         DATA   AGE
```
(código de salida 0)
