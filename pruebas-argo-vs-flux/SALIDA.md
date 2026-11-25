# SALIDA — Argo CD vs Flux (vídeo 335)

Generado 2026-10-07 23:08 UTC con `python correr.py`. k3s + Gitea en Docker; Argo CD (install.yaml de stable) y Flux (ghcr.io/fluxcd/flux-cli:v2.9.6).

## 1 · Laboratorio y repositorio

### el repo

`$ git log --oneline; ls`

```
b70a464 web: nginx con 1 réplica
configmap.yaml
deployment.yaml
service.yaml
```

## 2 · Instalar los dos

### Argo CD

`$ kubectl apply -n argocd --server-side -f https://raw.githubusercontent.com/argoproj/argo-cd/stable/manifests/install.yaml`

```
argocd-application-controller-0
argocd-applicationset-controller-587567d8c9-59rnt
argocd-dex-server-5f8dcd7cb9-d8qcn
argocd-notifications-controller-7495ff777d-tq97g
argocd-redis-869ffc4dd6-fvdlk
argocd-repo-server-855594f74d-667x6
argocd-server-6d9dd9f68-rn8ls
(listo en 43 s) · versión argocd: v3.5.4
```

### Flux

`$ flux install`

```
✚ generating manifests
✔ manifests build completed
✔ helm-controller: deployment ready
✔ kustomize-controller: deployment ready
✔ notification-controller: deployment ready
✔ source-controller: deployment ready
✔ install finished
helm-controller-7b787d5fdb-dwrpq
kustomize-controller-7494666f95-zdrct
notification-controller-7fc76bbdcc-4fvw5
source-controller-84db886d7f-862sh
(listo en 32 s)
```

### versión de Flux

`$ flux version`

```
flux: v2.9.6
distribution: flux-v2.9.6
helm-controller: v1.6.5
kustomize-controller: v1.9.6
notification-controller: v1.9.4
source-controller: v1.9.6
```

### memoria en reposo

`$ kubectl top pods -n argocd / -n flux-system`

```
NAME                                                CPU(cores)   MEMORY(bytes)   
argocd-application-controller-0                     1m           24Mi            
argocd-applicationset-controller-587567d8c9-59rnt   1m           22Mi            
argocd-dex-server-5f8dcd7cb9-d8qcn                  1m           20Mi            
argocd-notifications-controller-7495ff777d-tq97g    1m           21Mi            
argocd-redis-869ffc4dd6-fvdlk                       4m           5Mi             
argocd-repo-server-855594f74d-667x6                 1m           21Mi            
argocd-server-6d9dd9f68-rn8ls                       1m           41Mi

NAME                                       CPU(cores)   MEMORY(bytes)   
helm-controller-7b787d5fdb-dwrpq           1m           14Mi            
kustomize-controller-7494666f95-zdrct      1m           15Mi            
notification-controller-7fc76bbdcc-4fvw5   1m           21Mi            
source-controller-84db886d7f-862sh         1m           16Mi

Argo CD: 7 pods, 154 MiB · Flux: 4 pods, 66 MiB
```

### CRD que añade cada uno

`$ kubectl get crd | grep -c argoproj / toolkit.fluxcd`

```
argoproj.io: 3
toolkit.fluxcd.io: 11
```

## 3 · Conectar el repo (configuración de la guía oficial de cada uno)

### Argo CD: Application

`$ cat application.yaml`

```
apiVersion: argoproj.io/v1alpha1
kind: Application
metadata: {name: web, namespace: argocd}
spec:
  project: default
  source: {repoURL: http://10.78.0.20:3000/dev/app.git, targetRevision: main, path: .}
  destination: {server: https://kubernetes.default.svc, namespace: argo-app}
  syncPolicy:
    automated: {}
    syncOptions: [CreateNamespace=true]
```

### Flux: GitRepository + Kustomization

`$ cat flux.yaml`

```
apiVersion: source.toolkit.fluxcd.io/v1
kind: GitRepository
metadata: {name: app, namespace: flux-system}
spec:
  interval: 1m
  url: http://10.78.0.20:3000/dev/app.git
  ref: {branch: main}
---
apiVersion: kustomize.toolkit.fluxcd.io/v1
kind: Kustomization
metadata: {name: web, namespace: flux-system}
spec:
  interval: 30m
  prune: true
  sourceRef: {kind: GitRepository, name: app}
  path: ./
  targetNamespace: flux-app
```

### primera sincronización

`$ kubectl get deploy web -n argo-app / -n flux-app`

```
Argo CD: web listo a los 11 s
Flux:    web listo a los 12 s
```

### estado según cada uno

`$ kubectl get application -n argocd; flux get kustomizations`

```
NAME   SYNC STATUS   HEALTH STATUS
web    Synced        Healthy

NAMESPACE  	NAME	REVISION          	SUSPENDED	READY	MESSAGE                              
flux-system	web 	main@sha1:b70a464f	False    	True 	Applied revision: main@sha1:b70a464f
```

## 4 · Un push: ¿cuánto tarda cada uno?

### el cambio

`$ git commit -m 'web: 3 réplicas' && git push`

```
commit 0267e91 a las 22:57:07 UTC
```

### ¿cuándo llegó a cada clúster?

`$ réplicas en argo-app / flux-app, cada 2 s`

```
Argo CD: 307 s
Flux:    49 s
```

## 5 · Borrar un manifiesto en Git

### ¿sigue el ConfigMap?

`$ kubectl get cm web-config -n argo-app / -n flux-app`

```
Argo CD (automated sin prune): sigue ahí a los 200 s
  Synced
Flux (prune: true de la guía):  borrado a los 44 s
```

## 6 · Alguien cambia el clúster a mano

### kubectl scale --replicas=1 en los dos y mirar 3 min

`$ réplicas cada 30 s`

```
t=   0s  argo-app=3  flux-app=1
t=  30s  argo-app=3  flux-app=1
t=  61s  argo-app=3  flux-app=1
t=  91s  argo-app=3  flux-app=1
t= 122s  argo-app=3  flux-app=1
t= 152s  argo-app=3  flux-app=1
```

### Flux: forzar la reconciliación

`$ flux reconcile kustomization web`

```
► annotating Kustomization web in flux-system namespace
✔ Kustomization annotated
◎ waiting for Kustomization reconciliation
✔ applied revision main@sha1:b08dfbe75e9dc2cf793c34e36780d0a5589c7cba
flux-app=3 (4 s)
```

### Argo CD: activar selfHeal

`$ syncPolicy.automated.selfHeal: true`

```
argo-app=3 (0 s)
```

## 7 · Ver el estado

### Flux desde la terminal

`$ flux get all -A`

```
NAMESPACE  	NAME             	REVISION          	SUSPENDED	READY	MESSAGE                                           
flux-system	gitrepository/app	main@sha1:b08dfbe7	False    	True 	stored artifact for revision 'main@sha1:b08dfbe7'	

NAMESPACE  	NAME             	REVISION          	SUSPENDED	READY	MESSAGE                              
flux-system	kustomization/web	main@sha1:b08dfbe7	False    	True 	Applied revision: main@sha1:b08dfbe7
```

### eventos de Flux

`$ flux events -A | tail`

```
flux-system	6m52s (x4 over 9m55s)	Normal	GitOperationSucceeded     	GitRepository/app	no changes since last reconciliation: observed revision 'main@sha1:0267e91d9a1a4fec2578bd6e5e5ba9751f827e7a'	
flux-system	5m50s                	Normal	ReconciliationSucceeded   	Kustomization/web	Reconciliation finished in 104.644575ms, next run in 30m0s                                                  	
flux-system	5m50s                	Normal	Progressing               	Kustomization/web	ConfigMap/flux-app/web-config deleted                                                                       	
flux-system	5m50s                	Normal	NewArtifact               	GitRepository/app	stored artifact for commit 'quitar web-config'                                                              	
flux-system	4m47s (x2 over 9m55s)	Normal	GarbageCollectionSucceeded	GitRepository/app	garbage collected 1 artifacts                                                                               	
flux-system	51s (x5 over 4m47s)  	Normal	GitOperationSucceeded     	GitRepository/app	no changes since last reconciliation: observed revision 'main@sha1:b08dfbe75e9dc2cf793c34e36780d0a5589c7cba'	
flux-system	9s (x2 over 10m)     	Normal	Progressing               	Kustomization/web	Deployment/flux-app/web configured                                                                          	
flux-system	9s                   	Normal	ReconciliationSucceeded   	Kustomization/web	Reconciliation finished in 83.505211ms, next run in 30m0s
```
