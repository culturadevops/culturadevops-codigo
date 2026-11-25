# SALIDA-877 · Jenkins en Kubernetes: agentes como pods

> Corrida 2026-11-18 14:21 UTC. Generado por `k8s/correr_877.py`. Candado `_logs/banco.lock` tomado durante toda la corrida.
> Otros contenedores vivos en la máquina al empezar (carga ajena): 'determined_chatelet', 'jk-a-fijo', 'jk-a-jenkins', 'jk-b-jenkins-877', 'jk-b-k8s-control-plane'
> Docker: 24 CPU, 15.4 GiB.

## Versiones
- Jenkins 2.580.2 (imagen jk-b-jenkins:2.580.2, 73 plugins fijados) · plugin kubernetes 4560.vc25b_83890c34
- kind v0.30.0 go1.26.5 windows/amd64 · nodo v1.34.0 (containerd://2.1.3)
- Nodo asignable: 24 CPU · 16101032Ki de memoria

## 1 · Arranque de un pod-agente en FRÍO (el nodo no tiene las imágenes; `crictl rmi` antes de cada corrida)
Espera = del inicio del build al primer `sh` dentro del pod (reloj del contenedor contra `startTimeInMillis`; mismo núcleo, misma hora).
- frío 1: build #2 · espera 36.1 s · build entero 37.7 s · pod borrado 31.6 s después · Maven 3.9.11 · Node v22.21.1
    - kubelet: Successfully pulled image "maven:3.9.11-eclipse-temurin-21" in 14.625s (14.625s including waiting). Image size: 242329466 bytes.
    - kubelet: Successfully pulled image "node:22.21.1-alpine" in 5.912s (5.912s including waiting). Image size: 56737378 bytes.
    - kubelet: Successfully pulled image "jenkins/inbound-agent:3391.va_37fa_a_305d6d-1-jdk25" in 12.646s (12.646s including waiting). Image size: 225036571 bytes.
- frío 2: build #3 · espera 39.0 s · build entero 40.5 s · pod borrado 31.1 s después · Maven 3.9.11 · Node v22.21.1
    - kubelet: Successfully pulled image "maven:3.9.11-eclipse-temurin-21" in 13.347s (13.347s including waiting). Image size: 242329466 bytes.
    - kubelet: Successfully pulled image "node:22.21.1-alpine" in 5.822s (5.822s including waiting). Image size: 56737378 bytes.
    - kubelet: Successfully pulled image "jenkins/inbound-agent:3391.va_37fa_a_305d6d-1-jdk25" in 16.614s (16.614s including waiting). Image size: 225036571 bytes.
- frío 3: build #4 · espera 36.5 s · build entero 38.0 s · pod borrado 30.4 s después · Maven 3.9.11 · Node v22.21.1
    - kubelet: Successfully pulled image "maven:3.9.11-eclipse-temurin-21" in 14.686s (14.686s including waiting). Image size: 242329466 bytes.
    - kubelet: Successfully pulled image "node:22.21.1-alpine" in 6.415s (6.415s including waiting). Image size: 56737378 bytes.
    - kubelet: Successfully pulled image "jenkins/inbound-agent:3391.va_37fa_a_305d6d-1-jdk25" in 12.663s (12.663s including waiting). Image size: 225036571 bytes.

## 2 · Arranque de un pod-agente en CALIENTE (las imágenes ya están en el nodo)
- caliente 1: build #5 · espera 3.2 s · build entero 4.7 s · pod borrado 29.8 s después · Maven 3.9.11 · Node v22.21.1
    - kubelet: Container image "maven:3.9.11-eclipse-temurin-21" already present on machine
    - kubelet: Container image "node:22.21.1-alpine" already present on machine
    - kubelet: Container image "jenkins/inbound-agent:3391.va_37fa_a_305d6d-1-jdk25" already present on machine
- caliente 2: build #6 · espera 2.4 s · build entero 4.0 s · pod borrado 31.0 s después · Maven 3.9.11 · Node v22.21.1
    - kubelet: Container image "maven:3.9.11-eclipse-temurin-21" already present on machine
    - kubelet: Container image "node:22.21.1-alpine" already present on machine
    - kubelet: Container image "jenkins/inbound-agent:3391.va_37fa_a_305d6d-1-jdk25" already present on machine
- caliente 3: build #7 · espera 3.0 s · build entero 4.5 s · pod borrado 31.1 s después · Maven 3.9.11 · Node v22.21.1
    - kubelet: Container image "maven:3.9.11-eclipse-temurin-21" already present on machine
    - kubelet: Container image "node:22.21.1-alpine" already present on machine
    - kubelet: Container image "jenkins/inbound-agent:3391.va_37fa_a_305d6d-1-jdk25" already present on machine
- caliente 4: build #8 · espera 2.8 s · build entero 4.3 s · pod borrado 29.5 s después · Maven 3.9.11 · Node v22.21.1
    - kubelet: Container image "maven:3.9.11-eclipse-temurin-21" already present on machine
    - kubelet: Container image "node:22.21.1-alpine" already present on machine
    - kubelet: Container image "jenkins/inbound-agent:3391.va_37fa_a_305d6d-1-jdk25" already present on machine
- caliente 5: build #9 · espera 2.9 s · build entero 4.4 s · pod borrado 31.1 s después · Maven 3.9.11 · Node v22.21.1
    - kubelet: Container image "maven:3.9.11-eclipse-temurin-21" already present on machine
    - kubelet: Container image "node:22.21.1-alpine" already present on machine
    - kubelet: Container image "jenkins/inbound-agent:3391.va_37fa_a_305d6d-1-jdk25" already present on machine

## ¿Mismo resultado en todas las corridas?
- versiones vistas dentro del pod: {('3.9.11', 'v22.21.1')} → SÍ, idénticas
- pods distintos: 8 de 8 builds (uno nuevo por build)
- pods que quedan en `jenkins-agentes` al acabar cada build: 0 en las 8 corridas

## Resumen del arranque
- FRÍO   mediana de 3: **36.5 s** (corridas: 36.1, 39.0, 36.5)
- CALIENTE mediana de 5: **2.9 s** (corridas: 3.2, 2.4, 3.0, 2.8, 2.9)
- build entero (3 etapas cortas): frío 38.0 s · caliente 4.4 s

## 3 · Tres builds a la vez (job `ocupado`: el mismo pod, 25 s de trabajo)

`$ kubectl get pods -n jenkins-agentes`
```
NAME                          READY   STATUS    RESTARTS   AGE
ocupado-1-8w1g0-v0zrm-0chq1   3/3     Running   0          5s
ocupado-2-2psjs-h8svf-97r6v   3/3     Running   0          4s
ocupado-3-4zll0-x7v2k-4trn9   3/3     Running   0          4s
```

`$ kubectl describe node | (recursos asignados)`
```
(Total limits may be over 100 percent, i.e., overcommitted.)
  Resource           Requests      Limits
  --------           --------      ------
  cpu                3500m (14%)   100m (0%)
  memory             3362Mi (21%)  4998Mi (31%)
  ephemeral-storage  0 (0%)        0 (0%)
```
- peticiones de UN pod-agente: [('maven', {'cpu': '500m', 'memory': '512Mi'}), ('node', {'cpu': '250m', 'memory': '256Mi'}), ('jnlp', {'cpu': '100m', 'memory': '256Mi'})]
- resultado de los tres: ['SUCCESS', 'SUCCESS', 'SUCCESS']

`$ kubectl get pods -n jenkins-agentes   # al terminar`
```
No resources found in jenkins-agentes namespace.
```
- los tres pods desaparecieron 30.1 s después del último build

## 4 · Un pod que pide 32 CPU en un nodo con 24 (job `pendiente`)
- a los 301 s: building=True result=None

`$ kubectl get pods -n jenkins-agentes`
```
NAME                            READY   STATUS    RESTARTS   AGE
pendiente-2-dzhqz-vm1hh-0xwlr   0/2     Pending   0          5m
```
- evento FailedScheduling (×1): 0/1 nodes are available: 1 Insufficient cpu. no new claims to deallocate, preemption: 0/1 nodes are available: 1 Preemption is not helpful for scheduling.
- la consola repite «Still waiting to schedule task» 1 veces

`$ consola del build (extracto)`
```
Created Pod: kind jenkins-agentes/pendiente-2-dzhqz-vm1hh-0xwlr
	Pod [Pending][Unschedulable] 0/1 nodes are available: 1 Insufficient cpu. no new claims to deallocate, preemption: 0/1 nodes are available: 1 Preemption is not helpful for scheduling.
	Pod [Pending][Unschedulable] 0/1 nodes are available: 1 Insufficient cpu. no new claims to deallocate, preemption: 0/1 nodes are available: 1 Preemption is not helpful for scheduling.
	Pod [Pending][Unschedulable] 0/1 nodes are available: 1 Insufficient cpu. no new claims to deallocate, preemption: 0/1 nodes are available: 1 Preemption is not helpf
```

`$ kubectl get pods -n jenkins-agentes   # 180 s después de abortar`
```
NAME                            READY   STATUS    RESTARTS   AGE
pendiente-2-dzhqz-vm1hh-0xwlr   0/2     Pending   0          8m1s
```
- 180 s después de abortar el build, el pod Pending SEGUÍA ahí: lo borro a mano con kubectl delete pod

## 5 · Un contenedor con límite de 128 MiB que reserva 300 MiB (job `oom`)
- oom 1: build #2 → **ABORTED** en 4.4 s

`$ consola del build (líneas clave)`
```
Container [node] terminated [OOMKilled] No message
- node -- terminated (137)
Agent oom-2-9nprc-55mj4-8g7m9 was deleted; cancelling node body
Agent was removed
Finished: ABORTED
```
- oom 2: build #3 → **ABORTED** en 3.9 s
- oom 3: build #4 → **ABORTED** en 4.0 s
- resultados: ['ABORTED', 'ABORTED', 'ABORTED']

## Lo que queda en el clúster

`$ kubectl get pods -n jenkins-agentes`
```
No resources found in jenkins-agentes namespace.
```
