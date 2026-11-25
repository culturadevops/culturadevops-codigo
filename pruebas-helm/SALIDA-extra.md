# SALIDA (2.ª parte) — Helm 4 (vídeo 407)

Generado 2026-10-13 20:50 UTC con `python correr_extra.py`.

## 7 · Ver lo que se va a aplicar, sin clúster

### lint

`$ helm4 lint demo`

```
==> Linting demo
[INFO] Chart.yaml: icon is recommended

1 chart(s) linted, 0 chart(s) failed
```
(código de salida 0)

### un error en el chart

`$ (replicaCount: "tres") helm4 lint demo`

```
cannot load values.yaml: cannot unmarshal yaml document: error converting YAML to JSON: yaml: line 6: mapping values are not allowed in this context

Error: 1 chart(s) linted, 1 chart(s) failed
```
(código de salida 0)

### template: los manifiestos, sin aplicar nada

`$ helm4 template web ./demo | grep -E '^kind:' | sort | uniq -c`

```
1 kind: Deployment
      1 kind: Pod
      1 kind: Service
      1 kind: ServiceAccount
```
(código de salida 0)

## 8 · El chart en un registro OCI

### empaquetar y subir

`$ helm4 push demo-0.1.0.tgz oci://registro:5000/charts --plain-http`

```
Pushed: registro:5000/charts/demo:0.1.0
Digest: sha256:5a77f090ea3f1b91af76bf3f471703f0f8e85222779e81f7e62fe5d16297ec67
```
(código de salida 0)

### leerlo desde el registro

`$ helm4 show chart oci://registro:5000/charts/demo --plain-http`

```
appVersion: 1.16.0
name: demo
version: 0.1.0
```
(código de salida 0)

### instalarlo desde ahí, con un valor cambiado

`$ helm4 install web oci://registro:5000/charts/demo --set replicaCount=2 …`

```
STATUS: deployed
REVISION: 1
réplicas=2
```
(código de salida 0)

### qué valores cambié

`$ helm4 get values web -n oci`

```
USER-SUPPLIED VALUES:
replicaCount: 2
```
(código de salida 0)
