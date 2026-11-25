#!/usr/bin/env bash
# Demo del vídeo 468 «Seguridad mínima en Kubernetes» — se EJECUTA y su salida va a SALIDA.md.
# Un clúster local con kind (dentro de Docker), y tres controles:
#   1) RBAC: una cuenta de servicio que solo puede LEER pods de su namespace (kubectl auth can-i);
#   2) Pod Security Admission: el namespace en «restricted» rechaza un pod privilegiado y acepta uno correcto;
#   3) NetworkPolicy: un cliente llega a un servidor; con «denegar todo» deja de llegar; con una regla, vuelve.
# Al final el clúster se borra. Nada sale de esta máquina.
set -u
KIND="$HOME/go/bin/kind"
C=demo-seguridad
export MSYS_NO_PATHCONV=1
"$KIND" delete cluster --name "$C" >/dev/null 2>&1
"$KIND" create cluster --name "$C" --wait 120s >/dev/null 2>&1
K="kubectl --context kind-$C"
echo '$ kubectl version | grep Server'
$K version 2>/dev/null | grep Server
echo

echo '# 1) RBAC'
$K create namespace tienda >/dev/null
$K -n tienda create serviceaccount lector >/dev/null
$K -n tienda create role leer-pods --verb=get,list,watch --resource=pods >/dev/null
$K -n tienda create rolebinding lector-lee --role=leer-pods --serviceaccount=tienda:lector >/dev/null
echo '$ kubectl -n tienda create role leer-pods --verb=get,list,watch --resource=pods'
echo '$ kubectl -n tienda create rolebinding lector-lee --role=leer-pods --serviceaccount=tienda:lector'
for q in "get pods -n tienda" "delete pods -n tienda" "get secrets -n tienda" "get pods -n kube-system"; do
  echo "\$ kubectl auth can-i $q --as=system:serviceaccount:tienda:lector"
  $K auth can-i $q --as=system:serviceaccount:tienda:lector 2>&1
done
echo

echo '# 2) Pod Security Admission'
echo '$ kubectl label namespace tienda pod-security.kubernetes.io/enforce=restricted'
$K label namespace tienda pod-security.kubernetes.io/enforce=restricted >/dev/null && echo "namespace/tienda labeled"
cat > privilegiado.yaml <<'EOF'
apiVersion: v1
kind: Pod
metadata: {name: privilegiado}
spec:
  containers:
  - name: app
    image: busybox:1.36
    command: ["sleep", "3600"]
    securityContext: {privileged: true}
EOF
cat > correcto.yaml <<'EOF'
apiVersion: v1
kind: Pod
metadata: {name: correcto}
spec:
  securityContext: {runAsNonRoot: true, runAsUser: 1000, seccompProfile: {type: RuntimeDefault}}
  containers:
  - name: app
    image: busybox:1.36
    command: ["sleep", "3600"]
    securityContext: {allowPrivilegeEscalation: false, capabilities: {drop: ["ALL"]}}
EOF
echo '$ kubectl -n tienda apply -f privilegiado.yaml'
$K -n tienda apply -f privilegiado.yaml 2>&1 | fold -w 110 -s
echo '$ kubectl -n tienda apply -f correcto.yaml'
$K -n tienda apply -f correcto.yaml 2>&1
echo

echo '# 3) NetworkPolicy'
$K create namespace red >/dev/null
$K -n red run servidor --image=nginx:1.27-alpine --labels=app=servidor --port=80 >/dev/null
$K -n red expose pod servidor --port=80 >/dev/null
$K -n red run cliente --image=busybox:1.36 --labels=app=cliente -- sleep 3600 >/dev/null
$K -n red run otro --image=busybox:1.36 --labels=app=otro -- sleep 3600 >/dev/null
$K -n red wait --for=condition=Ready pod/servidor pod/cliente pod/otro --timeout=180s >/dev/null
probar() { # $1 = pod que pregunta
  if $K -n red exec "$1" -- wget -q -T 3 -O /dev/null http://servidor 2>/dev/null; then echo "  $1 -> servidor: responde"; else echo "  $1 -> servidor: sin respuesta (3 s)"; fi
}
echo '$ # sin políticas'
probar cliente; probar otro
cat > denegar.yaml <<'EOF'
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata: {name: denegar-todo}
spec:
  podSelector: {}
  policyTypes: [Ingress]
EOF
cat > permitir.yaml <<'EOF'
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata: {name: cliente-a-servidor}
spec:
  podSelector: {matchLabels: {app: servidor}}
  ingress:
  - from:
    - podSelector: {matchLabels: {app: cliente}}
EOF
echo '$ kubectl -n red apply -f denegar.yaml'
$K -n red apply -f denegar.yaml 2>&1
sleep 5
probar cliente; probar otro
echo '$ kubectl -n red apply -f permitir.yaml'
$K -n red apply -f permitir.yaml 2>&1
sleep 5
probar cliente; probar otro
echo
"$KIND" delete cluster --name "$C" >/dev/null 2>&1
echo '$ kind delete cluster   # clúster borrado'
echo '$ kind version'
"$KIND" version
