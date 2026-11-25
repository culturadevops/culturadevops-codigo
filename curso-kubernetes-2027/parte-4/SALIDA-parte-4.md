# SALIDA — Curso de Kubernetes 2027 · Parte 4: Ingress y Gateway API

> Corrida del 2026-11-22 19:19. kind v0.30.0, clúster k8s-a (1 plano de control + 2 workers), kindest/node:v1.34.0.
> ingress-nginx controller-v1.15.1 · Envoy Gateway v1.10.0 (Gateway API v1.6.1) · cloud-provider-kind v0.12.0 · curl 8.17.0
> Contenedores ajenos vivos al empezar: k8s-b-control-plane k8s-b-worker k8s-b-worker2 

```

### 1 · Cuatro aplicaciones y un certificado
$ kubectl apply -f 1-apps.yaml
deployment.apps/tienda created
service/tienda created
deployment.apps/blog created
service/blog created
deployment.apps/api created
service/api created
deployment.apps/api-v2 created
service/api-v2 created
NAME     READY   UP-TO-DATE   AVAILABLE   AGE
api      1/1     1            1           2s
api-v2   1/1     1            1           2s
blog     1/1     1            1           2s
tienda   1/1     1            1           2s
$ openssl req -x509 -newkey rsa:2048 -nodes -days 30 -subj '/CN=*.ejemplo.test' -addext 'subjectAltName=DNS:*.ejemplo.test' -keyout tls.key -out tls.crt
(certificado autofirmado generado)
$ kubectl create secret tls tls-ejemplo --cert=tls.crt --key=tls.key
secret/tls-ejemplo created

### 2 · ingress-nginx (el controlador que se retiró)
$ kubectl apply -f ingress-nginx-controller-v1.15.1-kind.yaml
job.batch/ingress-nginx-admission-patch created
ingressclass.networking.k8s.io/nginx created
validatingwebhookconfiguration.admissionregistration.k8s.io/ingress-nginx-admission created
(controlador listo 12403 ms después del apply; imagen ya bajada en una corrida anterior)
$ kubectl get pods -n ingress-nginx -l app.kubernetes.io/component=controller -o custom-columns=POD:.metadata.name,NODO:.spec.nodeName,IMAGEN:.spec.containers[0].image
POD                                       NODO           IMAGEN
ingress-nginx-controller-f5784567-h8rnm   k8s-a-worker   registry.k8s.io/ingress-nginx/controller:v1.15.1
(el controlador usa hostPort 80/443 en k8s-a-worker = 192.168.48.7 dentro de la red kind)
$ kubectl get ingressclass
NAME    CONTROLLER             PARAMETERS   AGE
nginx   k8s.io/ingress-nginx   <none>       13s

### 3 · Un Ingress: por host y por ruta, con TLS
$ kubectl apply -f 2-ingress.yaml
ingress.networking.k8s.io/entrada created
$ kubectl get ingress entrada
NAME      CLASS   HOSTS                                   ADDRESS     PORTS     AGE
entrada   nginx   tienda.ejemplo.test,blog.ejemplo.test   localhost   80, 443   44s
$ curl -sk --resolve tienda.ejemplo.test:443:192.168.48.7 https://tienda.ejemplo.test/
soy tienda
$ curl -sk --resolve tienda.ejemplo.test:443:192.168.48.7 https://tienda.ejemplo.test/api/pedidos
soy api v1
$ curl -sk --resolve blog.ejemplo.test:443:192.168.48.7 https://blog.ejemplo.test/
soy blog
$ curl -s -o /dev/null -w '%{http_code} → %{redirect_url}' -H 'Host: tienda.ejemplo.test' http://192.168.48.7/
308 → https://tienda.ejemplo.test/
$ curl -s -o /dev/null -w '%{http_code}' -H 'Host: otro.ejemplo.test' http://192.168.48.7/   # host que nadie declaró
404
$ curl -skv --resolve tienda.ejemplo.test:443:192.168.48.7 https://tienda.ejemplo.test/ 2>&1 | grep -E 'subject:|SSL connection'
SSL connection using TLSv1.3 / TLS_AES_256_GCM_SHA384 / X25519MLKEM768 / RSASSA-PSS
subject: CN=*.ejemplo.test
$ kubectl patch ingress entrada --type=json -p '[{"op":"replace","path":"/spec/tls/0/secretName","value":"no-existe"}]'   # un Secret que no existe
ingress.networking.k8s.io/entrada patched
$ curl -skv --resolve tienda.ejemplo.test:443:192.168.48.7 https://tienda.ejemplo.test/ 2>&1 | grep -E 'subject:|^soy'
subject: O=Acme Co; CN=Kubernetes Ingress Controller Fake Certificate
soy tienda
$ kubectl delete -f 2-ingress.yaml && kubectl delete -f ingress-nginx-controller-v1.15.1-kind.yaml
(ingress-nginx borrado)

### 4 · Gateway API con Envoy Gateway v1.10.0
$ kubectl apply --server-side -f envoy-gateway-v1.10.0-install.yaml
43 objetos aplicados
(envoy-gateway disponible 2752 ms después del apply; imagen ya bajada en una corrida anterior)
$ kubectl get crd | grep -c gateway.networking.k8s.io
10
$ kubectl get crd gateways.gateway.networking.k8s.io -o jsonpath='{.metadata.annotations.gateway\.networking\.k8s\.io/bundle-version} {.metadata.annotations.gateway\.networking\.k8s\.io/channel}'
v1.6.1 experimental
$ kubectl get ingress -A   # ya no hay ningún Ingress
No resources found
$ docker run -d --name k8s-a-cpk --network kind -v /var/run/docker.sock:/var/run/docker.sock registry.k8s.io/cloud-provider-kind/cloud-controller-manager:v0.12.0 --gateway-channel disabled --enable-default-ingress=false
$ kubectl apply -f 3-gateway.yaml
gatewayclass.gateway.networking.k8s.io/envoy created
gateway.gateway.networking.k8s.io/entrada created
httproute.gateway.networking.k8s.io/tienda created
httproute.gateway.networking.k8s.io/blog created
(Gateway Programmed 11651 ms después del apply; imagen ya bajada en una corrida anterior)
$ kubectl get gatewayclass,gateway,httproute
NAME    CONTROLLER                                      ACCEPTED   AGE
envoy   gateway.envoyproxy.io/gatewayclass-controller   True       12s
NAME      CLASS   ADDRESS        PROGRAMMED   AGE
entrada   envoy   192.168.48.9   True         12s
NAME     HOSTNAMES                 AGE
blog     ["blog.ejemplo.test"]     12s
tienda   ["tienda.ejemplo.test"]   12s
$ kubectl get pods,svc -n envoy-gateway-system -l gateway.envoyproxy.io/owning-gateway-name=entrada
POD                                             ESTADO    IMAGEN
envoy-parte4-entrada-1d5a10aa-6989665dd-tk67w   Running   docker.io/envoyproxy/envoy:distroless-v1.40.2@sha256:09ca6f2140a61ad8df11779a4a30d52b48433d444466328494f9188c9c35eded
NAME                            TYPE           CLUSTER-IP      EXTERNAL-IP    PORT(S)                      AGE
envoy-parte4-entrada-1d5a10aa   LoadBalancer   10.96.131.100   192.168.48.9   80:31896/TCP,443:32418/TCP   12s
$ kubectl get gateway entrada -o jsonpath='{range .status.listeners[*]}{.name} rutas={.attachedRoutes} Programmed={.conditions[?(@.type=="Programmed")].status}{"\n"}{end}'
http rutas=2 Programmed=True
https rutas=2 Programmed=True
$ kubectl get httproute tienda -o jsonpath='{range .status.parents[0].conditions[*]}{.type}={.status} {end}'
Accepted=True ResolvedRefs=True 
$ curl -sk --resolve tienda.ejemplo.test:443:192.168.48.9 https://tienda.ejemplo.test/
soy tienda
$ curl -sk --resolve tienda.ejemplo.test:443:192.168.48.9 https://tienda.ejemplo.test/api/pedidos
soy api v1
$ curl -sk --resolve blog.ejemplo.test:443:192.168.48.9 https://blog.ejemplo.test/
soy blog
$ curl -s -H 'Host: blog.ejemplo.test' http://192.168.48.9/   # el listener http no redirige solo
soy blog
$ curl -s -o /dev/null -w '%{http_code}' -H 'Host: otro.ejemplo.test' http://192.168.48.9/
404
$ curl -skv --resolve blog.ejemplo.test:443:192.168.48.9 https://blog.ejemplo.test/ 2>&1 | grep -E 'subject:|SSL connection'
SSL connection using TLSv1.3 / TLS_AES_256_GCM_SHA384 / X25519MLKEM768 / RSASSA-PSS
subject: CN=*.ejemplo.test

### 5 · Canary por peso (90/10) y por cabecera
$ kubectl apply -f 4-canary.yaml
httproute.gateway.networking.k8s.io/api-canary created
$ for i in $(seq 1000); do curl -s -H 'Host: api.ejemplo.test' http://192.168.48.9/; done | sort | uniq -c
    899 soy api v1
    101 soy api v2
$ for i in $(seq 20); do curl -s -H 'Host: api.ejemplo.test' -H 'x-version: v2' http://192.168.48.9/; done | sort | uniq -c
     20 soy api v2

### 6 · Una ruta a un Service que no existe
$ kubectl patch httproute blog --type=json -p '[{"op":"replace","path":"/spec/rules/0/backendRefs/0/name","value":"bolg"}]'
httproute.gateway.networking.k8s.io/blog patched
$ kubectl get httproute blog -o jsonpath='{range .status.parents[0].conditions[*]}{.type}={.status} {.reason}{"\n"}{end}'
Accepted=True Accepted
ResolvedRefs=False BackendNotFound
$ curl -sk -o /dev/null -w '%{http_code}' --resolve blog.ejemplo.test:443:192.168.48.9 https://blog.ejemplo.test/
500

### 7 · Limpieza
contenedores de cloud-provider-kind que quedan: 
```

> Contenedores ajenos vivos al terminar: k8s-b-control-plane k8s-b-worker k8s-b-worker2 
