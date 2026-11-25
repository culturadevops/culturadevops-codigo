# SALIDA — Kubernetes en 5 minutos (cultura-devops)

> Corrida del 2026-10-19 17:32. Kubernetes de un nodo con k3s (rancher/k3s:v1.37.1-k3s1) dentro de Docker.

```
$ kubectl version
Server Version: v1.37.1+k3s1
$ kubectl get nodes
NOMBRE         ESTADO
b51738f9f70c   Ready

$ kubectl apply -f app.yaml
deployment.apps/web created
service/web created
$ kubectl get deployment web
NAME   READY   UP-TO-DATE   AVAILABLE   AGE
web    3/3     3            3           8s
$ kubectl get pods -l app=web
POD                   ESTADO
web-d489c9cb5-5lrnt   Running
web-d489c9cb5-pzmvr   Running
web-d489c9cb5-s8nks   Running

$ kubectl delete pod web-d489c9cb5-5lrnt   # matar uno a propósito
pod "web-d489c9cb5-5lrnt" deleted from default namespace
$ kubectl get pods -l app=web
POD                   ESTADO
web-d489c9cb5-jqspr   Running
web-d489c9cb5-pzmvr   Running
web-d489c9cb5-s8nks   Running

$ kubectl scale deployment web --replicas=5
deployment.apps/web scaled
$ kubectl get deployment web
NAME   READY   UP-TO-DATE   AVAILABLE   AGE
web    5/5     5            5           15s

$ kubectl get service web
NOMBRE   TIPO        PUERTO
web      ClusterIP   80
$ kubectl run prueba --rm -i --image=busybox:1.37 --restart=Never -- wget -qO- http://web | grep title
<title>Welcome to nginx!</title>
<title>Welcome to nginx!</title>
```
