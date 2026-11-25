# SALIDA 874 — Agentes de Jenkins en Docker (cultura-devops)

> Corrida del 2026-11-18 10:51. jk-a-jenkins:1 = jenkins/jenkins:2.580.2-lts-jdk21 + plugins.txt; configuración en 874/jenkins.yaml (JCasC) y 874/jobs.groovy (Job DSL). Jenkins arrancó en 5363 ms.

```
### 0 · Versiones
$ jenkins --version · plugins · docker
2.580.2
configuration-as-code 2147.v8a_8d38668c72
docker-plugin 1337.v3ca_fd1b_b_25ef
job-dsl 3752.vb_199526b_20c3
workflow-aggregator 608.v67378e9d3db_1
docker (servidor) 29.6.2
imagen del agente efímero: jenkins/agent:3395.v6e5377b_0fb_3c-5-jdk21
imagen del agente fijo:    jenkins/inbound-agent:3395.v6e5377b_0fb_3c-5-jdk21
plugins fijados en plugins.txt: 76

### 1 · Jenkins habla con Docker por el socket
$ docker run ... --group-add 0 -v /var/run/docker.sock:/var/run/docker.sock jk-a-jenkins:1
jk-a-jenkins$ id ; ls -ln /var/run/docker.sock
uid=1000(jenkins) gid=1000(jenkins) groups=1000(jenkins),0(root)
srw-rw---- 1 0 0 0 Nov 18 14:12 /var/run/docker.sock
jk-a-jenkins$ curl --unix-socket /var/run/docker.sock http://docker/containers/json | contar
6 contenedores del host visibles desde Jenkins

# El riesgo: con el socket, Jenkins puede crear un contenedor que monte la raíz del host.
# (Aquí solo LEE: ls de /etc del host, en solo lectura, y el contenedor se borra.)
jk-a-jenkins$ POST /containers/create {Image: alpine, Cmd: [ls, /host/etc], Binds: [/:/host:ro]}
  X11
  adduser.conf
  alternatives
  apt
  bash.bashrc
  ...
  116

### 2 · Agente FIJO: tres builds seguidos en el mismo agente
--- estado-fijo #1 (INSTALAR=true)
Started from command line by admin
Running on fijo in /home/jenkins/agent/workspace/estado-fijo
agente: fijo · contenedor: 39bdfdd2ea5c
archivos que ya había en el workspace: 0  
instalé mi-linter en ~/bin
mi-linter 1.0: 0 problemas
Finished: SUCCESS
--- estado-fijo #2 (INSTALAR=false: el Jenkinsfile ya no instala mi-linter)
Started from command line by admin
Running on fijo in /home/jenkins/agent/workspace/estado-fijo
agente: fijo · contenedor: 39bdfdd2ea5c
archivos que ya había en el workspace: 1  salida-1.txt 
mi-linter 1.0: 0 problemas
Finished: SUCCESS
--- estado-fijo #3 (INSTALAR=false)
Started from command line by admin
Running on fijo in /home/jenkins/agent/workspace/estado-fijo
agente: fijo · contenedor: 39bdfdd2ea5c
archivos que ya había en el workspace: 2  salida-1.txt salida-2.txt 
mi-linter 1.0: 0 problemas
Finished: SUCCESS
jk-a-fijo$ ls ~/agent/workspace/estado-fijo ; ls ~/bin
salida-1.txt salida-2.txt salida-3.txt 
mi-linter

### 3 · Agente EFÍMERO: lo mismo, un contenedor nuevo por build
--- estado-efimero #1 (INSTALAR=true)
Started from command line by admin
Running on efimero-000023nda28zq on docker in /home/jenkins/agent/workspace/estado-efimero
agente: efimero-000023nda28zq · contenedor: 4ee69150a86e
archivos que ya había en el workspace: 0  
instalé mi-linter en ~/bin
mi-linter 1.0: 0 problemas
Finished: SUCCESS
--- estado-efimero #2 (INSTALAR=false)
Started from command line by admin
Still waiting to schedule task
‘efimero-000023nda28zq on docker’ is offline
Running on efimero-000024rmecb0e on docker in /home/jenkins/agent/workspace/estado-efimero
agente: efimero-000024rmecb0e · contenedor: 7ea208205366
archivos que ya había en el workspace: 0  
/home/jenkins/agent/workspace/estado-efimero@tmp/durable-4f05d743/script.sh.copy: 11: /home/jenkins/bin/mi-linter: not found
ERROR: script returned exit code 127
Finished: FAILURE

$ docker ps -a --filter id=4ee69150a86e ; docker ps -a --filter id=7ea208205366
(vacío: los dos contenedores ya no existen; el del #2 desapareció 10244 ms después de terminar el build)
$ jenkins list nodes
  Built-In Node online
  efimero-000023nda28zq offline
  efimero-000024rmecb0e offline
  fijo online

### 4 · Cuánto cuesta el contenedor nuevo: 10 builds vacíos por lado (pipeline de un solo sh)
# espera = desde que empieza el build hasta que corre el primer sh en el agente (API: timestamp; el sh imprime date +%s%3N)
--- vacio-fijo: build resultado espera_ms duración_ms
  1 SUCCESS 492 813
  2 SUCCESS 334 634
  3 SUCCESS 239 551
  4 SUCCESS 229 531
  5 SUCCESS 215 518
  6 SUCCESS 204 517
  7 SUCCESS 163 459
  8 SUCCESS 138 435
  9 SUCCESS 133 433
  10 SUCCESS 146 445
  mediana espera: 209 ms · mediana duración: 517 ms
--- vacio-efimero: build resultado espera_ms duración_ms
  1 SUCCESS 2052 2383
  2 SUCCESS 2237 2576
  3 SUCCESS 4537 4874
  4 SUCCESS 5419 5743
  5 SUCCESS 5494 5814
  6 SUCCESS 5394 5717
  7 SUCCESS 5491 5825
  8 SUCCESS 5453 5786
  9 SUCCESS 5524 5859
  10 SUCCESS 5474 5814
  mediana espera: 5436 ms · mediana duración: 5764 ms

### 5 · ¿Quedó algo?
$ docker ps -a --filter ancestor=jenkins/agent:3395.v6e5377b_0fb_3c-5-jdk21
  contenedores del agente efímero vivos: 1
```
