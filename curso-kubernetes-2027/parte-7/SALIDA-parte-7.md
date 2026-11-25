# SALIDA de la parte 7 · Curso de Kubernetes 2027 (cultura-devops)

Generado: 2026-11-23 00:12:37 UTC · script: correr-parte-7.sh
Clúster: kind v0.30.0 · servidor v1.34.0 · nodos: 3
Contenedores de Docker vivos al empezar (ajenos a k8s-b): k8s-a-fuera-6183 k8s-a-control-plane k8s-a-worker2 k8s-a-worker

```

### 1 · Una app que tarda 30 s en arrancar, solo con livenessProbe
$ kubectl apply -f manifiestos/1-sin-startup.yaml
pod/sin-startup created
$ kubectl apply -f manifiestos/2-con-startup.yaml
pod/con-startup created
# espero 75 s
$ kubectl get pods   # a los 75 s
POD           LISTO   REINICIOS   ESTADO
con-startup   true    0           Running
sin-startup   false   3           Running
$ kubectl get events --field-selector involvedObject.name=sin-startup | grep -E "Unhealthy|Killing"
MOTIVO      VECES   MENSAJE
Unhealthy   12      Liveness probe failed: Get "http://10.244.2.26:8080/salud": dial tcp 10.244.2.26:8080: connect: connection refused
Killing     4       Container api failed liveness probe, will be restarted
$ kubectl logs sin-startup --previous
2026/11/23 00:13:23 arrancando: 30 s de preparación antes de escuchar
# con-startup: listo 35 s después de arrancar el pod, 0 reinicios esperados: 0
$ kubectl logs con-startup
2026/11/23 00:12:38 arrancando: 30 s de preparación antes de escuchar
2026/11/23 00:13:08 escuchando en :8080 tras 30023 ms

### 2 · readinessProbe: sacar un pod del Service sin reiniciarlo
$ kubectl apply -f manifiestos/3-probes.yaml
deployment.apps/api created
service/api created
$ kubectl get endpointslice -l kubernetes.io/service-name=api   # direcciones listas
api-59f5bc9954-s8sst ready=true
api-59f5bc9954-n685k ready=true
$ kubectl exec api-59f5bc9954-n685k -- wget -qO- --post-data= http://localhost:8080/fuera   # /listo empieza a dar 503
fuera
# api-59f5bc9954-n685k salió del Service 2997 ms después (readiness cada 2 s, 2 fallos)
api-59f5bc9954-s8sst ready=true
api-59f5bc9954-n685k ready=false
$ kubectl exec cliente -- sh -c "for i in $(seq 20); do wget -qO- http://api/; done" | contar pods
     20 "pod":"api-59f5bc9954-s8sst"
$ kubectl get pods -l app=api   # 20 s después
POD                    LISTO   REINICIOS
api-59f5bc9954-n685k   false   0
api-59f5bc9954-s8sst   true    0
# readiness NO reinicia: el pod se queda fuera hasta que /listo vuelva a dar 200

### 3 · livenessProbe: reiniciar un proceso colgado
$ kubectl exec api-59f5bc9954-s8sst -- wget -qO- --post-data= http://localhost:8080/colgar   # /salud deja de contestar
colgado
# api-59f5bc9954-s8sst reiniciado 9955 ms después de colgarse (liveness cada 3 s, timeout 1 s, 3 fallos); listo otra vez a los 10317 ms
$ kubectl get events --field-selector involvedObject.name=api-59f5bc9954-s8sst | grep -E 'Unhealthy|Killing'
Unhealthy   Liveness probe failed: Get "http://10.244.1.41:8080/salud": context deadline exceeded (Client.Timeout exceeded while awaiting headers)
Killing     Container api failed liveness probe, will be restarted
POD                    LISTO   REINICIOS
api-59f5bc9954-n685k   false   0
api-59f5bc9954-s8sst   true    1

### 4 · Límite de CPU: el mismo trabajo, tres límites (medido)
$ kubectl apply -f manifiestos/4-cpu.yaml
pod/cpu-200m created
pod/cpu-500m created
pod/cpu-1 created
# candado banco.lock tomado 00:19:52 UTC tras esperar 316 s · contenedores ajenos vivos: k8s-a-control-plane k8s-a-worker2 k8s-a-worker 
$ kubectl exec cpu-1 -- wget -qO- http://localhost:8080/cpu?n=25000000   # corrida 1
25000000 rondas en 983 ms (b8c7)
$ kubectl exec cpu-1 -- wget -qO- http://localhost:8080/cpu?n=25000000   # corrida 2
25000000 rondas en 983 ms (b8c7)
$ kubectl exec cpu-1 -- wget -qO- http://localhost:8080/cpu?n=25000000   # corrida 3
25000000 rondas en 978 ms (b8c7)
# cpu-1 · cpu.stat en las 3 corridas: nr_throttled +0 · throttled_usec +0 (0 ms frenado)
$ kubectl exec cpu-500m -- wget -qO- http://localhost:8080/cpu?n=25000000   # corrida 1
25000000 rondas en 1930 ms (1cee)
$ kubectl exec cpu-500m -- wget -qO- http://localhost:8080/cpu?n=25000000   # corrida 2
25000000 rondas en 1948 ms (1cee)
$ kubectl exec cpu-500m -- wget -qO- http://localhost:8080/cpu?n=25000000   # corrida 3
25000000 rondas en 1938 ms (1cee)
# cpu-500m · cpu.stat en las 3 corridas: nr_throttled +57 · throttled_usec +2143320 (2143 ms frenado)
$ kubectl exec cpu-200m -- wget -qO- http://localhost:8080/cpu?n=25000000   # corrida 1
25000000 rondas en 4878 ms (dbc6)
$ kubectl exec cpu-200m -- wget -qO- http://localhost:8080/cpu?n=25000000   # corrida 2
25000000 rondas en 4937 ms (dbc6)
$ kubectl exec cpu-200m -- wget -qO- http://localhost:8080/cpu?n=25000000   # corrida 3
25000000 rondas en 4915 ms (dbc6)
# cpu-200m · cpu.stat en las 3 corridas: nr_throttled +126 · throttled_usec +7481833 (7481 ms frenado)
# candado banco.lock soltado 00:20:20 UTC
$ kubectl exec cpu-200m -- cat /sys/fs/cgroup/cpu.max   # cuota y periodo en microsegundos
20000 100000

### 5 · Límite de memoria: OOMKilled
$ kubectl apply -f manifiestos/5-memoria.yaml
pod/memoria created
$ kubectl exec memoria -- wget -qO- "http://localhost:8080/mem?mb=30"
retengo 30 MiB
$ kubectl exec memoria -- cat /sys/fs/cgroup/memory.max /sys/fs/cgroup/memory.current
67108864
37994496
$ kubectl exec memoria -- wget -qO- "http://localhost:8080/mem?mb=60"   # 30 + 60 > 64 MiB
command terminated with exit code 137
$ kubectl get pod memoria -o jsonpath='{...lastState.terminated.reason} {...exitCode} · reinicios {...restartCount}'
OOMKilled 137 · reinicios 1

### 6 · Clases QoS
$ kubectl apply -f manifiestos/6-qos.yaml
pod/qos-guaranteed created
pod/qos-burstable created
pod/qos-besteffort created
$ kubectl get pods -o custom-columns=POD:.metadata.name,QOS:.status.qosClass ; cat /proc/1/oom_score_adj en cada uno
qos-guaranteed Guaranteed oom_score_adj=-997
qos-burstable Burstable oom_score_adj=996
qos-besteffort BestEffort oom_score_adj=1000

### 7 · HPA con carga real (medido)
$ kubectl apply -f 0-metrics-server-v0.8.0.yaml   # con --kubelet-insecure-tls para kind
apiservice.apiregistration.k8s.io/v1beta1.metrics.k8s.io unchanged
$ kubectl top nodes
NAME                  CPU(cores)   CPU(%)   MEMORY(bytes)   MEMORY(%)   
k8s-b-control-plane   157m         0%       1296Mi          8%          
k8s-b-worker          250m         1%       361Mi           2%          
k8s-b-worker2         49m          0%       398Mi           2%          
$ kubectl apply -f manifiestos/7-hpa.yaml
deployment.apps/web created
service/web created
horizontalpodautoscaler.autoscaling/web created
$ kubectl get hpa web
NAME   REFERENCE        TARGETS       MINPODS   MAXPODS   REPLICAS   AGE
web    Deployment/web   cpu: 1%/50%   1         8         1          32s
# candado banco.lock tomado 00:21:04 UTC tras esperar 1 s · contenedores ajenos vivos: k8s-a-control-plane k8s-a-worker2 k8s-a-worker 
$ kubectl apply -f 8-carga.yaml   # 4 bucles pidiendo trabajo de CPU
deployment.apps/carga created
# segundo · réplicas (listas) · uso medio de CPU sobre el request
t=0s · réplicas 1 (1 listas) · CPU 1%
t=16s · réplicas 1 (1 listas) · CPU 31%
t=32s · réplicas 4 (4 listas) · CPU 500%
t=48s · réplicas 8 (8 listas) · CPU 500%
t=63s · réplicas 8 (8 listas) · CPU 363%
t=79s · réplicas 8 (8 listas) · CPU 303%
t=94s · réplicas 8 (8 listas) · CPU 296%
t=110s · réplicas 8 (8 listas) · CPU 299%
t=126s · réplicas 8 (8 listas) · CPU 288%
t=142s · réplicas 8 (8 listas) · CPU 294%
t=157s · réplicas 8 (8 listas) · CPU 287%
t=173s · réplicas 8 (8 listas) · CPU 288%
t=188s · réplicas 8 (8 listas) · CPU 289%
t=204s · réplicas 8 (8 listas) · CPU 290%
t=220s · réplicas 8 (8 listas) · CPU 292%
t=235s · réplicas 8 (8 listas) · CPU 304%
t=251s · réplicas 8 (8 listas) · CPU 288%
t=267s · réplicas 8 (8 listas) · CPU 297%
t=282s · réplicas 8 (8 listas) · CPU 290%
t=298s · réplicas 8 (8 listas) · CPU 298%
# primera réplica nueva a los 32 s · máximo 8 réplicas, alcanzado a los 48 s
$ kubectl delete deployment carga   # se acaba la carga
deployment.apps "carga" deleted from curso7 namespace
t=1s sin carga · réplicas 8 · CPU 297%
t=11s sin carga · réplicas 8 · CPU 297%
t=21s sin carga · réplicas 8 · CPU 305%
t=32s sin carga · réplicas 8 · CPU 299%
t=42s sin carga · réplicas 8 · CPU 299%
t=53s sin carga · réplicas 8 · CPU 269%
t=63s sin carga · réplicas 8 · CPU 53%
t=74s sin carga · réplicas 8 · CPU 53%
t=84s sin carga · réplicas 8 · CPU 9%
t=94s sin carga · réplicas 8 · CPU 1%
t=105s sin carga · réplicas 8 · CPU 1%
t=115s sin carga · réplicas 8 · CPU 1%
t=126s sin carga · réplicas 8 · CPU 1%
t=136s sin carga · réplicas 8 · CPU 1%
t=147s sin carga · réplicas 8 · CPU 1%
t=157s sin carga · réplicas 8 · CPU 1%
t=167s sin carga · réplicas 8 · CPU 1%
t=178s sin carga · réplicas 8 · CPU 1%
t=188s sin carga · réplicas 8 · CPU 1%
t=199s sin carga · réplicas 8 · CPU 1%
t=209s sin carga · réplicas 8 · CPU 1%
t=219s sin carga · réplicas 8 · CPU 1%
t=230s sin carga · réplicas 8 · CPU 1%
t=241s sin carga · réplicas 8 · CPU 1%
t=251s sin carga · réplicas 8 · CPU 1%
t=262s sin carga · réplicas 8 · CPU 1%
t=272s sin carga · réplicas 8 · CPU 1%
t=282s sin carga · réplicas 8 · CPU 1%
t=293s sin carga · réplicas 8 · CPU 1%
t=303s sin carga · réplicas 8 · CPU 1%
t=314s sin carga · réplicas 8 · CPU 1%
t=324s sin carga · réplicas 8 · CPU 1%
t=335s sin carga · réplicas 8 · CPU 1%
t=345s sin carga · réplicas 8 · CPU 1%
t=355s sin carga · réplicas 8 · CPU 1%
t=366s sin carga · réplicas 2 · CPU 1%
t=376s sin carga · réplicas 1 · CPU 1%
# volvió a 1 réplica 376 s después de quitar la carga
# candado banco.lock soltado 00:32:34 UTC
$ kubectl describe hpa web | grep SuccessfulRescale
Normal   SuccessfulRescale             11m   horizontal-pod-autoscaler  New size: 4; reason: cpu resource utilization (percentage of request) above target
Normal   SuccessfulRescale             10m   horizontal-pod-autoscaler  New size: 8; reason: cpu resource utilization (percentage of request) above target
Normal   SuccessfulRescale             17s   horizontal-pod-autoscaler  New size: 2; reason: All metrics below target
Normal   SuccessfulRescale             2s    horizontal-pod-autoscaler  New size: 1; reason: All metrics below target

### 8 · Limpiar
$ kubectl delete namespace curso7
Warning: deleting cluster-scoped resources, not scoped to the provided namespace
namespace "curso7" deleted
```
