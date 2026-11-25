# SALIDA · docker-error-port-already-allocated (vídeo 696, cultura-devops)

Ejecutado el 2026-10-29 con `bash correr.sh` desde Git Bash en Windows 11 + Docker Desktop. La parte Linux corre en un docker-in-docker (`docker:29.6.2-dind`, `--privileged --rm`) para tener `ss` y `lsof` limpios; la parte Windows corre directa en el host. Salida literal.

```
### Versión (dentro del docker-in-docker Linux)
$ docker version --format ...
cliente 29.6.2 · servidor 29.6.2

=================== A · El error: dos contenedores quieren el mismo puerto ===================
$ docker run -d --name web1 -p 8080:80 nginx:1.29-alpine >/dev/null && echo "web1 arriba en 8080"
web1 arriba en 8080
$ docker run -d --name web2 -p 8080:80 nginx:1.29-alpine; echo exit=$?
21bc2e654139296ab255cc1bd6954147f90097345a250d91d2357a72ebfe80a1
docker: Error response from daemon: failed to set up container networking: driver failed programming external connectivity on endpoint web2 (d000a286b957a5e78445827d0776dcc541aff03066d2e24e64252ae694dc61ad): Bind for 0.0.0.0:8080 failed: port is already allocated

Run 'docker run --help' for more information
exit=125

=================== B · Encontrar al culpable ===================
--- quién publica ese puerto, según Docker:
$ docker ps --filter publish=8080 --format "table {{.Names}}\t{{.Ports}}"
NAMES     PORTS
web1      0.0.0.0:8080->80/tcp, [::]:8080->80/tcp
--- quién escucha en el host, con ss:
$ ss -ltnp "sport = :8080"
State  Recv-Q Send-Q Local Address:Port Peer Address:PortProcess
LISTEN 0      4096         0.0.0.0:8080      0.0.0.0:*    users:(("docker-proxy",pid=968,fd=8))
LISTEN 0      4096            [::]:8080         [::]:*    users:(("docker-proxy",pid=974,fd=8))
--- o con lsof:
$ lsof -nP -iTCP:8080 -sTCP:LISTEN
COMMAND   PID USER FD   TYPE DEVICE SIZE/OFF NODE NAME
docker-pr 968 root 8u  IPv4 437968      0t0  TCP *:8080 (LISTEN)
docker-pr 974 root 8u  IPv6 437969      0t0  TCP *:8080 (LISTEN)

=================== C · Los dos arreglos ===================
--- arreglo 1: publicar en OTRO puerto del host (izquierda = host, derecha = contenedor)
$ docker run -d --name web3 -p 8081:80 nginx:1.29-alpine >/dev/null && docker port web3
80/tcp -> 0.0.0.0:8081
80/tcp -> [::]:8081
--- arreglo 2: si web1 sobraba, pararlo y liberar el 8080
$ docker rm -f web1 >/dev/null && docker run -d --name web4 -p 8080:80 nginx:1.29-alpine >/dev/null && docker port web4
80/tcp -> 0.0.0.0:8080
80/tcp -> [::]:8080
$ docker rm -f web2 web3 web4 >/dev/null 2>&1; echo limpiado
limpiado

=================== D · Causa 2: un proceso del host (no un contenedor) ocupa el puerto ===================
--- un servidor cualquiera escuchando en 8082 (aquí, nc):
$ (nc -lk -p 8082 -e true &) ; sleep 1; echo "nc escuchando en 8082"
nc escuchando en 8082
$ docker run -d --name web5 -p 8082:80 nginx:1.29-alpine; echo exit=$?
a8a4f6d806adb71b4eda3eb65fe695b86d9c04884cbd83f007edf1a9e5cf47ae
docker: Error response from daemon: failed to set up container networking: driver failed programming external connectivity on endpoint web5 (45bbe7ae8b912df9a9dc9165e8b5ef08435a5cd952da2f901ac2686328439b5c): failed to bind host port 0.0.0.0:8082/tcp: address already in use

Run 'docker run --help' for more information
exit=125
(mensaje distinto: address already in use. docker ps --filter publish no muestra nada...)
$ docker ps --filter publish=8082 --format "{{.Names}}"; echo "(vacío: no es un contenedor)"
(vacío: no es un contenedor)
--- ...pero ss/lsof sí dan con el proceso del host:
$ ss -ltnp "sport = :8082"
State  Recv-Q Send-Q Local Address:Port Peer Address:PortProcess
LISTEN 0      1                  *:8082            *:*    users:(("nc",pid=1604,fd=3))
$ lsof -nP -iTCP:8082 -sTCP:LISTEN
COMMAND  PID USER FD   TYPE DEVICE SIZE/OFF NODE NAME
nc      1604 root 3u  IPv6 449392      0t0  TCP *:8082 (LISTEN)
$ pkill nc 2>/dev/null; docker rm -f web5 >/dev/null 2>&1; echo limpiado
limpiado

=================== E · Causa 3: un compose viejo que quedó levantado ===================
$ mkdir -p /tmp/tienda && printf "services:\n  cache:\n    image: nginx:1.29-alpine\n    ports:\n      - 8083:80\n" > /tmp/tienda/compose.yaml
$ cd /tmp/tienda && docker compose up -d 2>&1 | tail -1
 Container tienda-cache-1 Started 
(te olvidas de que sigue arriba y mañana otro proyecto pide el 8083)
$ docker run -d --name web6 -p 8083:80 nginx:1.29-alpine; echo exit=$?
4d375776bae53eaebe79eb8a165a96490775dd6377cfcb83ca195823f12c7cdb
docker: Error response from daemon: failed to set up container networking: driver failed programming external connectivity on endpoint web6 (14fbbe0f4b6d210794d25de7f32a8dd1eb2491767635f77435ad45fcbac7a851): Bind for :::8083 failed: port is already allocated

Run 'docker run --help' for more information
exit=125
--- el culpable lleva etiquetas de compose: te dicen qué proyecto y en qué carpeta pararlo
$ docker ps --filter publish=8083 --format "{{.Names}}"
tienda-cache-1
$ docker inspect -f "proyecto={{index .Config.Labels \"com.docker.compose.project\"}} carpeta={{index .Config.Labels \"com.docker.compose.project.working_dir\"}}" $(docker ps -q --filter publish=8083)
proyecto=tienda carpeta=/tmp/tienda
$ cd /tmp/tienda && docker compose down -v 2>&1 | tail -1
 Network tienda_default Removed 
$ docker rm -f web6 >/dev/null 2>&1; echo limpiado
limpiado

=================== F · En Windows: dos contenedores y netstat -ano para el culpable ===================
$ docker run -d --name v696-a -p 29087:80 nginx:1.29-alpine
v696-a arriba en 29087
$ docker run -d --name v696-b -p 29087:80 nginx:1.29-alpine
27d8b62b4e92b53ac3b600517406069d415bfa443af3e7480305e9a03e82f7d1
docker: Error response from daemon: failed to set up container networking: driver failed programming external connectivity on endpoint v696-b (48ed42efc65a8e0aebce915fe02dbcec042eafa39c2ce483dcb82e0646fd5ad6): Bind for 0.0.0.0:29087 failed: port is already allocated

Run 'docker run --help' for more information
exit=125

--- quién tiene el puerto, con netstat -ano (la última columna es el PID):
$ netstat -ano | findstr :29087
  TCP    0.0.0.0:29087          0.0.0.0:0              LISTENING       18268
  TCP    [::]:29087             [::]:0                 LISTENING       18268
  TCP    [::1]:29087            [::]:0                 LISTENING       39420
--- en Windows ese PID es el backend de Docker Desktop, no el contenedor:
$ tasklist /FI "PID eq 39420"
wslrelay.exe                 39420 Console                   11    10,632 KB
--- el culpable real (el contenedor) lo da docker ps --filter publish:
$ docker ps --filter publish=29087 --format "{{.Names}}"
v696-a

--- OJO (medido): en Windows, un proceso del host en 0.0.0.0 NO choca con el contenedor
$ docker run -d --rm --name v696-c -p 29088:80 nginx:1.29-alpine
exit=0  (arrancó: Docker Desktop reenvía por la red de WSL, convive con el proceso del host)
  TCP    0.0.0.0:29088          0.0.0.0:0              LISTENING       18268
  TCP    [::]:29088             [::]:0                 LISTENING       18268

--- donde SÍ choca un proceso del host en Windows: publicar en una interfaz concreta (127.0.0.1)
(un proceso escucha en 127.0.0.1:29089)
$ docker run -d --rm --name v696-d -p 127.0.0.1:29089:80 nginx:1.29-alpine
97b5db704354955b9804c9b7f99b0bf32045be6c2958819054be14c3b6f25012
docker: Error response from daemon: ports are not available: exposing port TCP 127.0.0.1:29089 -> 127.0.0.1:0: listen tcp4 127.0.0.1:29089: bind: Solo se permite un uso de cada dirección de socket (protocolo/dirección de red/puerto)

Run 'docker run --help' for more information
exit=125
--- netstat -ano y tasklist dan con el proceso del host:
  TCP    127.0.0.1:29089        0.0.0.0:0              LISTENING       5376
powershell.exe                5376 Console                   11   117,172 KB
```
