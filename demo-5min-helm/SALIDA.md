# SALIDA — Helm en 5 minutos (cultura-devops)

Generado 2026-10-23 12:36 UTC con `python correr.py`. k3s `rancher/k3s:v1.37.1-k3s1` en Docker; helm v4.3.1 y kubectl v1.37.1 en un contenedor Alpine.

## 1 · Versiones

### helm y el clúster

`$ helm version --short; kubectl get nodes`

```
v4.3.1+gc0d08d0
NAME   STATUS   ROLES           AGE   VERSION
k3s5   Ready    control-plane   7s    v1.37.1+k3s1
```
(código de salida 0)

## 2 · Un chart

### helm create tienda

`$ helm create tienda; find tienda -maxdepth 2 | sort`

```
tienda
tienda/.helmignore
tienda/Chart.yaml
tienda/charts
tienda/templates
tienda/templates/NOTES.txt
tienda/templates/_helpers.tpl
tienda/templates/deployment.yaml
tienda/templates/hpa.yaml
tienda/templates/httproute.yaml
tienda/templates/ingress.yaml
tienda/templates/service.yaml
tienda/templates/serviceaccount.yaml
tienda/templates/tests
tienda/values.yaml
```
(código de salida 0)

### lo que se puede cambiar (values.yaml)

`$ grep -E -A3 '^replicaCount|^image:' tienda/values.yaml`

```
replicaCount: 1

image:
  repository: nginx
  pullPolicy: IfNotPresent
```
(código de salida 0)

### y la versión de la app

`$ grep appVersion tienda/Chart.yaml`

```
appVersion: "1.16.0"
```
(código de salida 0)

## 3 · Instalar, actualizar, romper y volver atrás

### instalar

`$ helm install tienda ./tienda --set image.tag=1.31-alpine --wait`

```
NAME: tienda
NAMESPACE: default
STATUS: deployed
REVISION: 1
```
(código de salida 0)

### lo que creó

`$ kubectl get deploy,svc -l app.kubernetes.io/instance=tienda`

```
NAME                     READY   UP-TO-DATE   AVAILABLE   AGE
deployment.apps/tienda   1/1     1            1           7s

NAME             TYPE        CLUSTER-IP      EXTERNAL-IP   PORT(S)   AGE
service/tienda   ClusterIP   10.43.113.199   <none>        80/TCP    8s
```
(código de salida 0)

### actualizar: 3 réplicas

`$ helm upgrade tienda ./tienda --reuse-values --set replicaCount=3 --wait`

```
STATUS: deployed
REVISION: 2
NAME     READY   UP-TO-DATE   AVAILABLE   AGE
tienda   3/3     3            3           9s
```
(código de salida 0)

### una versión que no existe

`$ helm upgrade tienda ./tienda --reuse-values --set image.tag=no-existe --wait --timeout 40s`

```
Error: UPGRADE FAILED: resource Deployment/default/tienda not ready. status: InProgress, message: Updated: 1/3
context deadline exceeded
```
(código de salida 0)

### ¿y los pods?

`$ kubectl get pods -l app.kubernetes.io/instance=tienda`

```
POD                       ESTADO         LISTO
tienda-5d698dfd6d-fwk4k   <none>         true
tienda-5d698dfd6d-pflsn   <none>         true
tienda-5d698dfd6d-s8pql   <none>         true
tienda-677d64954f-fdfp9   ErrImagePull   false
```
(código de salida 0)

### el historial

`$ helm history tienda`

```
REVISION	UPDATED                 	STATUS    	CHART       	APP VERSION	DESCRIPTION                                                                                                     
1       	Fri Oct 23 12:36:28 2026	superseded	tienda-0.1.0	1.16.0     	Install complete                                                                                                
2       	Fri Oct 23 12:36:36 2026	deployed  	tienda-0.1.0	1.16.0     	Upgrade complete                                                                                                
3       	Fri Oct 23 12:36:38 2026	failed    	tienda-0.1.0	1.16.0     	Upgrade "tienda" failed: resource Deployment/default/tienda not ready. status: InProgress, message: Updated: ...
```
(código de salida 0)

### volver a la revisión 2

`$ helm rollback tienda 2 --wait`

```
Rollback was a success! Happy Helming!
NAME     READY   UP-TO-DATE   AVAILABLE   AGE
tienda   3/3     3            3           50s
imagen: nginx:1.31-alpine
```
(código de salida 0)

### el historial después

`$ helm history tienda`

```
REVISION	UPDATED                 	STATUS    	CHART       	APP VERSION	DESCRIPTION                                                                                                     
1       	Fri Oct 23 12:36:28 2026	superseded	tienda-0.1.0	1.16.0     	Install complete                                                                                                
2       	Fri Oct 23 12:36:36 2026	superseded	tienda-0.1.0	1.16.0     	Upgrade complete                                                                                                
3       	Fri Oct 23 12:36:38 2026	failed    	tienda-0.1.0	1.16.0     	Upgrade "tienda" failed: resource Deployment/default/tienda not ready. status: InProgress, message: Updated: ...
4       	Fri Oct 23 12:37:18 2026	deployed  	tienda-0.1.0	1.16.0     	Rollback to 2
```
(código de salida 0)

### y borrar todo

`$ helm uninstall tienda; kubectl get all -l app.kubernetes.io/instance=tienda`

```
release "tienda" uninstalled
NAME                          READY   STATUS      RESTARTS   AGE
pod/tienda-5d698dfd6d-fwk4k   0/1     Completed   0          43s
pod/tienda-5d698dfd6d-pflsn   0/1     Completed   0          43s
pod/tienda-5d698dfd6d-s8pql   0/1     Completed   0          50s
```
(código de salida 0)
