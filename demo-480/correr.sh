#!/usr/bin/env bash
# Demo del vídeo 480 «¿Debo aprender Kubernetes en la era de la IA?» — se EJECUTA y su salida va a SALIDA.md.
# Un clúster local con kind (dentro de Docker) y un Deployment como los que genera una IA:
#   1) con un campo inventado (alucinado): el servidor de la API lo rechaza (validación estricta de campos);
#   2) sin el campo inventado, se aplica… y trivy encuentra lo que falta (raíz, sin límites, imagen sin versión fija);
#   3) la versión revisada: trivy sin hallazgos altos y el despliegue queda disponible.
# Al final el clúster se borra. Nada sale de esta máquina.
set -u
KIND="$HOME/go/bin/kind"
C=demo-era-ia
export MSYS_NO_PATHCONV=1
T=$(mktemp -d)
cd "$T"
"$KIND" delete cluster --name "$C" >/dev/null 2>&1
"$KIND" create cluster --name "$C" --wait 120s >/dev/null 2>&1
K="kubectl --context kind-$C"

cat > ia.yaml <<'EOF'
apiVersion: apps/v1
kind: Deployment
metadata:
  name: web
spec:
  replicas: 2
  autoscale: true
  selector:
    matchLabels:
      app: web
  template:
    metadata:
      labels:
        app: web
    spec:
      containers:
        - name: web
          image: nginx:latest
          ports:
            - containerPort: 80
          resources:
            limit:
              memory: "128Mi"
EOF

# lo mismo sin los dos campos inventados (autoscale y limit en singular)
grep -vE "autoscale: true|limit:|memory: \"128Mi\"|resources:" ia.yaml > ia-sin-inventos.yaml

cat > revisado.yaml <<'EOF'
apiVersion: apps/v1
kind: Deployment
metadata:
  name: web
spec:
  replicas: 2
  selector:
    matchLabels:
      app: web
  template:
    metadata:
      labels:
        app: web
    spec:
      automountServiceAccountToken: false
      securityContext:
        runAsNonRoot: true
        seccompProfile:
          type: RuntimeDefault
      containers:
        - name: web
          image: nginxinc/nginx-unprivileged:1.29.1-alpine
          imagePullPolicy: Always
          ports:
            - containerPort: 8080
          resources:
            requests:
              cpu: 50m
              memory: 64Mi
            limits:
              cpu: 200m
              memory: 128Mi
          securityContext:
            runAsUser: 10101
            runAsGroup: 10101
            allowPrivilegeEscalation: false
            readOnlyRootFilesystem: true
            capabilities:
              drop: ["ALL"]
          volumeMounts:
            - name: tmp
              mountPath: /tmp
          readinessProbe:
            httpGet:
              path: /
              port: 8080
      volumes:
        - name: tmp
          emptyDir: {}
EOF

echo '$ kubectl version | grep Server'
$K version 2>/dev/null | grep Server
echo
echo '$ grep -nE "autoscale|limit:" deployment.yaml   # dos campos que no existen'
grep -nE "autoscale|limit:" ia.yaml
echo '$ kubectl apply -f deployment.yaml'
$K apply -f ia.yaml 2>&1
echo
echo '$ # sin los campos inventados'
echo '$ kubectl apply -f deployment.yaml'
$K apply -f ia-sin-inventos.yaml 2>&1
$K rollout status deploy/web --timeout=120s 2>&1 | tail -1
echo '$ kubectl exec deploy/web -- id'
$K exec deploy/web -- id 2>&1
echo
TRIVY="docker run --rm -v $(cygpath -w "$T"):/src aquasec/trivy:0.67.2 config --quiet"
cp ia-sin-inventos.yaml deployment.yaml
mkdir -p a b && mv deployment.yaml a/ && cp revisado.yaml b/deployment.yaml
echo '$ trivy config --severity HIGH,CRITICAL .'
$TRIVY --severity HIGH,CRITICAL /src/a 2>&1 | grep -E "^Tests:|^Failures:|^KSV|^AVD-" | head -20
echo
echo '$ trivy config --severity HIGH,CRITICAL .   # versión revisada'
$TRIVY --severity HIGH,CRITICAL /src/b 2>&1 | grep -E "^Tests:|^Failures:|^KSV|^AVD-|Misconfig|kubernetes" | head -10
echo
$K delete deploy web >/dev/null 2>&1
echo '$ kubectl apply -f deployment.yaml   # versión revisada'
$K apply -f revisado.yaml 2>&1
echo '$ kubectl rollout status deploy/web'
$K rollout status deploy/web --timeout=180s 2>&1 | tail -1
echo '$ kubectl get pods -l app=web'
$K get pods -l app=web --no-headers 2>&1 | awk '{print $1, $2, $3}'
echo '$ kubectl exec deploy/web -- id'
$K exec deploy/web -- id 2>&1
echo
echo '$ kind --version && trivy --version'
"$KIND" --version
docker run --rm aquasec/trivy:0.67.2 --version 2>&1 | head -1
"$KIND" delete cluster --name "$C" >/dev/null 2>&1
cd / && rm -rf "$T"
