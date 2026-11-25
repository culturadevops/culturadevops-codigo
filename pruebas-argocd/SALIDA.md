# SALIDA — Argo CD (vídeo 408)

Generado 2026-10-13 20:40 UTC con `python correr.py`. k3s en Docker, Argo CD v3.5.5 con su manifiesto oficial, Gitea propio como repositorio.

## 1 · Instalar Argo CD

### el manifiesto oficial

`$ kubectl apply -n argocd --server-side -f …/argo-cd/v3.5.5/manifests/install.yaml | tail -3`

```
networkpolicy.networking.k8s.io/argocd-redis-network-policy serverside-applied
networkpolicy.networking.k8s.io/argocd-repo-server-network-policy serverside-applied
networkpolicy.networking.k8s.io/argocd-server-network-policy serverside-applied
```
(código de salida 0)

> Todo listo a los 33 s (incluye bajar las imágenes).

### lo que instala

`$ kubectl get pods -n argocd`

```
NAME                                                READY   STATUS    RESTARTS   AGE
argocd-application-controller-0                     1/1     Running   0          33s
argocd-applicationset-controller-7c7cd47f9d-wvw9x   1/1     Running   0          33s
argocd-dex-server-6698896998-56tnp                  1/1     Running   0          33s
argocd-notifications-controller-644457c445-9rqmw    1/1     Running   0          33s
argocd-redis-6bcd6966f-8tdk9                        1/1     Running   0          33s
argocd-repo-server-6f6657d5cb-kfdwk                 1/1     Running   0          33s
argocd-server-664495b675-d2hz5                      1/1     Running   0          33s
```
(código de salida 0)

### la versión

`$ kubectl get deploy argocd-server -n argocd -o jsonpath=…image`

```
quay.io/argoproj/argocd:v3.5.5
```
(código de salida 0)

## 2 · Una aplicación que vive en Git

### lo que hay en el repositorio

`$ git log --oneline; ls web/`

```
f9409b8 web con 2 réplicas
ajustes.yaml
deploy.yaml
```
(código de salida 0)

### la Application (automatizada, con prune y selfHeal)

`$ kubectl apply -f app.yaml`

```
application.argoproj.io/web created
apiVersion: argoproj.io/v1alpha1
kind: Application
metadata: {name: web, namespace: argocd}
spec:
  project: default
  source: {repoURL: http://192.168.32.4:3000/lab/apps.git, targetRevision: main, path: web}
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
NAME                  READY   UP-TO-DATE   AVAILABLE   AGE
deployment.apps/web   2/2     2            2           6s

NAME                         DATA   AGE
configmap/ajustes            1      6s
configmap/kube-root-ca.crt   1      6s
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

### el historial de la aplicación

`$ kubectl get application web -n argocd -o jsonpath=…status.operationState`

```
successfully synced (all tasks run) · f9409b89210141656bece4b209389763e3bacbd4
```
(código de salida 0)

## 4 · Un commit en Git

### el commit

`$ git log --oneline | head -1`

```
171b4fa web con 3 réplicas
```
(código de salida 0)

> Con la configuración por defecto (sin webhook), el clúster pasó a 3 réplicas a los 358.0 s del push.

### intervalo de sondeo configurado

`$ kubectl get cm argocd-cm -n argocd -o jsonpath=…timeout.reconciliation`

```
timeout.reconciliation=
```
(código de salida 0)

> Vacío = valor por defecto de Argo CD.

## 5 · Se borra algo del repositorio

> prune: el ConfigMap desapareció del clúster a los 212.0 s del push.

### lo que queda

`$ kubectl get deploy,cm -n tienda`

```
NAME                  READY   UP-TO-DATE   AVAILABLE   AGE
deployment.apps/web   3/3     3            3           9m39s

NAME                         DATA   AGE
configmap/kube-root-ca.crt   1      9m39s
```
(código de salida 0)

## 6 · Lo que pesa

### contenedores de Argo CD

`$ kubectl get pods -n argocd --no-headers | wc -l`

```
7
```
(código de salida 0)
