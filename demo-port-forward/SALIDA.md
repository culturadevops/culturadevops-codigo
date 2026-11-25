# SALIDA — kubectl port-forward (cultura-devops)

> Corrida del 2026-10-20 16:43. Kubernetes de un nodo con k3s (rancher/k3s:v1.37.1-k3s1) dentro de Docker; kubectl v1.37.1+k3s1.

```
### 1 · Los pods y el Service: sin IP de fuera
$ kubectl get pods,svc
POD                   ESTADO    IP
web-c47cd8d45-6hdx7   Running   10.42.0.7
web-c47cd8d45-g68lm   Running   10.42.0.6
SERVICE   TIPO        PUERTO
web       ClusterIP   80

### 2 · port-forward a un pod
$ kubectl port-forward pod/web-c47cd8d45-6hdx7 8080:8080 &
Forwarding from 127.0.0.1:8080 -> 8080
Forwarding from [::1]:8080 -> 8080
$ wget -qO- localhost:8080
hola desde web-c47cd8d45-6hdx7
(lo que imprime port-forward)
Forwarding from 127.0.0.1:8080 -> 8080
Forwarding from [::1]:8080 -> 8080
Handling connection for 8080

### 3 · El puerto ya está ocupado
$ kubectl port-forward pod/web-c47cd8d45-6hdx7 8080:8080
Unable to listen on port 8080: Listeners failed to create with the following errors: [unable to create listener: Error listen tcp4 127.0.0.1:8080: bind: address already in use unable to create listener: Error listen tcp6 [::1]:8080: bind: address already in use]
error: unable to listen on any of the requested ports: [{8080 8080}]
$ kubectl port-forward pod/web-c47cd8d45-6hdx7 :8080   # puerto local al azar
Forwarding from 127.0.0.1:34159 -> 8080
Forwarding from [::1]:34159 -> 8080

### 4 · Solo escucha en 127.0.0.1
$ wget -qO- 172.17.0.3:8080   # desde la IP de la máquina, no localhost
wget: can't connect to remote host (172.17.0.3): Connection refused
$ kubectl port-forward --address 0.0.0.0 pod/web-c47cd8d45-6hdx7 8081:8080 &
Forwarding from 0.0.0.0:8081 -> 8080
$ wget -qO- 172.17.0.3:8081
hola desde web-c47cd8d45-6hdx7

### 5 · port-forward a un Service: elige UN pod y se queda con él
$ kubectl port-forward svc/web 9090:80 &
Forwarding from 127.0.0.1:9090 -> 8080
Forwarding from [::1]:9090 -> 8080
$ for i in 1 2 3 4 5 6; do wget -qO- localhost:9090; done
hola desde web-c47cd8d45-6hdx7
hola desde web-c47cd8d45-6hdx7
hola desde web-c47cd8d45-6hdx7
hola desde web-c47cd8d45-6hdx7
hola desde web-c47cd8d45-6hdx7
hola desde web-c47cd8d45-6hdx7
$ kubectl run prueba --rm -i --image=busybox:1.37 --restart=Never -- sh -c 'for i in 1 2 3 4 5 6; do wget -qO- web; done'   # desde dentro del clúster
hola desde web-c47cd8d45-g68lm
hola desde web-c47cd8d45-6hdx7
hola desde web-c47cd8d45-6hdx7
hola desde web-c47cd8d45-6hdx7
hola desde web-c47cd8d45-g68lm
hola desde web-c47cd8d45-6hdx7

### 6 · Si el pod muere, el túnel se rompe
$ kubectl delete pod web-c47cd8d45-6hdx7
pod "web-c47cd8d45-6hdx7" deleted from demo namespace
$ wget -qO- localhost:8080
wget: error getting response: Invalid argument
(lo que imprime port-forward)
Handling connection for 8080
E1020 21:44:34.547719    1346 portforward.go:549] "An error occurred forwarding" err="error forwarding port 8080 to pod fc15429aa08d53e6264c86900b5e4a0d2396166b2c81c373996aebf06f2d365f, uid : failed to find sandbox \"fc15429aa08d53e6264c86900b5e4a0d2396166b2c81c373996aebf06f2d365f\" in store: not found" localPort=8080 remotePort=8080
error: lost connection to pod
$ jobs   # ¿sigue vivo el port-forward?
terminó
$ kubectl get pods
POD                   ESTADO
web-c47cd8d45-5nxz4   Running
web-c47cd8d45-g68lm   Running
```
