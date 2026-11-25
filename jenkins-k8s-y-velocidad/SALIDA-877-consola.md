# SALIDA-877-consola · un build de pod-agente en caliente (build #10, SUCCESS, 4.1 s)

`k8s/consola_877.py`. Sin cronómetro.

## La consola del build
```
Started by user unknown or anonymous
[Pipeline] Start of Pipeline
[Pipeline] podTemplate
[Pipeline] {
[Pipeline] node
Created Pod: kind jenkins-agentes/pod-agente-10-r0fgr-mgsfg-q7jq0
[PodInfo] jenkins-agentes/pod-agente-10-r0fgr-mgsfg-q7jq0
	Container [jnlp] waiting [ContainerCreating] No message
	Container [maven] waiting [ContainerCreating] No message
	Container [node] waiting [ContainerCreating] No message
	Pod [Pending][ContainersNotReady] containers with unready status: [maven node jnlp]
Agent pod-agente-10-r0fgr-mgsfg-q7jq0 is provisioned from template pod-agente_10-r0fgr-mgsfg
---
apiVersion: "v1"
kind: "Pod"
metadata:
  annotations:
    kubernetes.jenkins.io/last-refresh: "1795012703898"
    buildUrl: "http://jk-b-jenkins-877:8080/job/pod-agente/10/"
    runUrl: "job/pod-agente/10/"
  labels:
    jenkins: "slave"
    jenkins/label-digest: "98f809468a4fdd008bc52ddc5f052c9fa615fb6b"
    jenkins/label: "pod-agente_10-r0fgr"
    kubernetes.jenkins.io/controller: "http___jk-b-jenkins-877_8080x"
  name: "pod-agente-10-r0fgr-mgsfg-q7jq0"
  namespace: "jenkins-agentes"
spec:
  containers:
  - args:
    - "infinity"
    command:
    - "sleep"
    image: "maven:3.9.11-eclipse-temurin-21"
    name: "maven"
    resources:
      limits:
        memory: "1Gi"
      requests:
        cpu: "500m"
        memory: "512Mi"
    volumeMounts:
    - mountPath: "/home/jenkins/agent"
      name: "workspace-volume"
      readOnly: false
  - args:
    - "infinity"
    command:
    - "sleep"
    image: "node:22.21.1-alpine"
    name: "node"
    resources:
      limits:
        memory: "512Mi"
      requests:
        cpu: "250m"
        memory: "256Mi"
    volumeMounts:
    - mountPath: "/home/jenkins/agent"
      name: "workspace-volume"
      readOnly: false
  - env:
    - name: "JENKINS_SECRET"
      value: "********"
    - name: "JENKINS_AGENT_NAME"
      value: "pod-agente-10-r0fgr-mgsfg-q7jq0"
    - name: "JENKINS_WEB_SOCKET"
      value: "true"
    - name: "REMOTING_OPTS"
      value: "-noReconnectAfter 1d"
    - name: "JENKINS_NAME"
      value: "pod-agente-10-r0fgr-mgsfg-q7jq0"
    - name: "JENKINS_AGENT_WORKDIR"
      value: "/home/jenkins/agent"
    - name: "JENKINS_URL"
      value: "http://jk-b-jenkins-877:8080/"
    image: "jenkins/inbound-agent:3391.va_37fa_a_305d6d-1-jdk25"
    name: "jnlp"
    resources:
      requests:
        memory: "256Mi"
        cpu: "100m"
    volumeMounts:
    - mountPath: "/home/jenkins/agent"
      name: "workspace-volume"
      readOnly: false
  nodeSelector:
    kubernetes.io/os: "linux"
  restartPolicy: "Never"
  volumes:
  - emptyDir:
      medium: ""
    name: "workspace-volume"

Running on pod-agente-10-r0fgr-mgsfg-q7jq0 in /home/jenkins/agent/workspace/pod-agente
[Pipeline] {
[Pipeline] stage
[Pipeline] { (Agente listo)
[Pipeline] sh
+ date +%s%3N
+ hostname
+ echo T_AGENTE=1795012705427 INICIO=1795012702785 POD=pod-agente-10-r0fgr-mgsfg-q7jq0
T_AGENTE=1795012705427 INICIO=1795012702785 POD=pod-agente-10-r0fgr-mgsfg-q7jq0
[Pipeline] }
[Pipeline] // stage
[Pipeline] stage
[Pipeline] { (Backend)
[Pipeline] container
[Pipeline] {
[Pipeline] sh
+ head -1
+ mvn -v
Apache Maven 3.9.11 (3e54c93a704957b63ee3494413a2b544fd3d825b)
+ head -1
+ java -version
openjdk version "21.0.9" 2025-10-21 LTS
[Pipeline] }
[Pipeline] // container
[Pipeline] }
[Pipeline] // stage
[Pipeline] stage
[Pipeline] { (Frontend)
[Pipeline] container
[Pipeline] {
[Pipeline] sh
+ node -v
v22.21.1
+ npm -v
10.9.4
[Pipeline] }
[Pipeline] // container
[Pipeline] }
[Pipeline] // stage
[Pipeline] }
[Pipeline] // node
[Pipeline] }
[Pipeline] // podTemplate
[Pipeline] End of Pipeline
Finished: SUCCESS
```

## `kubectl -n jenkins-agentes get pods` cada medio segundo (solo cuando cambia)
```
[09:38:22]
No resources found in jenkins-agentes namespace.
[09:38:23]
pod-agente-10-r0fgr-mgsfg-q7jq0   0/3   ContainerCreating   0     0s
[09:38:24]
pod-agente-10-r0fgr-mgsfg-q7jq0   0/3   ContainerCreating   0     1s
[09:38:25]
pod-agente-10-r0fgr-mgsfg-q7jq0   0/3   ContainerCreating   0     2s
[09:38:25]
pod-agente-10-r0fgr-mgsfg-q7jq0   3/3   Running   0     2s
[09:38:26]
pod-agente-10-r0fgr-mgsfg-q7jq0   3/3   Running   0     3s
[09:38:27]
pod-agente-10-r0fgr-mgsfg-q7jq0   3/3   Terminating   0     4s
[09:38:28]
pod-agente-10-r0fgr-mgsfg-q7jq0   3/3   Terminating   0     5s
[09:38:29]
pod-agente-10-r0fgr-mgsfg-q7jq0   3/3   Terminating   0     6s
[09:38:30]
pod-agente-10-r0fgr-mgsfg-q7jq0   3/3   Terminating   0     7s
[09:38:31]
pod-agente-10-r0fgr-mgsfg-q7jq0   3/3   Terminating   0     8s
[09:38:32]
pod-agente-10-r0fgr-mgsfg-q7jq0   3/3   Terminating   0     9s
[09:38:33]
pod-agente-10-r0fgr-mgsfg-q7jq0   3/3   Terminating   0     10s
[09:38:34]
pod-agente-10-r0fgr-mgsfg-q7jq0   3/3   Terminating   0     11s
[09:38:35]
pod-agente-10-r0fgr-mgsfg-q7jq0   3/3   Terminating   0     12s
[09:38:36]
pod-agente-10-r0fgr-mgsfg-q7jq0   3/3   Terminating   0     13s
[09:38:37]
pod-agente-10-r0fgr-mgsfg-q7jq0   3/3   Terminating   0     14s
[09:38:38]
pod-agente-10-r0fgr-mgsfg-q7jq0   3/3   Terminating   0     15s
[09:38:39]
pod-agente-10-r0fgr-mgsfg-q7jq0   3/3   Terminating   0     16s
[09:38:40]
pod-agente-10-r0fgr-mgsfg-q7jq0   3/3   Terminating   0     17s
[09:38:41]
pod-agente-10-r0fgr-mgsfg-q7jq0   3/3   Terminating   0     18s
[09:38:42]
pod-agente-10-r0fgr-mgsfg-q7jq0   3/3   Terminating   0     19s
[09:38:43]
pod-agente-10-r0fgr-mgsfg-q7jq0   3/3   Terminating   0     20s
[09:38:44]
pod-agente-10-r0fgr-mgsfg-q7jq0   3/3   Terminating   0     21s
[09:38:45]
pod-agente-10-r0fgr-mgsfg-q7jq0   3/3   Terminating   0     22s
[09:38:46]
pod-agente-10-r0fgr-mgsfg-q7jq0   3/3   Terminating   0     23s
[09:38:47]
pod-agente-10-r0fgr-mgsfg-q7jq0   3/3   Terminating   0     24s
[09:38:48]
pod-agente-10-r0fgr-mgsfg-q7jq0   3/3   Terminating   0     25s
[09:38:49]
pod-agente-10-r0fgr-mgsfg-q7jq0   3/3   Terminating   0     26s
[09:38:50]
pod-agente-10-r0fgr-mgsfg-q7jq0   3/3   Terminating   0     27s
[09:38:51]
pod-agente-10-r0fgr-mgsfg-q7jq0   3/3   Terminating   0     28s
[09:38:52]
pod-agente-10-r0fgr-mgsfg-q7jq0   3/3   Terminating   0     29s
[09:38:53]
pod-agente-10-r0fgr-mgsfg-q7jq0   3/3   Terminating   0     30s
[09:38:54]
pod-agente-10-r0fgr-mgsfg-q7jq0   3/3   Terminating   0     31s
[09:38:55]
pod-agente-10-r0fgr-mgsfg-q7jq0   3/3   Terminating   0     32s
[09:38:56]
pod-agente-10-r0fgr-mgsfg-q7jq0   3/3   Terminating   0     33s
[09:38:57]
No resources found in jenkins-agentes namespace.
```
