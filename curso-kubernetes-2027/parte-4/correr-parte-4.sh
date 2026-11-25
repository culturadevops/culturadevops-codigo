#!/bin/bash
# Curso de Kubernetes 2027 · Parte 4: Ingress y Gateway API. Git Bash en la máquina; kubectl dentro del
# nodo k8s-a-control-plane (v1.34.0). Escribe SALIDA-parte-4.md.
#  - Ingress con ingress-nginx controller-v1.15.1 (manifiesto oficial para kind, en descargas/)
#  - Gateway API con Envoy Gateway v1.10.0 (install.yaml oficial, en descargas/; trae Gateway API v1.6.1)
#  - la IP del Gateway la da cloud-provider-kind v0.12.0 (contenedor k8s-a-cpk, sin Gateway ni Ingress propios)
#  - «desde fuera» = contenedor curlimages/curl:8.17.0 desechable en la red «kind» de Docker
# El certificado es autofirmado y se genera en un directorio temporal que se borra al terminar.
# Uso: bash correr-parte-4.sh
set -u
cd "$(dirname "$0")"
. ../comun/lib.sh
SAL=SALIDA-parte-4.md
NS=parte4
fuera() { docker run --rm --ulimit core=1 --network kind --name k8s-a-curl-$RANDOM curlimages/curl:8.17.0 "$@" 2>&1; }
fuera_sh() { docker run --rm --ulimit core=1 --network kind --name k8s-a-curl-$RANDOM --entrypoint sh curlimages/curl:8.17.0 -c "$1" 2>&1; }
# Ruta RELATIVA a propósito: openssl de Git para Windows no entiende /tmp con MSYS_NO_PATHCONV=1.
TLS=.tls-temporal-$$
mkdir -p "$TLS"
trap 'rm -rf "$TLS"' EXIT
{
echo "# SALIDA — Curso de Kubernetes 2027 · Parte 4: Ingress y Gateway API"
echo
echo "> Corrida del $(date '+%Y-%m-%d %H:%M'). kind v0.30.0, clúster k8s-a (1 plano de control + 2 workers), kindest/node:v1.34.0."
echo "> ingress-nginx controller-v1.15.1 · Envoy Gateway v1.10.0 (Gateway API v1.6.1) · cloud-provider-kind v0.12.0 · curl 8.17.0"
echo "> Contenedores ajenos vivos al empezar: $(ajenos)"
echo
echo '```'
ns_nuevo $NS
k config set-context --current --namespace=$NS >/dev/null

titulo "1 · Cuatro aplicaciones y un certificado"
muestra kubectl apply -f 1-apps.yaml
kapply 1-apps.yaml
k wait --for=condition=Available deployment --all --timeout=180s >/dev/null
k get deployments
muestra "openssl req -x509 -newkey rsa:2048 -nodes -days 30 -subj '/CN=*.ejemplo.test' -addext 'subjectAltName=DNS:*.ejemplo.test' -keyout tls.key -out tls.crt"
MSYS_NO_PATHCONV=1 openssl req -x509 -newkey rsa:2048 -nodes -days 30 -subj '/CN=*.ejemplo.test' -addext 'subjectAltName=DNS:*.ejemplo.test' \
  -keyout "$TLS/tls.key" -out "$TLS/tls.crt" 2>/dev/null && echo "(certificado autofirmado generado)"
# /tmp del nodo kind es un tmpfs: docker cp escribe debajo y no se ve. Por eso /root.
docker cp "$TLS/tls.key" "$NODO":/root/k8sa-tls.key >/dev/null; docker cp "$TLS/tls.crt" "$NODO":/root/k8sa-tls.crt >/dev/null
muestra kubectl create secret tls tls-ejemplo --cert=tls.crt --key=tls.key
k create secret tls tls-ejemplo --cert=/root/k8sa-tls.crt --key=/root/k8sa-tls.key
docker exec "$NODO" rm -f /root/k8sa-tls.key /root/k8sa-tls.crt

titulo "2 · ingress-nginx (el controlador que se retiró)"
muestra kubectl apply -f ingress-nginx-controller-v1.15.1-kind.yaml
kapply descargas/ingress-nginx-controller-v1.15.1-kind.yaml | tail -3
T0=$(ms)
k wait -n ingress-nginx --for=condition=Ready pod -l app.kubernetes.io/component=controller --timeout=300s >/dev/null
echo "(controlador listo $(( $(ms) - T0 )) ms después del apply; imagen ya bajada en una corrida anterior)"
muestra "kubectl get pods -n ingress-nginx -l app.kubernetes.io/component=controller -o custom-columns=POD:.metadata.name,NODO:.spec.nodeName,IMAGEN:.spec.containers[0].image"
k get pods -n ingress-nginx -l app.kubernetes.io/component=controller -o custom-columns=POD:.metadata.name,NODO:.spec.nodeName,IMAGEN:.spec.containers[0].image | sed 's/@sha256:[0-9a-f]*//'
NODO_ING=$(k get pods -n ingress-nginx -l app.kubernetes.io/component=controller -o jsonpath='{.items[0].spec.nodeName}')
IP_ING=$(docker inspect -f '{{.NetworkSettings.Networks.kind.IPAddress}}' "$NODO_ING")
echo "(el controlador usa hostPort 80/443 en $NODO_ING = $IP_ING dentro de la red kind)"
muestra kubectl get ingressclass
k get ingressclass

titulo "3 · Un Ingress: por host y por ruta, con TLS"
muestra kubectl apply -f 2-ingress.yaml
sleep 5
kapply 2-ingress.yaml
for i in $(seq 1 60); do [ -n "$(k get ingress entrada -o jsonpath='{.status.loadBalancer.ingress[0]}')" ] && break; sleep 2; done
muestra kubectl get ingress entrada
k get ingress entrada
sleep 3
for u in "tienda.ejemplo.test /" "tienda.ejemplo.test /api/pedidos" "blog.ejemplo.test /"; do
  set -- $u
  muestra "curl -sk --resolve $1:443:$IP_ING https://$1$2"
  fuera -sk --resolve "$1:443:$IP_ING" "https://$1$2"
done
muestra "curl -s -o /dev/null -w '%{http_code} → %{redirect_url}' -H 'Host: tienda.ejemplo.test' http://$IP_ING/"
fuera -s -o /dev/null -w '%{http_code} → %{redirect_url}\n' -H 'Host: tienda.ejemplo.test' "http://$IP_ING/"
muestra "curl -s -o /dev/null -w '%{http_code}' -H 'Host: otro.ejemplo.test' http://$IP_ING/   # host que nadie declaró"
fuera -s -o /dev/null -w '%{http_code}\n' -H 'Host: otro.ejemplo.test' "http://$IP_ING/"
muestra "curl -skv --resolve tienda.ejemplo.test:443:$IP_ING https://tienda.ejemplo.test/ 2>&1 | grep -E 'subject:|SSL connection'"
fuera -skv --resolve "tienda.ejemplo.test:443:$IP_ING" https://tienda.ejemplo.test/ | grep -E 'subject:|SSL connection' | sed 's/^\* *//'
muestra "kubectl patch ingress entrada --type=json -p '[{\"op\":\"replace\",\"path\":\"/spec/tls/0/secretName\",\"value\":\"no-existe\"}]'   # un Secret que no existe"
k patch ingress entrada --type=json -p '[{"op":"replace","path":"/spec/tls/0/secretName","value":"no-existe"}]'
sleep 6
muestra "curl -skv --resolve tienda.ejemplo.test:443:$IP_ING https://tienda.ejemplo.test/ 2>&1 | grep -E 'subject:|^soy'"
fuera -skv --resolve "tienda.ejemplo.test:443:$IP_ING" https://tienda.ejemplo.test/ | grep -E 'subject:|^soy' | sed 's/^\* *//'
muestra "kubectl delete -f 2-ingress.yaml && kubectl delete -f ingress-nginx-controller-v1.15.1-kind.yaml"
k delete ingress entrada >/dev/null
docker exec -i -e KUBECONFIG=/etc/kubernetes/admin.conf "$NODO" kubectl delete -f - --wait=true < descargas/ingress-nginx-controller-v1.15.1-kind.yaml >/dev/null 2>&1
echo "(ingress-nginx borrado)"

titulo "4 · Gateway API con Envoy Gateway v1.10.0"
muestra kubectl apply --server-side -f envoy-gateway-v1.10.0-install.yaml
docker exec -i -e KUBECONFIG=/etc/kubernetes/admin.conf "$NODO" kubectl apply --server-side -f - < descargas/envoy-gateway-v1.10.0-install.yaml 2>&1 | wc -l | sed 's/$/ objetos aplicados/'
T0=$(ms)
k wait -n envoy-gateway-system --for=condition=Available deployment/envoy-gateway --timeout=300s >/dev/null
echo "(envoy-gateway disponible $(( $(ms) - T0 )) ms después del apply; imagen ya bajada en una corrida anterior)"
muestra "kubectl get crd | grep -c gateway.networking.k8s.io"
k get crd | grep -c gateway.networking.k8s.io
muestra "kubectl get crd gateways.gateway.networking.k8s.io -o jsonpath='{.metadata.annotations.gateway\\.networking\\.k8s\\.io/bundle-version} {.metadata.annotations.gateway\\.networking\\.k8s\\.io/channel}'"
k get crd gateways.gateway.networking.k8s.io -o jsonpath='{.metadata.annotations.gateway\.networking\.k8s\.io/bundle-version} {.metadata.annotations.gateway\.networking\.k8s\.io/channel}'; echo
muestra "kubectl get ingress -A   # ya no hay ningún Ingress"
k get ingress -A
muestra "docker run -d --name k8s-a-cpk --network kind -v /var/run/docker.sock:/var/run/docker.sock registry.k8s.io/cloud-provider-kind/cloud-controller-manager:v0.12.0 --gateway-channel disabled --enable-default-ingress=false"
docker run -d --rm --ulimit core=1 --name k8s-a-cpk --network kind -v /var/run/docker.sock:/var/run/docker.sock \
  registry.k8s.io/cloud-provider-kind/cloud-controller-manager:v0.12.0 --gateway-channel disabled --enable-default-ingress=false >/dev/null
muestra kubectl apply -f 3-gateway.yaml
kapply 3-gateway.yaml
T0=$(ms)
k wait --for=condition=Programmed gateway/entrada --timeout=300s >/dev/null
echo "(Gateway Programmed $(( $(ms) - T0 )) ms después del apply; imagen ya bajada en una corrida anterior)"
muestra kubectl get gatewayclass,gateway,httproute
k get gatewayclass; k get gateway; k get httproute
GW=$(k get gateway entrada -o jsonpath='{.status.addresses[0].value}')
muestra "kubectl get pods,svc -n envoy-gateway-system -l gateway.envoyproxy.io/owning-gateway-name=entrada"
k get pods -n envoy-gateway-system -l gateway.envoyproxy.io/owning-gateway-name=entrada -o custom-columns=POD:.metadata.name,ESTADO:.status.phase,IMAGEN:.spec.containers[0].image
k get svc -n envoy-gateway-system -l gateway.envoyproxy.io/owning-gateway-name=entrada
muestra "kubectl get gateway entrada -o jsonpath='{range .status.listeners[*]}{.name} rutas={.attachedRoutes} Programmed={.conditions[?(@.type==\"Programmed\")].status}{\"\n\"}{end}'"
k get gateway entrada -o jsonpath='{range .status.listeners[*]}{.name} rutas={.attachedRoutes} Programmed={.conditions[?(@.type=="Programmed")].status}{"\n"}{end}'
muestra "kubectl get httproute tienda -o jsonpath='{range .status.parents[0].conditions[*]}{.type}={.status} {end}'"
k get httproute tienda -o jsonpath='{range .status.parents[0].conditions[*]}{.type}={.status} {end}'; echo
sleep 3
for u in "tienda.ejemplo.test /" "tienda.ejemplo.test /api/pedidos" "blog.ejemplo.test /"; do
  set -- $u
  muestra "curl -sk --resolve $1:443:$GW https://$1$2"
  fuera -sk --resolve "$1:443:$GW" "https://$1$2"
done
muestra "curl -s -H 'Host: blog.ejemplo.test' http://$GW/   # el listener http no redirige solo"
fuera -s -H 'Host: blog.ejemplo.test' "http://$GW/"
muestra "curl -s -o /dev/null -w '%{http_code}' -H 'Host: otro.ejemplo.test' http://$GW/"
fuera -s -o /dev/null -w '%{http_code}\n' -H 'Host: otro.ejemplo.test' "http://$GW/"
muestra "curl -skv --resolve blog.ejemplo.test:443:$GW https://blog.ejemplo.test/ 2>&1 | grep -E 'subject:|SSL connection'"
fuera -skv --resolve "blog.ejemplo.test:443:$GW" https://blog.ejemplo.test/ | grep -E 'subject:|SSL connection' | sed 's/^\* *//'

titulo "5 · Canary por peso (90/10) y por cabecera"
muestra kubectl apply -f 4-canary.yaml
kapply 4-canary.yaml
sleep 5
muestra "for i in \$(seq 1000); do curl -s -H 'Host: api.ejemplo.test' http://$GW/; done | sort | uniq -c"
fuera_sh "for i in \$(seq 1000); do curl -s -H 'Host: api.ejemplo.test' http://$GW/; done | sort | uniq -c"
muestra "for i in \$(seq 20); do curl -s -H 'Host: api.ejemplo.test' -H 'x-version: v2' http://$GW/; done | sort | uniq -c"
fuera_sh "for i in \$(seq 20); do curl -s -H 'Host: api.ejemplo.test' -H 'x-version: v2' http://$GW/; done | sort | uniq -c"

titulo "6 · Una ruta a un Service que no existe"
muestra "kubectl patch httproute blog --type=json -p '[{\"op\":\"replace\",\"path\":\"/spec/rules/0/backendRefs/0/name\",\"value\":\"bolg\"}]'"
k patch httproute blog --type=json -p '[{"op":"replace","path":"/spec/rules/0/backendRefs/0/name","value":"bolg"}]'
sleep 4
muestra "kubectl get httproute blog -o jsonpath='{range .status.parents[0].conditions[*]}{.type}={.status} {.reason}{\"\\n\"}{end}'"
k get httproute blog -o jsonpath='{range .status.parents[0].conditions[*]}{.type}={.status} {.reason}{"\n"}{end}'
muestra "curl -sk -o /dev/null -w '%{http_code}' --resolve blog.ejemplo.test:443:$GW https://blog.ejemplo.test/"
fuera -sk -o /dev/null -w '%{http_code}\n' --resolve "blog.ejemplo.test:443:$GW" https://blog.ejemplo.test/

titulo "7 · Limpieza"
k delete -f - >/dev/null 2>&1 < 4-canary.yaml
docker exec -i -e KUBECONFIG=/etc/kubernetes/admin.conf "$NODO" kubectl delete -f - --wait=true < 3-gateway.yaml >/dev/null 2>&1
sleep 5
docker stop k8s-a-cpk >/dev/null 2>&1
sleep 2
echo "contenedores de cloud-provider-kind que quedan: $(docker ps -a --format '{{.Names}}' | grep -i -E 'kindccm|k8s-a-cpk' | tr '\n' ' ')"
echo '```'
echo
echo "> Contenedores ajenos vivos al terminar: $(ajenos)"
} > "$SAL" 2>&1
echo "listo: $SAL"
