# SALIDA — Argo CD en 5 minutos (cultura-devops)

Generado 2026-10-23 12:38 UTC con `python correr.py`. k3s en Docker, Argo CD v3.5.6 con su manifiesto oficial, Gitea (gitea/gitea:1.25) como repositorio.

## 1 · Instalar Argo CD

### el manifiesto oficial

`$ kubectl apply -n argocd --server-side -f …/argo-cd/v3.5.6/manifests/install.yaml | tail -2`

```
networkpolicy.networking.k8s.io/argocd-repo-server-network-policy serverside-applied
networkpolicy.networking.k8s.io/argocd-server-network-policy serverside-applied
```
(código de salida 0)

> Todo listo a los 47 s (incluye bajar las imágenes).

### lo que instala

`$ kubectl get pods -n argocd`

```
POD                                                 ESTADO
argocd-application-controller-0                     Running
argocd-applicationset-controller-86bcdc46cf-pgtwn   Running
argocd-dex-server-7f65987db5-8bn44                  Running
argocd-notifications-controller-6885f68ddd-tvqxn    Running
argocd-redis-7d5d5cb5b6-9l4rf                       Running
argocd-repo-server-7f4759f94-q4lhw                  Running
argocd-server-777cfb8fc4-pz7ws                      Running
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
886635f web con 2 réplicas
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

> Synced y Healthy a los 2.2 s.

### lo que creó en el clúster

`$ kubectl get deploy,cm -n tienda`

```
NAME      DATA   AGE
ajustes   1      2s
Error from server (NotFound): deployments.apps "ajustes" not found
```
(código de salida 1)

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
22b6ac1 web con 4 réplicas
```
(código de salida 0)

> Sin webhook (sondeo por defecto), el clúster pasó a 4 réplicas a los 249.6 s del push.

## 5 · Volver atrás es un git revert

### git revert

`$ git revert --no-edit HEAD && git push`

```
usage: git revert [--[no-]edit] [-n] [-m <parent-number>] [-s] [-S[<keyid>]] <commit>...
   or: git revert (--continue | --skip | --abort | --quit)

    --quit                end revert or cherry-pick sequence
    --continue            resume revert or cherry-pick sequence
    --abort               cancel revert or cherry-pick sequence
    --skip                skip current commit and continue
    --[no-]cleanup <mode> how to strip spaces and #comments from message
    -n, --no-commit       don't automatically commit
    --commit              opposite of --no-commit
    -e, --[no-]edit       edit the commit message
    -s, --[no-]signoff    add a Signed-off-by trailer
    -m, --[no-]mainline <parent-number>
                          select mainline parent
    --[no-]rerere-autoupdate
                          update the index with reused conflict resolution if possible
    --[no-]strategy <strategy>
                          merge strategy
    -X, --[no-]strategy-option <option>
                          option for merge strategy
    -S, --[no-]gpg-sign[=<key-id>]
                          GPG sign commit
    --[no-]reference      use the 'reference' format to refer to commits
```
(código de salida 129)

> El clúster volvió a 2 réplicas a los None s del push.

## 6 · Se borra algo del repositorio

> prune: el ConfigMap desapareció del clúster a los 57.3 s del push.

### lo que queda

`$ kubectl get deploy,cm -n tienda`

```
NAME                  READY   UP-TO-DATE   AVAILABLE   AGE
deployment.apps/web   2/2     2            2           12m

NAME                         DATA   AGE
```
(código de salida 0)
