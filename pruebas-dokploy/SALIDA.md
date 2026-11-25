# SALIDA — Dokploy (vídeo 333)

Generado 2026-10-07 22:46 UTC con `python correr.py`. Instalador oficial dentro de docker:dind; app de ejemplo: Dokploy/examples, carpeta go-fiber.

## 1 · Instalar

### el instalador dentro de un contenedor

`$ curl -sSL https://dokploy.com/install.sh | sh`

```
Latest stable version detected: v0.30.8
Installing Dokploy version: v0.30.8
This script must be run on Linux
codigo=0
```

### instalar (sin /.dockerenv)

`$ curl -sSL https://dokploy.com/install.sh | sh`

```
Using advertise address: 172.17.0.3
Swarm initialized: current node (y50281oms02kk5xbg9rxh1x45) is now a manager.
Swarm initialized
Network created
Generated secure database credentials and auth secret (stored in Docker Secrets)
Congratulations, Dokploy is installed!
Please go to http://172.17.0.3:3000
(instalado en 90 s)
```

### servicios del swarm

`$ docker service ls`

```
dokploy  1/1  dokploy/dokploy:v0.30.8
dokploy-postgres  1/1  postgres:16
```

### contenedores

`$ docker ps`

```
dokploy-postgres.1.kj6mgyxo919e4p626l0wym4ab  postgres:16
dokploy-traefik  traefik:v3.6.25
dokploy.1.nxa5r6mpevftbdwasvx9aucnv  dokploy/dokploy:v0.30.8
```

### memoria (recién instalado)

`$ docker stats --no-stream`

```
dokploy-postgres.1.kj6mgyxo919e4p626l0wym4ab 49MiB / 15.36GiB
dokploy-traefik 19.55MiB / 15.36GiB
dokploy.1.nxa5r6mpevftbdwasvx9aucnv 759.1MiB / 15.36GiB
```

## 2 · Registro, proyecto, aplicación desde Git, despliegue y dominios (flujo.js)

### flujo.js

`$ node flujo.js`

```
### registro
tras registrarse: http://localhost:3300/dashboard/home

### crear proyecto
{"status":200,"json":{"project":{"projectId":"Yg_WIvJV4Vje-DH-VgBJg","name":"tienda","description":"banco de pruebas","createdAt":"2026-10-07T22:45:20.461Z","organizationId":"Qq-Fhl2EMQWbNptoKWRYR","env":""},"environment":{"environmentId":"WITPB1sRs41-YjusZltuO","name":"production","description":"Production environment","createdAt":"2026-10-07T22:45:20.463Z","env":"","projectId":"Yg_WIvJV4Vje-DH-VgBJg","isDefault":true}}}
entornos del proyecto: production

### crear aplicación
status 200 applicationId nVtsxqmSxhJnb7BSJiUbg appName app-program-neural-card-484ue2

### origen: Git
saveGitProvider 200
saveBuildType nixpacks 200

### desplegar
deploy 200
estado: done · 65 s desde el deploy
título: Update README.md · log: /etc/dokploy/logs/app-program-neural-card-484ue2/app-program-neural-card-484ue2-2026-10-07:22:45:20.log
applicationStatus: done · appName: app-program-neural-card-484ue2

### dominio sin HTTPS
domain.create 200 {"domainId":"YoKP-VIzKIoGKcrEBd-M8","host":"tienda.localhost","https":false,"port":3000,"customEntrypoint":null,"path":"/","serviceName":null,"domainType":"application","uniqueConfigKey":1,"createdAt":"2026-10-07T22:46:31.444Z","composeId":null,"customCertResolver":null,"applicationId":"nVtsxqmSxhJn

### dominio con HTTPS (Let's Encrypt)
domain.create 200 {"domainId":"yTLqeMC3ppWeVgj0hWyPW","host":"tienda.ejemplo.test","https":true,"port":3000,"customEntrypoint":null,"path":"/","serviceName":null,"domainType":"application","uniqueConfigKey":2,"createdAt":"2026-10-07T22:46:31.475Z","composeId":null,"customCertResolver":null,"applicationId":"nVtsxqmSxh
APPNAME=app-program-neural-card-484ue2
```

## 3 · Comprobar desde fuera

### servicio de la app

`$ docker service ls | grep app`

```
app-program-neural-card-484ue2  1/1  app-program-neural-card-484ue2:latest
```

### imagen construida

`$ docker images | grep app`

```
app-program-neural-card-484ue2:latest                                                             922f0da8534c        134MB         35.5MB   U
```

### HTTP con el dominio tienda.localhost

`$ curl -H 'Host: tienda.localhost' http://localhost:8089/`

```
HTTP/1.1 200 OK
Content-Length: 29
Content-Type: application/json
Date: Wed, 07 Oct 2026 22:46:39 GMT

{"message":"Hello, Railway!"}
```

### HTTPS con tienda.ejemplo.test (Let's Encrypt imposible en local)

`$ curl -k -v --resolve tienda.ejemplo.test:8444:127.0.0.1 https://tienda.ejemplo.test:8444/`

```
{"message":"Hello, Railway!"}* Added tienda.ejemplo.test:8444:127.0.0.1 to DNS cache
* using HTTP/1.x
> GET / HTTP/1.1
< HTTP/1.1 200 OK
```

### el certificado que intentó pedir

`$ docker logs dokploy-traefik | grep -i acme`

```
[90m2026-10-07T22:46:35Z[0m [31mERR[0m [1mUnable to obtain ACME certificate for domains[0m [36merror=[0m[31m[1m"unable to generate a certificate for the domains [tienda.ejemplo.test]: acme: error: 400 :: POST :: https://acme-v02.api.letsencrypt.org/acme/new-order :: urn:ietf:params:acme:er
```

### memoria (con la app)

`$ docker stats --no-stream`

```
app-program-neural-card-484ue2.1.ookjnhcr32ruwir2rtj5rjmte 4.426MiB / 15.36GiB
dokploy-postgres.1.kj6mgyxo919e4p626l0wym4ab 107.2MiB / 15.36GiB
dokploy-traefik 24MiB / 15.36GiB
dokploy.1.nxa5r6mpevftbdwasvx9aucnv 820.9MiB / 15.36GiB
```
