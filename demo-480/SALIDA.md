$ kubectl version | grep Server
Server Version: v1.34.0

$ grep -nE "autoscale|limit:" deployment.yaml   # dos campos que no existen
7:  autoscale: true
22:            limit:
$ kubectl apply -f deployment.yaml
Error from server (BadRequest): error when creating "ia.yaml": Deployment in version "v1" cannot be handled as a Deployment: strict decoding error: unknown field "spec.autoscale", unknown field "spec.template.spec.containers[0].resources.limit"

$ # sin los campos inventados
$ kubectl apply -f deployment.yaml
deployment.apps/web created
deployment "web" successfully rolled out
$ kubectl exec deploy/web -- id
uid=0(root) gid=0(root) groups=0(root)

$ trivy config --severity HIGH,CRITICAL .
Tests: 23 (SUCCESSES: 20, FAILURES: 3)
Failures: 3 (HIGH: 3, CRITICAL: 0)
AVD-KSV-0014 (HIGH): Container 'web' of Deployment 'web' should set 'securityContext.readOnlyRootFilesystem' to true
AVD-KSV-0118 (HIGH): container web in default namespace is using the default security context
AVD-KSV-0118 (HIGH): deployment web in default namespace is using the default security context, which allows root privileges

$ trivy config --severity HIGH,CRITICAL .   # versión revisada
│     Target      │    Type    │ Misconfigurations │
│ deployment.yaml │ kubernetes │         0         │

$ kubectl apply -f deployment.yaml   # versión revisada
deployment.apps/web created
$ kubectl rollout status deploy/web
deployment "web" successfully rolled out
$ kubectl get pods -l app=web
web-85cbf5c79f-cdzmh 1/1 Running
web-85cbf5c79f-zkwjp 1/1 Running
$ kubectl exec deploy/web -- id
uid=10101 gid=10101 groups=10101

$ kind --version && trivy --version
kind version 0.30.0
Version: 0.67.2
