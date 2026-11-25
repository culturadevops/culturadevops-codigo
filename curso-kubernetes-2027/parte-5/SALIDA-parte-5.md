# SALIDA de la parte 5 · Curso de Kubernetes 2027 (cultura-devops)

Generado: 2026-11-22 23:58:57 UTC · script: correr-parte-5.sh
Clúster: kind v0.30.0 · servidor v1.34.0 · nodos: 3
Contenedores de Docker vivos al empezar (ajenos a k8s-b): k8s-a-control-plane k8s-a-worker2 k8s-a-worker

```

### 1 · El clúster de la parte 5
$ kubectl get nodes
NAME                  STATUS   ROLES           AGE   VERSION
k8s-b-control-plane   Ready    control-plane   21m   v1.34.0
k8s-b-worker          Ready    <none>          21m   v1.34.0
k8s-b-worker2         Ready    <none>          21m   v1.34.0
$ kubectl get storageclass
NAME                 PROVISIONER             RECLAIMPOLICY   VOLUMEBINDINGMODE      ALLOWVOLUMEEXPANSION   AGE
standard (default)   rancher.io/local-path   Delete          WaitForFirstConsumer   false                  21m

### 2 · ConfigMap y Secret
$ kubectl apply -f manifiestos/1-config.yaml
configmap/app-config created
secret/db-cred created
$ kubectl get configmap app-config -o jsonpath={.data}
{"MENSAJE":"hola-v1","app.conf":"nivel_log=info\ncolor=azul\n"}
$ kubectl apply -f manifiestos/2-lector.yaml
pod/lector created
$ kubectl exec lector -- sh -c 'echo "variable: $MENSAJE"; echo "archivo: $(cat /config/MENSAJE)"; echo "subPath: $(cat /fijo/MENSAJE)"'
variable: hola-v1
archivo: hola-v1
subPath: hola-v1
$ kubectl exec lector -- ls /config
MENSAJE
app.conf
$ kubectl exec lector -- cat /config/app.conf
nivel_log=info
color=azul
$ kubectl exec lector -- ls -la /config   # los archivos son enlaces a una carpeta con fecha
total 12
drwxrwxrwx    3 root     root          4096 Nov 22 23:59 .
drwxr-xr-x    1 root     root          4096 Nov 22 23:59 ..
drwxr-xr-x    2 root     root          4096 Nov 22 23:59 ..2026_11_22_23_59_41.2613334138
lrwxrwxrwx    1 root     root            32 Nov 22 23:59 ..data -> ..2026_11_22_23_59_41.2613334138
lrwxrwxrwx    1 root     root            14 Nov 22 23:59 MENSAJE -> ..data/MENSAJE
lrwxrwxrwx    1 root     root            15 Nov 22 23:59 app.conf -> ..data/app.conf

### 3 · Cambiar el ConfigMap con el pod corriendo (medido)
# candado banco.lock tomado 00:16:30 UTC tras esperar 1007 s · contenedores ajenos vivos: kindccm-48ac4abbc77d k8s-a-cpk k8s-a-control-plane k8s-a-worker2 k8s-a-worker 
$ kubectl patch configmap app-config -p '{"data":{"MENSAJE":"hola-v2"}}'
configmap/app-config patched
# hola-v2: el archivo montado cambió 37 s después del patch (reloj del pod, resolución 1 s)
$ kubectl patch configmap app-config -p '{"data":{"MENSAJE":"hola-v3"}}'
configmap/app-config patched
# hola-v3: el archivo montado cambió 84 s después del patch (reloj del pod, resolución 1 s)
$ kubectl patch configmap app-config -p '{"data":{"MENSAJE":"hola-v4"}}'
configmap/app-config patched
# hola-v4: el archivo montado cambió 62 s después del patch (reloj del pod, resolución 1 s)
# candado banco.lock soltado 00:19:37 UTC
$ kubectl logs lector   # el pod anota la hora (epoch) en que ve cada valor
cambio 1795391982 hola-v1
cambio 1795393028 hola-v2
cambio 1795393113 hola-v3
cambio 1795393176 hola-v4
$ kubectl exec lector -- sh -c 'echo "variable: $MENSAJE"; echo "archivo: $(cat /config/MENSAJE)"; echo "subPath: $(cat /fijo/MENSAJE)"'
variable: hola-v1
archivo: hola-v4
subPath: hola-v1
# la variable solo cambia si el pod se vuelve a crear:
$ kubectl delete pod lector && kubectl apply -f 2-lector.yaml
pod "lector" deleted from curso5 namespace
pod/lector created
$ kubectl exec lector -- sh -c 'echo "variable: $MENSAJE"'
variable: hola-v4

### 4 · Un Secret no está cifrado
$ kubectl get secret db-cred -o jsonpath='{.data.CLAVE}'
czNjcjN0by12MQ==
$ kubectl get secret db-cred -o jsonpath='{.data.CLAVE}' | base64 -d
s3cr3to-v1
$ kubectl exec lector -- cat /secretos/CLAVE ; echo ; kubectl exec lector -- sh -c "mount | grep secretos"
s3cr3to-v1
tmpfs on /secretos type tmpfs (ro,relatime,size=16101036k,noswap)
# y en etcd, la base de datos del clúster, sin cifrado en reposo configurado:
$ kubectl -n kube-system exec etcd-k8s-b-control-plane -- etcdctl get /registry/secrets/curso5/db-cred | grep -a -o "s3cr3to-v1"
s3cr3to-v1
s3cr3to-v1
$ grep -c encryption-provider-config /etc/kubernetes/manifests/kube-apiserver.yaml
0

### 5 · emptyDir: vive lo que vive el pod
$ kubectl apply -f manifiestos/3-emptydir.yaml
pod/compartido created
$ kubectl exec compartido -c lector -- cat /datos/registro.txt   # lo escribió el OTRO contenedor
escrito 00:20:11
$ kubectl exec compartido -c escritor -- kill 1   # mato el contenedor escritor; el kubelet lo reinicia
$ kubectl get pod compartido -o jsonpath='{.status.containerStatuses[?(@.name=="escritor")].restartCount}'
1
$ kubectl exec compartido -c lector -- cat /datos/registro.txt   # el emptyDir sobrevivió al reinicio
escrito 00:20:11
escrito 00:20:12
$ kubectl delete pod compartido && kubectl apply -f 3-emptydir.yaml
pod "compartido" deleted from curso5 namespace
pod/compartido created
$ kubectl exec compartido -c lector -- cat /datos/registro.txt   # pod nuevo: emptyDir nuevo
escrito 00:20:56

### 6 · PVC con aprovisionamiento dinámico
$ kubectl apply -f manifiestos/4-pvc.yaml
persistentvolumeclaim/datos created
$ kubectl get pvc datos -o custom-columns=NOMBRE:.metadata.name,ESTADO:.status.phase,CLASE:.spec.storageClassName
NOMBRE   ESTADO    CLASE
datos    Pending   standard
$ kubectl describe pvc datos | tail -2
  ----    ------                ----  ----                         -------
  Normal  WaitForFirstConsumer  3s    persistentvolume-controller  waiting for first consumer to be created before binding
$ kubectl get pv
No resources found
$ kubectl apply -f manifiestos/5-pod-pvc.yaml
pod/usa-pvc created
$ kubectl get pvc datos -o custom-columns=NOMBRE:.metadata.name,ESTADO:.status.phase,VOLUMEN:.spec.volumeName,TAMANO:.status.capacity.storage
NOMBRE   ESTADO   VOLUMEN                                    TAMANO
datos    Bound    pvc-8e5d614d-5851-432d-bef4-89dd485271e4   1Gi
$ kubectl get pv -o custom-columns=PV:.metadata.name,RECLAMO:.spec.persistentVolumeReclaimPolicy,ESTADO:.status.phase,PVC:.spec.claimRef.name
PV                                         RECLAMO   ESTADO   PVC
pvc-8e5d614d-5851-432d-bef4-89dd485271e4   Delete    Bound    datos
$ kubectl get pv pvc-8e5d614d-5851-432d-bef4-89dd485271e4 -o jsonpath='{.spec.hostPath.path} {.spec.nodeAffinity.required.nodeSelectorTerms[0].matchExpressions[0].values[0]}'
/var/local-path-provisioner/pvc-8e5d614d-5851-432d-bef4-89dd485271e4_curso5_datos k8s-b-worker2
$ kubectl exec usa-pvc -- sh -c "echo pedido 41 > /datos/pedido.txt"
$ kubectl delete pod usa-pvc && kubectl apply -f 5-pod-pvc.yaml
pod "usa-pvc" deleted from curso5 namespace
pod/usa-pvc created
$ kubectl exec usa-pvc -- cat /datos/pedido.txt   # pod nuevo, mismo PVC
pedido 41
$ kubectl get pod usa-pvc -o jsonpath='{.spec.nodeName}'   # antes estaba en k8s-b-worker2
k8s-b-worker2
$ docker exec k8s-b-worker2 ls /var/local-path-provisioner/pvc-8e5d614d-5851-432d-bef4-89dd485271e4_curso5_datos   # el disco real, en el nodo
pedido.txt

### 7 · Borrar el PVC con reclaimPolicy Delete
$ kubectl delete pod usa-pvc && kubectl delete pvc datos
pod "usa-pvc" deleted from curso5 namespace
persistentvolumeclaim "datos" deleted from curso5 namespace
$ kubectl get pv pvc-8e5d614d-5851-432d-bef4-89dd485271e4
Error from server (NotFound): persistentvolumes "pvc-8e5d614d-5851-432d-bef4-89dd485271e4" not found
$ docker exec k8s-b-worker2 ls /var/local-path-provisioner/pvc-8e5d614d-5851-432d-bef4-89dd485271e4_curso5_datos
ls: cannot access '/var/local-path-provisioner/pvc-8e5d614d-5851-432d-bef4-89dd485271e4_curso5_datos': No such file or directory

### 8 · La misma prueba con reclaimPolicy Retain
$ kubectl apply -f manifiestos/6-retener.yaml
storageclass.storage.k8s.io/retener created
persistentvolumeclaim/datos-retener created
pod/usa-retener created
$ kubectl delete pod usa-retener && kubectl delete pvc datos-retener
pod "usa-retener" deleted from curso5 namespace
persistentvolumeclaim "datos-retener" deleted from curso5 namespace
$ kubectl get pv pvc-81d858a2-eb86-46ff-9054-deb70aa73e27 -o custom-columns=PV:.metadata.name,RECLAMO:.spec.persistentVolumeReclaimPolicy,ESTADO:.status.phase,PVC:.spec.claimRef.name
PV                                         RECLAMO   ESTADO     PVC
pvc-81d858a2-eb86-46ff-9054-deb70aa73e27   Retain    Released   datos-retener
$ docker exec k8s-b-worker2 cat /var/local-path-provisioner/pvc-81d858a2-eb86-46ff-9054-deb70aa73e27_curso5_datos-retener/pedido.txt   # los datos siguen en el nodo
pedido 42 guardado
# un PVC nuevo NO se engancha solo a un PV Released: hay que limpiarlo o reutilizarlo a mano.
$ kubectl delete pv pvc-81d858a2-eb86-46ff-9054-deb70aa73e27   # el PV se borra; la carpeta del nodo, NO (Retain)
Warning: deleting cluster-scoped resources, not scoped to the provided namespace
persistentvolume "pvc-81d858a2-eb86-46ff-9054-deb70aa73e27" deleted
$ docker exec k8s-b-worker2 ls /var/local-path-provisioner/pvc-81d858a2-eb86-46ff-9054-deb70aa73e27_curso5_datos-retener
pedido.txt

### 9 · Limpiar
$ kubectl delete namespace curso5
Warning: deleting cluster-scoped resources, not scoped to the provided namespace
namespace "curso5" deleted
```
