# SALIDA — Curso de Kubernetes 2027 · Parte 3: Service

> Corrida del 2026-11-22 19:11. kind v0.30.0, clúster k8s-a (1 plano de control + 2 workers), kindest/node:v1.34.0, kube-proxy en modo iptables.
> Imágenes ya descargadas en los nodos. Contenedores ajenos vivos al empezar: k8s-b-control-plane k8s-b-worker k8s-b-worker2 
> Nodos en la red kind: control-plane 192.168.48.5 · worker 192.168.48.7 · worker2 192.168.48.6

```

### 1 · Tres pods y un Service ClusterIP
$ kubectl apply -f 1-web.yaml
deployment.apps/web created
service/web created
pod/cliente created
$ kubectl get pods -l app=web -o wide
NAME READY STATUS IP NODE
web-7c7cbbb544-4lvdz 1/1 Running 10.244.2.55 k8s-a-worker2
web-7c7cbbb544-kx7m9 1/1 Running 10.244.1.55 k8s-a-worker
web-7c7cbbb544-v252f 1/1 Running 10.244.2.56 k8s-a-worker2
$ kubectl get service web
NAME   TYPE        CLUSTER-IP     EXTERNAL-IP   PORT(S)   AGE
web    ClusterIP   10.96.163.17   <none>        80/TCP    2s
$ kubectl get endpointslices -l kubernetes.io/service-name=web
NAME        ADDRESSTYPE   PORTS   ENDPOINTS                             AGE
web-ngshz   IPv4          80      10.244.1.55,10.244.2.56,10.244.2.55   2s
$ kubectl get endpointslices -l kubernetes.io/service-name=web -o jsonpath='{range .items[*].endpoints[*]}{.addresses[0]} {.targetRef.name} ready={.conditions.ready}{"\n"}{end}'
10.244.1.55 web-7c7cbbb544-kx7m9 ready=true
10.244.2.56 web-7c7cbbb544-v252f ready=true
10.244.2.55 web-7c7cbbb544-4lvdz ready=true

### 2 · La ClusterIP no es una máquina: es una regla
$ kubectl exec cliente -- wget -qO- http://10.96.163.17
web-7c7cbbb544-4lvdz
$ kubectl exec cliente -- ping -c 2 -W 1 10.96.163.17
2 packets transmitted, 0 packets received, 100% packet loss
command terminated with exit code 1
$ iptables-save -t nat | grep 'parte3/web cluster IP'   # en cualquier nodo
-A KUBE-SERVICES -d 10.96.163.17/32 -p tcp -m tcp --dport 80 -j KUBE-SVC-6EITWBLFOKIGD2WH
$ iptables-save -t nat | grep -- '-A KUBE-SVC-6EITWBLFOKIGD2WH'
-A KUBE-SVC-6EITWBLFOKIGD2WH -m statistic --mode random --probability 0.33333333349 -j KUBE-SEP-AKFIKECSQWTTD2GP
-A KUBE-SVC-6EITWBLFOKIGD2WH -m statistic --mode random --probability 0.50000000000 -j KUBE-SEP-MM6VH5QKLFSOEYOR
-A KUBE-SVC-6EITWBLFOKIGD2WH -j KUBE-SEP-KWQ7RN5ZDLAMU4SV

### 3 · Reparto: 300 peticiones al Service
$ kubectl exec cliente -- sh -c 'for i in $(seq 300); do wget -qO- http://web; done | sort | uniq -c'
    112 web-7c7cbbb544-4lvdz
     98 web-7c7cbbb544-kx7m9
     90 web-7c7cbbb544-v252f

### 4 · DNS interno
$ kubectl exec cliente -- cat /etc/resolv.conf
search parte3.svc.cluster.local svc.cluster.local cluster.local
nameserver 10.96.0.10
options ndots:5
$ kubectl exec cliente -- nslookup web.parte3.svc.cluster.local
Name:	web.parte3.svc.cluster.local
Address: 10.96.163.17

$ kubectl exec cliente -- wget -qO- http://web   # nombre corto, mismo namespace
web-7c7cbbb544-kx7m9
$ kubectl exec -n otro vecino -- wget -qO- http://web   # desde OTRO namespace
wget: bad address 'web'
command terminated with exit code 1
$ kubectl exec -n otro vecino -- wget -qO- http://web.parte3
web-7c7cbbb544-4lvdz

### 5 · Un pod deja de estar Ready (readinessProbe), medido
$ kubectl exec web-7c7cbbb544-4lvdz -- rm /usr/share/nginx/html/listo.html   # periodSeconds 2, failureThreshold 3
rm listo.html en web-7c7cbbb544-4lvdz: a los 3002 ms · touch listo.html: a los 23086 ms
EndpointSlice (cambios de ready de web-7c7cbbb544-4lvdz):
  28 web-7c7cbbb544-4lvdz=true
  7433 web-7c7cbbb544-4lvdz=false
  23381 web-7c7cbbb544-4lvdz=true
última respuesta de web-7c7cbbb544-4lvdz tras el rm: 7269 ms (4267 ms después del rm)
primera respuesta de web-7c7cbbb544-4lvdz tras el touch: 23381 ms (295 ms después del touch)
peticiones totales: 1728 · errores: 0
reparto entre 11002 y 23086 ms (pod caído): web-7c7cbbb544-v252f=220 web-7c7cbbb544-kx7m9=242
$ kubectl get pod web-7c7cbbb544-4lvdz   # durante la caída (otra vez sin listo.html 8 s)
NAME                   READY   STATUS    RESTARTS   AGE
web-7c7cbbb544-4lvdz   0/1     Running   0          74s
$ kubectl get endpointslices -l kubernetes.io/service-name=web -o jsonpath='…{.targetRef.name} ready={.conditions.ready} serving={.conditions.serving}…'
web-7c7cbbb544-kx7m9 ready=true serving=true
web-7c7cbbb544-v252f ready=true serving=true
web-7c7cbbb544-4lvdz ready=false serving=false

### 6 · Un selector que no casa con nada
$ kubectl apply -f 5-sin-pods.yaml
service/web-mal created
$ kubectl get endpointslices -l kubernetes.io/service-name=web-mal
NAME            ADDRESSTYPE   PORTS     ENDPOINTS   AGE
web-mal-55jv8   IPv4          <unset>   <unset>     2s
$ kubectl exec cliente -- wget -qO- http://web-mal
wget: can't connect to remote host (10.96.122.27): Connection refused
command terminated with exit code 1

### 7 · NodePort: el mismo puerto en TODOS los nodos
$ kubectl apply -f 2-nodeport.yaml
service/web-nodeport created
$ kubectl get service web-nodeport
NAME           TYPE       CLUSTER-IP      EXTERNAL-IP   PORT(S)        AGE
web-nodeport   NodePort   10.96.176.133   <none>        80:30080/TCP   0s
$ kubectl get pods -l app=web -o wide   # una sola réplica
NAME STATUS NODE
web-7c7cbbb544-kx7m9 Running k8s-a-worker
$ docker run --rm --network kind busybox:1.37 wget -qO- http://192.168.48.5:30080   # nodo control-plane
web-7c7cbbb544-kx7m9
$ docker run --rm --network kind busybox:1.37 wget -qO- http://192.168.48.7:30080   # nodo worker
web-7c7cbbb544-kx7m9
$ docker run --rm --network kind busybox:1.37 wget -qO- http://192.168.48.6:30080   # nodo worker2
web-7c7cbbb544-kx7m9
$ kubectl patch service web-nodeport -p '{"spec":{"externalTrafficPolicy":"Local"}}'
service/web-nodeport patched
$ docker run --rm --network kind busybox:1.37 wget -qO- -T 3 http://192.168.48.5:30080   # nodo control-plane, Local
wget: download timed out
$ docker run --rm --network kind busybox:1.37 wget -qO- -T 3 http://192.168.48.7:30080   # nodo worker, Local
web-7c7cbbb544-kx7m9
$ docker run --rm --network kind busybox:1.37 wget -qO- -T 3 http://192.168.48.6:30080   # nodo worker2, Local
wget: download timed out

### 8 · LoadBalancer en kind
$ kubectl apply -f 3-loadbalancer.yaml
service/web-lb created
$ kubectl get service web-lb   # 20 s después, sin proveedor de nube
NAME     TYPE           CLUSTER-IP    EXTERNAL-IP   PORT(S)        AGE
web-lb   LoadBalancer   10.96.10.15   <pending>     80:31453/TCP   20s
$ docker run -d --name k8s-a-cpk --network kind -v /var/run/docker.sock:/var/run/docker.sock registry.k8s.io/cloud-provider-kind/cloud-controller-manager:v0.12.0 --gateway-channel disabled --enable-default-ingress=false
(IP externa asignada 10039 ms después de arrancar cloud-provider-kind; incluye bajar su imagen de Envoy si no estaba)
$ kubectl get service web-lb
NAME     TYPE           CLUSTER-IP    EXTERNAL-IP    PORT(S)        AGE
web-lb   LoadBalancer   10.96.10.15   192.168.48.9   80:31453/TCP   30s
$ docker ps --filter label=io.x-k8s.cloud-provider-kind.cluster=k8s-a --format '{{.Names}} {{.Image}}'
kindccm-e32f071ae026 envoyproxy/envoy:v1.33.2
kindccm-48ac4abbc77d envoyproxy/envoy:v1.33.2
kindccm-e32f071ae026 envoyproxy/envoy:v1.33.2
$ docker run --rm --network kind busybox:1.37 sh -c 'for i in $(seq 30); do wget -qO- http://192.168.48.9; done | sort | uniq -c'
      9 web-7c7cbbb544-hzphx
      7 web-7c7cbbb544-kx7m9
     14 web-7c7cbbb544-s9msz
$ curl -m 5 http://192.168.48.9   # desde Windows, fuera de la red kind
000
(sin respuesta en 5 s)

### 9 · Headless: sin ClusterIP, el DNS da las IP de los pods
$ kubectl apply -f 4-headless.yaml
service/web-headless created
Warning: spec.SessionAffinity is ignored for headless services
$ kubectl get service web web-headless
NAME           TYPE        CLUSTER-IP     EXTERNAL-IP   PORT(S)   AGE
web            ClusterIP   10.96.163.17   <none>        80/TCP    2m23s
web-headless   ClusterIP   None           <none>        80/TCP    4s
$ kubectl exec cliente -- nslookup web-headless.parte3.svc.cluster.local
Address:	10.96.0.10:53
Address: 10.244.1.55
Address: 10.244.1.57
Address: 10.244.2.58
$ kubectl get pods -l app=web -o custom-columns=POD:.metadata.name,IP:.status.podIP
POD                    IP
web-7c7cbbb544-hzphx   10.244.2.58
web-7c7cbbb544-kx7m9   10.244.1.55
web-7c7cbbb544-s9msz   10.244.1.57

### 10 · Limpieza del LoadBalancer
contenedores de cloud-provider-kind que quedan: 
```

> Contenedores ajenos vivos al terminar: k8s-b-control-plane k8s-b-worker k8s-b-worker2 
