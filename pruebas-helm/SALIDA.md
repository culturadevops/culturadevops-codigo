# SALIDA — Helm 3 contra Helm 4 (vídeo 407)

Generado 2026-10-13 20:25 UTC con `python correr.py`. Clúster k3s en Docker; Helm y kubectl dentro de un contenedor Alpine.

## 1 · Versiones

### las dos versiones

`$ helm3 version; helm4 version`

```
v3.22.0+g144ca65
v4.3.0+gbec5b06
```
(código de salida 0)

### el clúster

`$ kubectl get nodes`

```
NAME           STATUS   ROLES           AGE     VERSION
9661ad1d2c2d   Ready    control-plane   2m17s   v1.34.1+k3s1
```
(código de salida 0)

## 2 · Empaquetar el mismo chart dos veces

### Helm 3: dos paquetes, ¿mismo hash?

`$ helm3 package demo (dos veces); sha256sum`

```
55fa71f9b07c30eb141099c7753c0382d1b3ef808f913b0d7110ca3cbd256b7e  p3a/demo-0.1.0.tgz
4f74f29a11237be74e2a2a59acab5324dafcf4c81300e06545916de4639e1e61  p3b/demo-0.1.0.tgz
```
(código de salida 0)

### Helm 4: lo mismo

`$ helm4 package demo (dos veces); sha256sum`

```
59d7fb4858782171ebc57b5205d80175003345614f7a4651ec7a88e771c6fa8b  p4a/demo-0.1.0.tgz
59d7fb4858782171ebc57b5205d80175003345614f7a4651ec7a88e771c6fa8b  p4b/demo-0.1.0.tgz
```
(código de salida 0)

## 3 · Instalar el mismo chart

### Helm 3

`$ helm3 install web3 ./demo -n h3 --create-namespace --wait`

```
STATUS: deployed
```
(código de salida 0)

### Helm 4

`$ helm4 install web4 ./demo -n h4 --create-namespace --wait`

```
STATUS: deployed
```
(código de salida 0)

### quién gestiona los campos (Helm 3)

`$ kubectl get deploy -n h3 -o jsonpath=…managedFields`

```
helm Update
k3s Update
```
(código de salida 0)

### quién gestiona los campos (Helm 4)

`$ kubectl get deploy -n h4 -o jsonpath=…managedFields`

```
helm Apply
k3s Update
```
(código de salida 0)

## 4 · Alguien toca el clúster a mano

### escalar a 3 réplicas con kubectl

`$ kubectl scale deploy --replicas=3 (en h3 y h4)`

```
deployment.apps/web3-demo scaled
deployment.apps/web4-demo scaled
```
(código de salida 0)

### Helm 3: upgrade sin cambiar nada

`$ helm3 upgrade web3 ./demo -n h3; réplicas`

```
código 0
réplicas=1
```
(código de salida 0)

### Helm 4: upgrade sin cambiar nada

`$ helm4 upgrade web4 ./demo -n h4; réplicas`

```
código 1
Error: UPGRADE FAILED: conflict occurred while applying object h4/web4-demo apps/v1, Kind=Deployment: Apply failed with 1 conflict: conflict with "kubectl" with subresource "scale" using apps/v1: .spec.replicas
réplicas=3
```
(código de salida 0)

### Helm 4: upgrade con --force-conflicts

`$ helm4 upgrade web4 ./demo -n h4 --force-conflicts; réplicas`

```
código 0
réplicas=1
```
(código de salida 0)

## 5 · Lo que guarda Helm del despliegue

### historial

`$ helm4 history web4 -n h4`

```
REVISION	UPDATED                 	STATUS    	CHART     	APP VERSION	DESCRIPTION                                                                                                                                                                                                       
1       	Tue Oct 13 20:25:47 2026	superseded	demo-0.1.0	1.16.0     	Install complete                                                                                                                                                                                                  
2       	Tue Oct 13 20:25:51 2026	failed    	demo-0.1.0	1.16.0     	Upgrade "web4" failed: conflict occurred while applying object h4/web4-demo apps/v1, Kind=Deployment: Apply failed with 1 conflict: conflict with "kubectl" with subresource "scale" using apps/v1: .spec.replicas
3       	Tue Oct 13 20:25:51 2026	deployed  	demo-0.1.0	1.16.0     	Upgrade complete
```
(código de salida 0)

### dónde lo guarda

`$ kubectl get secrets -n h4 -l owner=helm`

```
NAME                         TYPE                 DATA   AGE
sh.helm.release.v1.web4.v1   helm.sh/release.v1   1      5s
sh.helm.release.v1.web4.v2   helm.sh/release.v1   1      1s
sh.helm.release.v1.web4.v3   helm.sh/release.v1   1      1s
```
(código de salida 0)

### volver atrás

`$ helm4 rollback web4 1 -n h4`

```
Rollback was a success! Happy Helming!
3       	Tue Oct 13 20:25:51 2026	superseded	demo-0.1.0	1.16.0     	Upgrade complete                                                                                                                                                                                                  
4       	Tue Oct 13 20:25:52 2026	deployed  	demo-0.1.0	1.16.0     	Rollback to 1
```
(código de salida 0)

## 6 · La alternativa que ya viene en kubectl

### kustomize dentro de kubectl

`$ kubectl version --client; kubectl kustomize --help | head -3`

```
Client Version: v1.34.1
Kustomize Version: v5.7.1
Build a set of KRM resources using a 'kustomization.yaml' file. The DIR argument must be a path to a directory containing 'kustomization.yaml', or a git repository URL with a path suffix specifying same with respect to the repository root. If DIR is omitted, '.' is assumed.

Examples:
```
(código de salida 0)
