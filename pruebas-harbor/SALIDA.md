# SALIDA — Harbor (vídeo 331)

Generado 2026-10-07 22:20 UTC con `python correr.py`. Harbor v2.15.3 con Trivy, dentro de docker:dind.

## 1 · Instalar Harbor (instalador online + Trivy)

### harbor.yml (lo que cambié)

`$ grep -E '^(hostname|harbor_admin_password|#https|http:)' harbor.yml`

```
5:hostname: harbor.local
8:http:
10:  port: 80
13:#https:
47:harbor_admin_password: Harbor-de-prueba-123
66:data_volume: /data
```

### install.sh --with-trivy

`$ ./install.sh --with-trivy`

```
[Step 0]: checking if docker is installed ...
[Step 1]: checking docker-compose is installed ...
[Step 2]: preparing environment ...
[Step 3]: preparing harbor configs ...
[Step 4]: starting Harbor ...
 Network harbor_harbor Creating 
 Network harbor_harbor Creating 
 Container harbor-log Creating 
 Container registry Creating 
 Container harbor-portal Creating 
 Container harbor-db Creating 
 Container redis Creating 
 Container registryctl Creating 
 Container trivy-adapter Creating 
 Container harbor-core Creating 
 Container nginx Creating 
 Container harbor-jobservice Creating 
 Container harbor-log Started 
 Container redis Started 
 Container trivy-adapter Started 
 Container registryctl Started 
 Container harbor-portal Started 
 Container harbor-db Started 
 Container registry Started 
 Container harbor-core Started 
 Container nginx Started 
 Container harbor-jobservice Started 
✔ ----Harbor has been installed and started successfully.----
(instalado en 54 s)
```

### contenedores

`$ docker ps --format '{{.Names}}  {{.Image}}'`

```
harbor-core  goharbor/harbor-core:v2.15.3
harbor-db  goharbor/harbor-db:v2.15.3
harbor-jobservice  goharbor/harbor-jobservice:v2.15.3
harbor-log  goharbor/harbor-log:v2.15.3
harbor-portal  goharbor/harbor-portal:v2.15.3
nginx  goharbor/nginx-photon:v2.15.3
redis  goharbor/valkey-photon:v2.15.3
registry  goharbor/registry-photon:v2.15.3
registryctl  goharbor/harbor-registryctl:v2.15.3
trivy-adapter  goharbor/trivy-adapter-photon:v2.15.3
```

### salud

`$ curl /api/v2.0/health`

```
["core","healthy"]
["database","healthy"]
["jobservice","unhealthy"]
["portal","healthy"]
["redis","healthy"]
["registry","healthy"]
["registryctl","healthy"]
["trivy","healthy"]
```

### memoria

`$ docker stats --no-stream`

```
harbor-core 40.46MiB / 15.36GiB
harbor-db 82.09MiB / 15.36GiB
harbor-jobservice 0B / 0B
harbor-log 5.008MiB / 15.36GiB
harbor-portal 17.29MiB / 15.36GiB
nginx 38.89MiB / 15.36GiB
redis 6.887MiB / 15.36GiB
registry 8MiB / 15.36GiB
registryctl 10.16MiB / 15.36GiB
trivy-adapter 3.504MiB / 15.36GiB
```

### versión

`$ curl /api/v2.0/systeminfo`

```
v2.15.3-fb476e10
```

## 2 · Un proyecto que escanea al subir

### crear proyecto

`$ POST /projects {name: demo, auto_scan: true}`

```
{"name":"demo","metadata":{"auto_scan":"true","public":"false"}}
```

## 3 · Subir una imagen vieja y una nueva

### push nginx:1.20

`$ docker push harbor.local/demo/nginx:1.20`

```
docker.io/library/nginx:1.20
 Info -> Not all multiplatform-content is present and only the available single-platform image was pushed
         sha256:38f8c1d9613f3f42e7969c3b1dd5c3277e635d4576713e6453c6193e66270a6d -> sha256:a76df3b4f1478766631c794de7ff466aca466f995fd5bb216bb9643a3dd2a6bb
(19 s)
```

### push alpine:3.22

`$ docker push harbor.local/demo/alpine:3.22`

```
docker.io/library/alpine:3.22
 Info -> Not all multiplatform-content is present and only the available single-platform image was pushed
         sha256:5291449c3df73caf6ed85e649dec1b9e818b39a5d8c871e97afc13e9cd5e8fa8 -> sha256:3e9b4b680bfc9fb5269227cffbd6d42be39fbf7c0b908123913864aa4447e764
(2 s)
```

### escaneo de nginx:1.20

`$ GET .../repositories/nginx/artifacts/1.20?with_scan_overview=true`

```
{"scanner": "Trivy", "severidad_max": "Critical", "total": 927, "por_severidad": {"Critical": 32, "High": 237, "Low": 257, "Medium": 386, "Unknown": 15}}
(resultado 102 s después de pedirlo)
```

### escaneo de alpine:3.22

`$ GET .../repositories/alpine/artifacts/3.22?with_scan_overview=true`

```
{"scanner": "Trivy", "severidad_max": "Medium", "total": 1, "por_severidad": {"Medium": 1}}
(resultado 0 s después de pedirlo)
```

### las 5 más graves de nginx:1.20

`$ GET .../vulnerabilities`

```
CVE-2021-22945  curl 7.74.0-1.3+deb11u1  Critical
CVE-2022-32207  curl 7.74.0-1.3+deb11u1  Critical
CVE-2022-32221  curl 7.74.0-1.3+deb11u1  Critical
CVE-2023-23914  curl 7.74.0-1.3+deb11u1  Critical
CVE-2023-38545  curl 7.74.0-1.3+deb11u1  Critical
```

## 4 · Impedir descargar imágenes vulnerables

### activar la política

`$ PUT /projects/demo {prevent_vul: true, severity: high}`

```
(200, sin cuerpo)
```

### pull de nginx:1.20

`$ docker pull harbor.local/demo/nginx:1.20`

```
Error response from daemon: unknown: failed to resolve reference "harbor.local/demo/nginx:1.20": unexpected status from HEAD request to http://harbor.local/v2/demo/nginx/manifests/1.20: 412 Precondition Failed
codigo=1
```

### pull de alpine:3.22

`$ docker pull harbor.local/demo/alpine:3.22`

```
harbor.local/demo/alpine:3.22
codigo=0
```

## 5 · Retención: quedarse con las 2 últimas etiquetas

### etiquetas de app

`$ GET .../repositories/app/artifacts`

```
v1
v2
v3
v4
v5
```

### crear la regla

`$ POST /retentions (retener las 2 últimas subidas de app)`

```
(201)
```

### ensayo (dry run)

`$ POST /retentions/{id}/executions {dry_run: true}`

```
{"id":10,"dry_run":true,"status":"Running"}
{"repository":"app","retained":2,"total":5,"status":"Success"}
```

### después del ensayo

`$ etiquetas de app`

```
v1
v2
v3
v4
v5
```

### de verdad

`$ POST /retentions/{id}/executions {dry_run: false}`

```
{"id":13,"dry_run":null,"status":"Success"}
```

### etiquetas que quedan

`$ etiquetas de app`

```
v4
v5
```

### ¿y el disco?

`$ du -sh /data/registry (antes de la recolección de basura)`

```
58.6M	/data/registry
```

### recolección de basura

`$ POST /system/gc/schedule (manual)`

```
{"job_status":"Success","job_parameters":"{\"delete_tag\":false,\"delete_untagged\":true,\"dry_run\":false,\"freed_space\":0,\"purged_blobs\":0,\"purged_manifests\":0,\"time_window\":2,\"workers\":0}"}
58.6M	/data/registry
```
