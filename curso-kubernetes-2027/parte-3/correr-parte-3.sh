#!/bin/bash
# Curso de Kubernetes 2027 · Parte 3: Service. Git Bash en la máquina; kubectl dentro del nodo
# k8s-a-control-plane (v1.34.0). Escribe SALIDA-parte-3.md. Las pruebas «desde fuera» se hacen con un
# contenedor busybox desechable en la red «kind» de Docker. Para el LoadBalancer arranca un rato
# cloud-provider-kind v0.12.0 (contenedor k8s-a-cpk), sin Gateway ni Ingress propios.
# Uso: bash correr-parte-3.sh
set -u
cd "$(dirname "$0")"
. ../comun/lib.sh
SAL=SALIDA-parte-3.md
docker exec "$NODO" rm -rf /curso; docker cp .. "$NODO":/curso >/dev/null
NS=parte3
fuera() { docker run --rm --ulimit core=1 --network kind --name k8s-a-fuera-$RANDOM busybox:1.37 "$@" 2>&1; }
IP_CP=$(docker inspect -f '{{.NetworkSettings.Networks.kind.IPAddress}}' k8s-a-control-plane)
IP_W1=$(docker inspect -f '{{.NetworkSettings.Networks.kind.IPAddress}}' k8s-a-worker)
IP_W2=$(docker inspect -f '{{.NetworkSettings.Networks.kind.IPAddress}}' k8s-a-worker2)
{
echo "# SALIDA — Curso de Kubernetes 2027 · Parte 3: Service"
echo
echo "> Corrida del $(date '+%Y-%m-%d %H:%M'). kind v0.30.0, clúster k8s-a (1 plano de control + 2 workers), kindest/node:v1.34.0, kube-proxy en modo iptables."
echo "> Imágenes ya descargadas en los nodos. Contenedores ajenos vivos al empezar: $(ajenos)"
echo "> Nodos en la red kind: control-plane $IP_CP · worker $IP_W1 · worker2 $IP_W2"
echo
echo '```'
ns_nuevo $NS
k config set-context --current --namespace=$NS >/dev/null

titulo "1 · Tres pods y un Service ClusterIP"
muestra kubectl apply -f 1-web.yaml
kapply 1-web.yaml
k rollout status deployment/web --timeout=180s >/dev/null
k wait --for=condition=Ready pod/cliente --timeout=120s >/dev/null
muestra kubectl get pods -l app=web -o wide
k get pods -l app=web -o wide | awk '{print $1, $2, $3, $6, $7}'
muestra kubectl get service web
k get service web
CIP=$(k get service web -o jsonpath='{.spec.clusterIP}')
muestra "kubectl get endpointslices -l kubernetes.io/service-name=web"
k get endpointslices -l kubernetes.io/service-name=web
muestra "kubectl get endpointslices -l kubernetes.io/service-name=web -o jsonpath='{range .items[*].endpoints[*]}{.addresses[0]} {.targetRef.name} ready={.conditions.ready}{\"\\n\"}{end}'"
k get endpointslices -l kubernetes.io/service-name=web -o jsonpath='{range .items[*].endpoints[*]}{.addresses[0]} {.targetRef.name} ready={.conditions.ready}{"\n"}{end}'

titulo "2 · La ClusterIP no es una máquina: es una regla"
muestra "kubectl exec cliente -- wget -qO- http://$CIP"
k exec cliente -- wget -qO- -T 2 http://$CIP
muestra "kubectl exec cliente -- ping -c 2 -W 1 $CIP"
k exec cliente -- ping -c 2 -W 1 $CIP | tail -2
muestra "iptables-save -t nat | grep 'parte3/web cluster IP'   # en cualquier nodo"
docker exec k8s-a-worker sh -c "iptables-save -t nat | grep 'parte3/web cluster IP' | grep -- '-j KUBE-SVC'" | sed -E 's/ -m comment --comment "[^"]*"//'
SVC_CHAIN=$(docker exec k8s-a-worker sh -c "iptables-save -t nat | grep 'parte3/web cluster IP' | grep -o 'KUBE-SVC-[A-Z0-9]*' | head -1")
muestra "iptables-save -t nat | grep -- '-A $SVC_CHAIN'"
docker exec k8s-a-worker sh -c "iptables-save -t nat | grep -- '-A $SVC_CHAIN ' | grep KUBE-SEP" | sed -E 's/ -m comment --comment "[^"]*"//'

titulo "3 · Reparto: 300 peticiones al Service"
muestra "kubectl exec cliente -- sh -c 'for i in \$(seq 300); do wget -qO- http://web; done | sort | uniq -c'"
k exec cliente -- sh -c 'for i in $(seq 300); do wget -qO- -T 2 http://web; done | sort | uniq -c'

titulo "4 · DNS interno"
muestra "kubectl exec cliente -- cat /etc/resolv.conf"
k exec cliente -- cat /etc/resolv.conf
muestra "kubectl exec cliente -- nslookup web.parte3.svc.cluster.local"
k exec cliente -- nslookup web.parte3.svc.cluster.local | grep -A2 '^Name' | grep -v '^--'
muestra "kubectl exec cliente -- wget -qO- http://web   # nombre corto, mismo namespace"
k exec cliente -- wget -qO- -T 2 http://web
k create namespace otro >/dev/null 2>&1
k run -n otro vecino --image=busybox:1.37.0 --restart=Never -- sleep 600 >/dev/null
k wait -n otro --for=condition=Ready pod/vecino --timeout=60s >/dev/null
muestra "kubectl exec -n otro vecino -- wget -qO- http://web   # desde OTRO namespace"
k exec -n otro vecino -- wget -qO- -T 2 http://web
muestra "kubectl exec -n otro vecino -- wget -qO- http://web.parte3"
k exec -n otro vecino -- wget -qO- -T 2 http://web.parte3
k delete namespace otro --wait=false >/dev/null

titulo "5 · Un pod deja de estar Ready (readinessProbe), medido"
VICT=$(k get pods -l app=web -o jsonpath='{.items[0].metadata.name}')
muestra "kubectl exec $VICT -- rm /usr/share/nginx/html/listo.html   # periodSeconds 2, failureThreshold 3"
nodo_sh "sh /curso/parte-3/readiness.sh $NS $CIP $VICT"
muestra "kubectl get pod $VICT   # durante la caída (otra vez sin listo.html 8 s)"
k exec $VICT -- rm /usr/share/nginx/html/listo.html; sleep 8
k get pod $VICT
muestra "kubectl get endpointslices -l kubernetes.io/service-name=web -o jsonpath='…{.targetRef.name} ready={.conditions.ready} serving={.conditions.serving}…'"
k get endpointslices -l kubernetes.io/service-name=web -o jsonpath='{range .items[*].endpoints[*]}{.targetRef.name} ready={.conditions.ready} serving={.conditions.serving}{"\n"}{end}'
k exec $VICT -- touch /usr/share/nginx/html/listo.html; sleep 4

titulo "6 · Un selector que no casa con nada"
muestra kubectl apply -f 5-sin-pods.yaml
kapply 5-sin-pods.yaml; sleep 2
muestra "kubectl get endpointslices -l kubernetes.io/service-name=web-mal"
k get endpointslices -l kubernetes.io/service-name=web-mal
muestra "kubectl exec cliente -- wget -qO- http://web-mal"
k exec cliente -- wget -qO- -T 2 http://web-mal

titulo "7 · NodePort: el mismo puerto en TODOS los nodos"
k scale deployment web --replicas=1 >/dev/null; k rollout status deployment/web --timeout=60s >/dev/null; sleep 3
muestra kubectl apply -f 2-nodeport.yaml
kapply 2-nodeport.yaml
muestra kubectl get service web-nodeport
k get service web-nodeport
muestra "kubectl get pods -l app=web -o wide   # una sola réplica"
k get pods -l app=web -o wide | awk '{print $1, $3, $7}'
for n in "control-plane $IP_CP" "worker $IP_W1" "worker2 $IP_W2"; do
  set -- $n
  muestra "docker run --rm --network kind busybox:1.37 wget -qO- http://$2:30080   # nodo $1"
  fuera wget -qO- -T 3 http://$2:30080
done
muestra "kubectl patch service web-nodeport -p '{\"spec\":{\"externalTrafficPolicy\":\"Local\"}}'"
k patch service web-nodeport -p '{"spec":{"externalTrafficPolicy":"Local"}}'
sleep 3
for n in "control-plane $IP_CP" "worker $IP_W1" "worker2 $IP_W2"; do
  set -- $n
  muestra "docker run --rm --network kind busybox:1.37 wget -qO- -T 3 http://$2:30080   # nodo $1, Local"
  fuera wget -qO- -T 3 http://$2:30080
done
k scale deployment web --replicas=3 >/dev/null; k rollout status deployment/web --timeout=60s >/dev/null

titulo "8 · LoadBalancer en kind"
muestra kubectl apply -f 3-loadbalancer.yaml
kapply 3-loadbalancer.yaml
sleep 20
muestra "kubectl get service web-lb   # 20 s después, sin proveedor de nube"
k get service web-lb
muestra "docker run -d --name k8s-a-cpk --network kind -v /var/run/docker.sock:/var/run/docker.sock registry.k8s.io/cloud-provider-kind/cloud-controller-manager:v0.12.0 --gateway-channel disabled --enable-default-ingress=false"
T0=$(ms)
docker run -d --rm --ulimit core=1 --name k8s-a-cpk --network kind -v /var/run/docker.sock:/var/run/docker.sock \
  registry.k8s.io/cloud-provider-kind/cloud-controller-manager:v0.12.0 --gateway-channel disabled --enable-default-ingress=false >/dev/null
until [ -n "$(k get service web-lb -o jsonpath='{.status.loadBalancer.ingress[0].ip}')" ]; do sleep 0.5; [ $(( $(ms) - T0 )) -gt 180000 ] && break; done
echo "(IP externa asignada $(( $(ms) - T0 )) ms después de arrancar cloud-provider-kind; incluye bajar su imagen de Envoy si no estaba)"
muestra kubectl get service web-lb
k get service web-lb
LBIP=$(k get service web-lb -o jsonpath='{.status.loadBalancer.ingress[0].ip}')
muestra "docker ps --filter label=io.x-k8s.cloud-provider-kind.cluster=k8s-a --format '{{.Names}} {{.Image}}'"
docker ps --filter label=io.x-k8s.cloud-provider-kind.cluster=k8s-a --format '{{.Names}} {{.Image}}'
docker ps --format '{{.Names}} {{.Image}} {{.Labels}}' | grep -i -E 'kindccm|envoy' | awk '{print $1, $2}'
sleep 3
muestra "docker run --rm --network kind busybox:1.37 sh -c 'for i in \$(seq 30); do wget -qO- http://$LBIP; done | sort | uniq -c'"
fuera sh -c "for i in \$(seq 30); do wget -qO- -T 3 http://$LBIP; done | sort | uniq -c"
muestra "curl -m 5 http://$LBIP   # desde Windows, fuera de la red kind"
curl -s -m 5 -o /dev/null -w '%{http_code}\n' http://$LBIP 2>&1 || echo "(sin respuesta en 5 s)"

titulo "9 · Headless: sin ClusterIP, el DNS da las IP de los pods"
muestra kubectl apply -f 4-headless.yaml
kapply 4-headless.yaml; sleep 3
muestra kubectl get service web web-headless
k get service web web-headless
muestra "kubectl exec cliente -- nslookup web-headless.parte3.svc.cluster.local"
k exec cliente -- nslookup web-headless.parte3.svc.cluster.local | grep '^Address' | grep -v '#53'
muestra "kubectl get pods -l app=web -o custom-columns=POD:.metadata.name,IP:.status.podIP"
k get pods -l app=web -o custom-columns=POD:.metadata.name,IP:.status.podIP

titulo "10 · Limpieza del LoadBalancer"
k delete service web-lb >/dev/null; sleep 5
docker stop k8s-a-cpk >/dev/null 2>&1
sleep 2
echo "contenedores de cloud-provider-kind que quedan: $(docker ps -a --format '{{.Names}}' | grep -i -E 'kindccm|k8s-a-cpk' | tr '\n' ' ')"
echo '```'
echo
echo "> Contenedores ajenos vivos al terminar: $(ajenos)"
} > "$SAL" 2>&1
echo "listo: $SAL"
