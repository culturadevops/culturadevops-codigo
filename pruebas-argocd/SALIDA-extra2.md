# SALIDA (3.ª parte) — Argo CD, ApplicationSet (vídeo 408)

Generado 2026-10-13 20:53 UTC con `python correr_extra2.py`.

## 10 · Una carpeta nueva = una aplicación nueva

### las carpetas en Git

`$ ls equipos/`

```
envios
pagos
```
(código de salida 0)

### el ApplicationSet

`$ kubectl apply -f appset.yaml`

```
applicationset.argoproj.io/equipos created
      directories: [{path: "equipos/*"}]
  template:
    metadata: {name: "eq-{{.path.basename}}"}
```
(código de salida 0)

### las aplicaciones que generó

`$ kubectl get applications -n argocd`

```
NAME   SYNC STATUS   HEALTH STATUS
web    Synced        Healthy
```
(código de salida 0)

### añado una carpeta y hago push

`$ mkdir equipos/soporte … git push`

```
926a257 equipo soporte
```
(código de salida 0)

> La aplicación «eq-soporte» apareció, sincronizada y sana, a los 1.3 s (con aviso al ApplicationSet).

### y queda así

`$ kubectl get applications -n argocd`

```
NAME         SYNC STATUS   HEALTH STATUS
eq-envios    Synced        Healthy
eq-pagos     Synced        Healthy
eq-soporte   Synced        Healthy
web          Synced        Healthy
```
(código de salida 0)
