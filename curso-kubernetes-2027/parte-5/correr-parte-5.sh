#!/usr/bin/env bash
# Parte 5 · Configuración y almacenamiento. Ejecuta todo y escribe SALIDA-parte-5.md.
#   bash correr-parte-5.sh            (el clúster k8s-b tiene que existir: bash cluster-k8s-b.sh up)
set -u
cd "$(dirname "$0")"
source ./lib-k8s-b.sh
M=manifiestos
SALIDA=SALIDA-parte-5.md
NS=curso5

{
encabezado 5 correr-parte-5.sh
k delete namespace curso5 --ignore-not-found --wait=true >/dev/null
k delete pv -l nada=nada >/dev/null 2>&1
k create namespace curso5 >/dev/null

titulo "1 · El clúster de la parte 5"
x get nodes
x get storageclass

titulo "2 · ConfigMap y Secret"
aplicar $M/1-config.yaml
x get configmap app-config -o jsonpath='{.data}'; echo
aplicar $M/2-lector.yaml
k wait --for=condition=Ready pod/lector --timeout=120s >/dev/null
echo '$ kubectl exec lector -- sh -c '"'"'echo "variable: $MENSAJE"; echo "archivo: $(cat /config/MENSAJE)"; echo "subPath: $(cat /fijo/MENSAJE)"'"'"
k exec lector -- sh -c 'echo "variable: $MENSAJE"; echo "archivo: $(cat /config/MENSAJE)"; echo "subPath: $(cat /fijo/MENSAJE)"'
echo '$ kubectl exec lector -- ls /config'
k exec lector -- ls /config
echo '$ kubectl exec lector -- cat /config/app.conf'
k exec lector -- cat /config/app.conf
echo '$ kubectl exec lector -- ls -la /config   # los archivos son enlaces a una carpeta con fecha'
k exec lector -- ls -la /config | sed -n '1,8p'

titulo "3 · Cambiar el ConfigMap con el pod corriendo (medido)"
candado_tomar
for v in v2 v3 v4; do
  t0=$(ms)
  echo "\$ kubectl patch configmap app-config -p '{\"data\":{\"MENSAJE\":\"hola-$v\"}}'"
  k patch configmap app-config --type merge -p "{\"data\":{\"MENSAJE\":\"hola-$v\"}}"
  fin=""
  for i in $(seq 1 600); do
    l=$(k logs lector | grep " hola-$v$" | tail -1)
    if [ -n "$l" ]; then fin=$(echo "$l" | awk '{print $2}'); break; fi
    sleep 0.5
  done
  if [ -n "$fin" ]; then
    echo "# hola-$v: el archivo montado cambió $(( fin - t0/1000 )) s después del patch (reloj del pod, resolución 1 s)"
  else
    echo "# hola-$v: el archivo NO cambió en 300 s"
  fi
done
candado_soltar
echo '$ kubectl logs lector   # el pod anota la hora (epoch) en que ve cada valor'
k logs lector
echo '$ kubectl exec lector -- sh -c '"'"'echo "variable: $MENSAJE"; echo "archivo: $(cat /config/MENSAJE)"; echo "subPath: $(cat /fijo/MENSAJE)"'"'"
k exec lector -- sh -c 'echo "variable: $MENSAJE"; echo "archivo: $(cat /config/MENSAJE)"; echo "subPath: $(cat /fijo/MENSAJE)"'
nota "la variable solo cambia si el pod se vuelve a crear:"
echo '$ kubectl delete pod lector && kubectl apply -f 2-lector.yaml'
k delete pod lector --wait=true
docker exec -i "$CP" kubectl -n "$NS" apply -f - < $M/2-lector.yaml 2>&1
k wait --for=condition=Ready pod/lector --timeout=120s >/dev/null
echo '$ kubectl exec lector -- sh -c '"'"'echo "variable: $MENSAJE"'"'"
k exec lector -- sh -c 'echo "variable: $MENSAJE"'

titulo "4 · Un Secret no está cifrado"
echo "\$ kubectl get secret db-cred -o jsonpath='{.data.CLAVE}'"
k get secret db-cred -o jsonpath='{.data.CLAVE}'; echo
echo "\$ kubectl get secret db-cred -o jsonpath='{.data.CLAVE}' | base64 -d"
k get secret db-cred -o jsonpath='{.data.CLAVE}' | base64 -d; echo
echo '$ kubectl exec lector -- cat /secretos/CLAVE ; echo ; kubectl exec lector -- sh -c "mount | grep secretos"'
k exec lector -- cat /secretos/CLAVE; echo
k exec lector -- sh -c 'mount | grep secretos'
nota "y en etcd, la base de datos del clúster, sin cifrado en reposo configurado:"
echo '$ kubectl -n kube-system exec etcd-k8s-b-control-plane -- etcdctl get /registry/secrets/curso5/db-cred | grep -a -o "s3cr3to-v1"'
k -n kube-system exec etcd-k8s-b-control-plane -- etcdctl --endpoints=https://127.0.0.1:2379 \
  --cacert=/etc/kubernetes/pki/etcd/ca.crt --cert=/etc/kubernetes/pki/etcd/server.crt --key=/etc/kubernetes/pki/etcd/server.key \
  get /registry/secrets/curso5/db-cred | grep -a -o "s3cr3to-v1"
echo '$ grep -c encryption-provider-config /etc/kubernetes/manifests/kube-apiserver.yaml'
docker exec "$CP" grep -c encryption-provider-config /etc/kubernetes/manifests/kube-apiserver.yaml

titulo "5 · emptyDir: vive lo que vive el pod"
aplicar $M/3-emptydir.yaml
k wait --for=condition=Ready pod/compartido --timeout=120s >/dev/null
echo '$ kubectl exec compartido -c lector -- cat /datos/registro.txt   # lo escribió el OTRO contenedor'
k exec compartido -c lector -- cat /datos/registro.txt
echo '$ kubectl exec compartido -c escritor -- kill 1   # mato el contenedor escritor; el kubelet lo reinicia'
k exec compartido -c escritor -- kill 1
sleep 12
k wait --for=condition=Ready pod/compartido --timeout=120s >/dev/null
echo "\$ kubectl get pod compartido -o jsonpath='{.status.containerStatuses[?(@.name==\"escritor\")].restartCount}'"
k get pod compartido -o jsonpath='{.status.containerStatuses[?(@.name=="escritor")].restartCount}'; echo
echo '$ kubectl exec compartido -c lector -- cat /datos/registro.txt   # el emptyDir sobrevivió al reinicio'
k exec compartido -c lector -- cat /datos/registro.txt
echo '$ kubectl delete pod compartido && kubectl apply -f 3-emptydir.yaml'
k delete pod compartido --wait=true
docker exec -i "$CP" kubectl -n "$NS" apply -f - < $M/3-emptydir.yaml 2>&1
k wait --for=condition=Ready pod/compartido --timeout=120s >/dev/null
echo '$ kubectl exec compartido -c lector -- cat /datos/registro.txt   # pod nuevo: emptyDir nuevo'
k exec compartido -c lector -- cat /datos/registro.txt

titulo "6 · PVC con aprovisionamiento dinámico"
aplicar $M/4-pvc.yaml
sleep 3
x get pvc datos -o custom-columns=NOMBRE:.metadata.name,ESTADO:.status.phase,CLASE:.spec.storageClassName
echo '$ kubectl describe pvc datos | tail -2'
k describe pvc datos | tail -2
x get pv
aplicar $M/5-pod-pvc.yaml
k wait --for=condition=Ready pod/usa-pvc --timeout=120s >/dev/null
x get pvc datos -o custom-columns=NOMBRE:.metadata.name,ESTADO:.status.phase,VOLUMEN:.spec.volumeName,TAMANO:.status.capacity.storage
x get pv -o custom-columns=PV:.metadata.name,RECLAMO:.spec.persistentVolumeReclaimPolicy,ESTADO:.status.phase,PVC:.spec.claimRef.name
PV=$(k get pvc datos -o jsonpath='{.spec.volumeName}')
NODO=$(k get pod usa-pvc -o jsonpath='{.spec.nodeName}')
echo "\$ kubectl get pv $PV -o jsonpath='{.spec.hostPath.path} {.spec.nodeAffinity.required.nodeSelectorTerms[0].matchExpressions[0].values[0]}'"
k get pv "$PV" -o jsonpath='{.spec.hostPath.path} {.spec.nodeAffinity.required.nodeSelectorTerms[0].matchExpressions[0].values[0]}'; echo
echo '$ kubectl exec usa-pvc -- sh -c "echo pedido 41 > /datos/pedido.txt"'
k exec usa-pvc -- sh -c "echo pedido 41 > /datos/pedido.txt"
echo '$ kubectl delete pod usa-pvc && kubectl apply -f 5-pod-pvc.yaml'
k delete pod usa-pvc --wait=true
docker exec -i "$CP" kubectl -n "$NS" apply -f - < $M/5-pod-pvc.yaml 2>&1
k wait --for=condition=Ready pod/usa-pvc --timeout=120s >/dev/null
echo '$ kubectl exec usa-pvc -- cat /datos/pedido.txt   # pod nuevo, mismo PVC'
k exec usa-pvc -- cat /datos/pedido.txt
echo "\$ kubectl get pod usa-pvc -o jsonpath='{.spec.nodeName}'   # antes estaba en $NODO"
k get pod usa-pvc -o jsonpath='{.spec.nodeName}'; echo
echo "\$ docker exec $NODO ls $(k get pv "$PV" -o jsonpath='{.spec.hostPath.path}')   # el disco real, en el nodo"
docker exec "$NODO" ls "$(k get pv "$PV" -o jsonpath='{.spec.hostPath.path}')" 2>&1

titulo "7 · Borrar el PVC con reclaimPolicy Delete"
DIR=$(k get pv "$PV" -o jsonpath='{.spec.hostPath.path}')
echo '$ kubectl delete pod usa-pvc && kubectl delete pvc datos'
k delete pod usa-pvc --wait=true
k delete pvc datos --wait=true
sleep 10
x get pv "$PV"
echo "\$ docker exec $NODO ls $DIR"
docker exec "$NODO" ls "$DIR" 2>&1

titulo "8 · La misma prueba con reclaimPolicy Retain"
aplicar $M/6-retener.yaml
k wait --for=condition=Ready pod/usa-retener --timeout=120s >/dev/null
PV2=$(k get pvc datos-retener -o jsonpath='{.spec.volumeName}')
NODO2=$(k get pod usa-retener -o jsonpath='{.spec.nodeName}')
DIR2=$(k get pv "$PV2" -o jsonpath='{.spec.hostPath.path}')
echo '$ kubectl delete pod usa-retener && kubectl delete pvc datos-retener'
k delete pod usa-retener --wait=true
k delete pvc datos-retener --wait=true
sleep 10
x get pv "$PV2" -o custom-columns=PV:.metadata.name,RECLAMO:.spec.persistentVolumeReclaimPolicy,ESTADO:.status.phase,PVC:.spec.claimRef.name
echo "\$ docker exec $NODO2 cat $DIR2/pedido.txt   # los datos siguen en el nodo"
docker exec "$NODO2" cat "$DIR2/pedido.txt" 2>&1
nota "un PVC nuevo NO se engancha solo a un PV Released: hay que limpiarlo o reutilizarlo a mano."
echo '$ kubectl delete pv '"$PV2"'   # el PV se borra; la carpeta del nodo, NO (Retain)'
k delete pv "$PV2"
echo "\$ docker exec $NODO2 ls $DIR2"
docker exec "$NODO2" ls "$DIR2" 2>&1
docker exec "$NODO2" rm -rf "$DIR2"

titulo "9 · Limpiar"
echo '$ kubectl delete namespace curso5'
k delete namespace curso5
k delete storageclass retener >/dev/null
pie
} 2>&1 | tee "$SALIDA"
