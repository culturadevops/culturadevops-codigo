# SALIDA · docker-error-no-such-container (vídeo 694, cultura-devops)

Ejecutado el 2026-10-29 con `bash correr.sh` desde Git Bash en Windows 11 + Docker Desktop. Imágenes: nginx:1.29-alpine, alpine:3.24.3, docker:29.6.2-dind (el segundo daemon de la causa 5). Todo lo de abajo es la salida literal.

```
### Versión
$ docker version --format 'cliente {{.Client.Version}} · servidor {{.Server.Version}}'
cliente 29.6.2 · servidor 29.6.2

=================== A · Causa 1: el nombre o el ID no es ese ===================
$ docker logs v694-wbe
Error response from daemon: No such container: v694-wbe
$ docker exec v694-wbe nginx -v
Error response from daemon: No such container: v694-wbe
$ docker stop v694-wbe
Error response from daemon: No such container: v694-wbe
--- el arreglo: pregúntale a Docker cómo se llama de verdad (el filtro name busca por trozo)
$ docker ps -a --filter name=web --format 'table {{.Names}}\t{{.Status}}'
NAMES      STATUS
v694-web   Up Less than a second
$ docker exec v694-web nginx -v
nginx version: nginx/1.29.8
--- con el ID basta un prefijo único; un ID que no existe da el mismo error
$ docker inspect -f '{{.Name}}' dde9
/v694-web
$ docker logs 0000aaaa
Error response from daemon: No such container: 0000aaaa
--- inspect lo dice distinto
$ docker inspect v694-wbe
[]
error: no such object: v694-wbe

=================== B · Detenido NO es borrado (otro error distinto) ===================
$ docker stop v694-web
v694-web
$ docker ps --filter name=v694-web --format '{{.Names}} {{.Status}}'
(docker ps no lo muestra: solo enseña los que están corriendo)
$ docker ps -a --filter name=v694-web --format '{{.Names}} {{.Status}}'
v694-web Exited (0) Less than a second ago
$ docker exec v694-web nginx -v
Error response from daemon: container dde9976f36af17e5f7ba0eac1c5fe3383495e57ce92f1c2fc5cebaf0f09f332e is not running
$ docker start v694-web
v694-web
$ docker exec v694-web nginx -v
nginx version: nginx/1.29.8
$ docker rm -f v694-web
v694-web

=================== C · Causa 2: --rm lo borró al terminar ===================
$ docker run --rm --name v694-tarea alpine:3.24.3 sh -c 'echo migracion hecha; exit 3'; echo exit=$?
migracion hecha
exit=3
$ docker logs v694-tarea
Error response from daemon: No such container: v694-tarea
$ docker ps -a --filter name=v694-tarea --format '{{.Names}} {{.Status}}'
(nada: con --rm, al salir el contenedor se borra con sus logs y su código de salida)
--- el arreglo: si vas a querer los logs, sin --rm
$ docker run --name v694-guardada alpine:3.24.3 sh -c 'echo migracion hecha; exit 3'; echo exit=$?
migracion hecha
exit=3
$ docker logs v694-guardada
migracion hecha
$ docker inspect -f 'ExitCode={{.State.ExitCode}}' v694-guardada
ExitCode=3
$ docker rm v694-guardada
v694-guardada
--- borrarlo dos veces: la segunda ya no existe
$ docker rm v694-guardada
Error response from daemon: No such container: v694-guardada
$ docker rm -f v694-guardada; echo exit=$?
Error response from daemon: No such container: v694-guardada
exit=0
(con -f el mensaje sale igual, pero el código es 0: útil en scripts de limpieza)

=================== D · Causa 3: Docker Compose le pone prefijo al nombre ===================
$ cat compose.yaml
services:
  web:
    image: nginx:1.29-alpine
$ docker compose up -d 2>&1 | tail -1
 Container v694-tienda-web-1 Started 
$ docker exec web nginx -v
Error response from daemon: No such container: web
$ docker ps --filter label=com.docker.compose.project=v694-tienda --format '{{.Names}}'
v694-tienda-web-1
(nombre = proyecto-servicio-número; el proyecto, por defecto, es el nombre de la carpeta)
--- arreglo 1: hablarle a Compose por el nombre del servicio
$ docker compose exec web nginx -v
nginx version: nginx/1.29.8
--- arreglo 2: el nombre completo
$ docker exec v694-tienda-web-1 nginx -v
nginx version: nginx/1.29.8
--- pero docker compose exec fuera de la carpeta no encuentra el proyecto
$ docker compose exec web nginx -v
no configuration file provided: not found
$ docker compose -p v694-tienda exec web nginx -v
nginx version: nginx/1.29.8

=================== E · Causa 4: el ID cambió al recrear ===================
(guardé el ID: d102088e6a33)
$ docker compose up -d --force-recreate 2>&1 | tail -1
 Container v694-tienda-web-1 Started 
$ docker logs d102088e6a33
Error response from daemon: No such container: d102088e6a33
$ docker compose ps -q web | cut -c1-12
2e09314170da
(recrear = borrar y crear otro: ID nuevo. Guarda el nombre, no el ID)
$ docker compose down -v 2>&1 | tail -1
 Network v694-tienda_default Removed 

=================== F · Causa 5: estás hablando con otro daemon ===================
(un segundo daemon de Docker, en tcp://127.0.0.1:23750: otra máquina, otro contexto)
$ docker -H tcp://127.0.0.1:23750 run -d --name v694-api alpine:3.24.3 sleep 600 | cut -c1-12
d0e372bb4980
$ docker exec v694-api echo hola
Error response from daemon: No such container: v694-api
$ docker context show
desktop-linux
$ docker context create v694-dind --docker host=tcp://127.0.0.1:23750
v694-dind
Successfully created context "v694-dind"
$ docker context ls --format '{{.Name}}\t{{.DockerEndpoint}}' | grep -E 'default|desktop|v694'
default	npipe:////./pipe/docker_engine
desktop-linux	npipe:////./pipe/dockerDesktopLinuxEngine
v694-dind	tcp://127.0.0.1:23750
$ DOCKER_CONTEXT=v694-dind docker exec v694-api echo hola
hola
$ docker --context v694-dind ps --format '{{.Names}} {{.Status}}'
v694-api Up 1 second
$ DOCKER_HOST=tcp://127.0.0.1:23750 docker exec v694-api echo hola
hola
(docker context use v694-dind lo deja fijo; aquí uso la variable para no cambiar el contexto de la máquina)
```
