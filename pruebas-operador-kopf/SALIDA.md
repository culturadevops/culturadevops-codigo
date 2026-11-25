# SALIDA — Operador de Kubernetes en Python con kopf (cultura-devops 801)

> Corrida del 2026-11-05 13:06. kind v0.30.0 (Kubernetes v1.34.0, clúster cd801) · python:3.13.17-slim · kopf 1.45.2 · kubernetes (cliente) 37.0.1.
> Operador en un contenedor `docker run --rm --cpus 1 --network kind`, fuera del clúster, con el kubeconfig interno de kind.
> Guion: `ejecutar.sh` (funcional, sin cronómetro). Modelo: golandia 517 (`canales/golandia/recursos/pruebas-operador`, kubebuilder en Go).
>
> Notas de la corrida (no van al vídeo como hallazgo):
> - 1.ª corrida: arrancar kopf justo después de crear la CRD dio `429 storage is (re)initializing` y kopf reintentó solo. Por eso el guion espera 15 s tras `Established`.
> - El hueco de ~70 s entre el arranque de kopf y el primer handler es del propio guion (espera fija de 60 s), no de kopf. NO es un tiempo de reacción.
> - La memoria (79 MiB) es UNA lectura de `docker stats`, no una medida repetida.

```
### 0 · Versiones
$ kind version ; kubectl version (servidor)
kind v0.30.0 go1.26.5 windows/amd64
Server Version: v1.34.0
$ python --version ; pip show kopf kubernetes   # dentro de la imagen del operador
Python 3.13.17
Name: kopf
Version: 1.45.2
Name: kubernetes
Version: 37.0.1
$ docker image ls cd801-operador:1
cd801-operador:1  377MB

### 1 · La CRD (escrita a mano: kopf no la genera) y el operador
$ wc -l crd.yaml operador.py
  34 crd.yaml
  79 operador.py
 113 total
$ kubectl apply -f crd.yaml
customresourcedefinition.apiextensions.k8s.io/paginawebs.web.culturadevops.dev created
$ kubectl get crd -o name | grep paginaweb
customresourcedefinition.apiextensions.k8s.io/paginawebs.web.culturadevops.dev

### 2 · El operador en marcha (sin vigilar a los hijos)
$ docker run --rm --cpus 1 --network kind cd801-operador:1   # kopf run --standalone --namespace default operador.py
[2026-11-05 13:06:16,273] kopf._core.engines.a [INFO    ] Initial authentication has been initiated.
[2026-11-05 13:06:16,277] kopf.activities.auth [INFO    ] Activity 'login_via_client' succeeded.
[2026-11-05 13:06:16,278] kopf._core.engines.a [INFO    ] Initial authentication has finished.
$ cat pagina.yaml
apiVersion: web.culturadevops.dev/v1
kind: PaginaWeb
metadata:
  name: hola
spec:
  replicas: 2
  mensaje: Hola desde un operador en Python
$ kubectl apply -f pagina.yaml
paginaweb.web.culturadevops.dev/hola created
$ kubectl get deployment,service,configmap -l app=hola -o name ; kubectl get paginaweb
deployment.apps/hola
service/hola
configmap/hola
NAME   REPLICAS   LISTAS   MENSAJE
hola   2                   Hola desde un operador en Python
$ kubectl get deployment hola -o jsonpath='{.metadata.ownerReferences[0].kind}/{.metadata.ownerReferences[0].name}'
PaginaWeb/hola
$ kubectl run prueba --rm -i --image=busybox:1.37 --restart=Never -- wget -qO- http://hola
<h1>Hola desde un operador en Python</h1>
$ docker logs cd801-op   # lo que dijo kopf
[2026-11-05 13:06:16,277] kopf.activities.auth [INFO    ] Activity 'login_via_client' succeeded.
[2026-11-05 13:07:27,686] kopf.objects         [INFO    ] [default/hola] configmap creado · deployment creado · service creado
[2026-11-05 13:07:27,686] kopf.objects         [INFO    ] [default/hola] Handler 'reconciliar' succeeded.
[2026-11-05 13:07:27,687] kopf.objects         [INFO    ] [default/hola] Creation is processed: 1 succeeded; 0 failed.

### 3 · Cambiar la PaginaWeb: kopf llama al handler de update
$ kubectl patch paginaweb hola --type merge -p '{"spec":{"replicas":4}}'
paginaweb.web.culturadevops.dev/hola patched
$ kubectl get deployment hola ; kubectl get paginaweb
NAME   READY   UP-TO-DATE   AVAILABLE   AGE
hola   4/4     4            4           14s
NAME   REPLICAS   LISTAS   MENSAJE
hola   4                   Hola desde un operador en Python
$ kubectl get paginaweb hola -o jsonpath='{.metadata.annotations.kopf\.zalando\.org/last-handled-configuration}'
{"spec":{"mensaje":"Hola desde un operador en Python","replicas":4}}


### 4 · Borrar el Deployment a mano, SIN vigilar a los hijos
$ kubectl delete deployment hola
deployment.apps "hola" deleted from default namespace
$ kubectl get deployment hola   # 30 segundos después
Error from server (NotFound): deployments.apps "hola" not found

### 5 · Reiniciar el operador: el handler de resume lo repara
$ docker restart del operador (VIGILAR_HIJOS=1)
$ kubectl get deployment hola
NAME   READY   UP-TO-DATE   AVAILABLE   AGE
hola   4/4     4            4           8s
$ docker logs cd801-op
[2026-11-05 13:08:13,276] kopf.objects         [INFO    ] [default/hola] configmap actualizado · deployment creado · service actualizado

### 6 · Ahora vigilando a los hijos: borrar el Deployment otra vez
$ kubectl delete deployment hola
deployment.apps "hola" deleted from default namespace
$ kubectl get deployment hola
NAME   READY   UP-TO-DATE   AVAILABLE   AGE
hola   4/4     4            4           8s
$ docker logs cd801-op
[2026-11-05 13:08:22,037] kopf.objects         [INFO    ] [default/hola] alguien borró el deployment hola: lo vuelvo a crear
[2026-11-05 13:08:22,063] kopf.objects         [INFO    ] [default/hola] configmap actualizado · deployment creado · service actualizado
$ kubectl get paginaweb   # el estado, ahora que alguien lo rellena
NAME   REPLICAS   LISTAS   MENSAJE
hola   4          4        Hola desde un operador en Python

### 7 · La validación de la CRD
$ kubectl patch paginaweb hola --type merge -p '{"spec":{"replicas":50}}'
The PaginaWeb "hola" is invalid: spec.replicas: Invalid value: 50: spec.replicas in body should be less than or equal to 10

### 8 · Memoria del operador
$ docker stats --no-stream cd801-op
cd801-op  79.26MiB / 15.36GiB

### 9 · Borrar la PaginaWeb: se va todo lo suyo
$ kubectl delete paginaweb hola
paginaweb.web.culturadevops.dev "hola" deleted from default namespace
$ kubectl get deployment,service,configmap hola
Error from server (NotFound): deployments.apps "hola" not found
Error from server (NotFound): services "hola" not found
Error from server (NotFound): configmaps "hola" not found
```
