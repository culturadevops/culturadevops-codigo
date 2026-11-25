#!/bin/bash
# Demo del vídeo 801 (cultura-devops): operador de Kubernetes en Python con kopf, contra kind (clúster cd801).
# Corre en el host (Git Bash). Requiere: kind create cluster --name cd801 · docker build -t cd801-operador:1 .
# Salida literal → _salida.txt (se copia a SALIDA.md). No mide tiempos: es funcional.
set -u
export MSYS_NO_PATHCONV=1
cd "$(dirname "$0")"
K="kubectl --context kind-cd801"
k() { $K "$@" 2>&1; }
$K delete crd paginawebs.web.culturadevops.dev --ignore-not-found >/dev/null 2>&1
kind get kubeconfig --internal --name cd801 > _kubeconfig
KCFG="$(cygpath -w "$PWD")\\_kubeconfig"
operador() {  # $1 = 0/1 VIGILAR_HIJOS
  docker rm -f cd801-op >/dev/null 2>&1
  docker run -d --rm --name cd801-op --network kind --cpus 1 -e VIGILAR_HIJOS="$1" \
    -v "$KCFG:/root/.kube/config:ro" cd801-operador:1 >/dev/null
  for i in $(seq 1 60); do docker logs cd801-op 2>&1 | grep -q "Kopf is ready\|Resuming\|Handler" && break; sleep 1; done
  sleep 3
}

echo "### 0 · Versiones"
echo "\$ kind version ; kubectl version (servidor)"
kind version
k version | grep Server
echo "\$ python --version ; pip show kopf kubernetes   # dentro de la imagen del operador"
docker run --rm --cpus 1 cd801-operador:1 sh -c "python --version; pip show kopf kubernetes 2>/dev/null | grep -E '^(Name|Version)'"
echo "\$ docker image ls cd801-operador:1"
docker image ls cd801-operador:1 --format '{{.Repository}}:{{.Tag}}  {{.Size}}'

echo
echo "### 1 · La CRD (escrita a mano: kopf no la genera) y el operador"
echo "\$ wc -l crd.yaml operador.py"
wc -l crd.yaml operador.py
echo "\$ kubectl apply -f crd.yaml"
k apply -f crd.yaml
k wait --for=condition=Established crd/paginawebs.web.culturadevops.dev --timeout=60s >/dev/null
sleep 15   # sin esto, kopf arranca con 429 «storage is (re)initializing» y reintenta (pasó en la 1.ª corrida)
echo "\$ kubectl get crd -o name | grep paginaweb"
k get crd -o name | grep paginaweb

echo
echo "### 2 · El operador en marcha (sin vigilar a los hijos)"
echo "\$ docker run --rm --cpus 1 --network kind cd801-operador:1   # kopf run --standalone --namespace default operador.py"
operador 0
docker logs cd801-op 2>&1 | head -5
cat > _pagina.yaml <<'EOF'
apiVersion: web.culturadevops.dev/v1
kind: PaginaWeb
metadata:
  name: hola
spec:
  replicas: 2
  mensaje: Hola desde un operador en Python
EOF
echo "\$ cat pagina.yaml"
cat _pagina.yaml
echo "\$ kubectl apply -f pagina.yaml"
k apply -f _pagina.yaml
sleep 3
k rollout status deployment/hola --timeout=180s >/dev/null
echo "\$ kubectl get deployment,service,configmap -l app=hola -o name ; kubectl get paginaweb"
k get deployment,service,configmap -l app=hola -o name
k get paginaweb
echo "\$ kubectl get deployment hola -o jsonpath='{.metadata.ownerReferences[0].kind}/{.metadata.ownerReferences[0].name}'"
k get deployment hola -o jsonpath='{.metadata.ownerReferences[0].kind}/{.metadata.ownerReferences[0].name}'; echo
echo "\$ kubectl run prueba --rm -i --image=busybox:1.37 --restart=Never -- wget -qO- http://hola"
$K run prueba --rm -i --image=busybox:1.37 --restart=Never -- wget -qO- http://hola 2>/dev/null | grep "<h1>" | head -1
echo "\$ docker logs cd801-op   # lo que dijo kopf"
docker logs cd801-op 2>&1 | grep -E "configmap|succeeded" | head -4

echo
echo "### 3 · Cambiar la PaginaWeb: kopf llama al handler de update"
echo "\$ kubectl patch paginaweb hola --type merge -p '{\"spec\":{\"replicas\":4}}'"
k patch paginaweb hola --type merge -p '{"spec":{"replicas":4}}'
sleep 3
k rollout status deployment/hola --timeout=180s >/dev/null
echo "\$ kubectl get deployment hola ; kubectl get paginaweb"
k get deployment hola
k get paginaweb
echo "\$ kubectl get paginaweb hola -o jsonpath='{.metadata.annotations.kopf\.zalando\.org/last-handled-configuration}'"
k get paginaweb hola -o jsonpath='{.metadata.annotations.kopf\.zalando\.org/last-handled-configuration}'; echo

echo
echo "### 4 · Borrar el Deployment a mano, SIN vigilar a los hijos"
echo "\$ kubectl delete deployment hola"
k delete deployment hola
sleep 30
echo "\$ kubectl get deployment hola   # 30 segundos después"
k get deployment hola

echo
echo "### 5 · Reiniciar el operador: el handler de resume lo repara"
echo "\$ docker restart del operador (VIGILAR_HIJOS=1)"
operador 1
sleep 5
echo "\$ kubectl get deployment hola"
k get deployment hola
echo "\$ docker logs cd801-op"
docker logs cd801-op 2>&1 | grep -E "resum|configmap" | head -3

echo
echo "### 6 · Ahora vigilando a los hijos: borrar el Deployment otra vez"
echo "\$ kubectl delete deployment hola"
k delete deployment hola
sleep 8
echo "\$ kubectl get deployment hola"
k get deployment hola
echo "\$ docker logs cd801-op"
docker logs cd801-op 2>&1 | grep -E "borró|configmap" | tail -2
k rollout status deployment/hola --timeout=180s >/dev/null
sleep 5
echo "\$ kubectl get paginaweb   # el estado, ahora que alguien lo rellena"
k get paginaweb

echo
echo "### 7 · La validación de la CRD"
echo "\$ kubectl patch paginaweb hola --type merge -p '{\"spec\":{\"replicas\":50}}'"
k patch paginaweb hola --type merge -p '{"spec":{"replicas":50}}'

echo
echo "### 8 · Memoria del operador"
echo "\$ docker stats --no-stream cd801-op"
docker stats --no-stream --format '{{.Name}}  {{.MemUsage}}' cd801-op

echo
echo "### 9 · Borrar la PaginaWeb: se va todo lo suyo"
echo "\$ kubectl delete paginaweb hola"
k delete paginaweb hola
sleep 10
echo "\$ kubectl get deployment,service,configmap hola"
k get deployment,service,configmap hola
docker stop cd801-op >/dev/null
rm -f _kubeconfig _pagina.yaml
