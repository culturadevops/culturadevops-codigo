# SALIDA (2.ª parte) — Argo CD (vídeo 408)

Generado 2026-10-13 20:52 UTC con `python correr_extra.py`, sobre el laboratorio de correr.py.

## 7 · Un commit con aviso inmediato (lo que hace un webhook)

### el commit

`$ git log --oneline | head -1`

```
85659ff web con 4 réplicas
```
(código de salida 0)

### pedir a Argo CD que mire ya

`$ kubectl annotate application web -n argocd argocd.argoproj.io/refresh=normal`

> Con el aviso, el clúster pasó a 4 réplicas a los 1.2 s (sin aviso, en la 1.ª parte: 358 s).

## 8 · Un commit roto

### el commit

`$ git log --oneline | head -1`

```
8974753 imagen que no existe
```
(código de salida 0)

> A los 2.3 s Argo CD ya marcaba la aplicación como no sana.

### el estado de la aplicación

`$ kubectl get application web -n argocd`

```
NAME   SYNC STATUS   HEALTH STATUS
web    Synced        Progressing
```
(código de salida 0)

### y los pods

`$ kubectl get pods -n tienda`

```
web-758bd78b4-dxvng Running
web-758bd78b4-j886s Running
web-758bd78b4-tpcvd Running
web-b76dfc678-2c8rw ImagePullBackOff
web-b76dfc678-9knpq ImagePullBackOff
```
(código de salida 0)

## 9 · Volver atrás: git revert

### revertir el commit

`$ git revert --no-edit HEAD && git push`

```
d412831 Revert "imagen que no existe"
8974753 imagen que no existe
```
(código de salida 0)

> Synced y Healthy otra vez a los 1.2 s del revert (con aviso).

### el estado

`$ kubectl get application web -n argocd`

```
NAME   SYNC STATUS   HEALTH STATUS
web    Synced        Healthy
```
(código de salida 0)
