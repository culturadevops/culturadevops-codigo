# SALIDA · docker-error-permission-denied-daemon (vídeo 695, cultura-devops)

Ejecutado el 2026-10-29 con `bash correr.sh` desde Git Bash en Windows 11 + Docker Desktop. Para tener un Linux con usuarios normales se usa un docker-in-docker (`docker:29.6.2-dind`, `--privileged --rm`) y un rootless (`docker:29.6.2-dind-rootless`). Salida literal.

```
### Versión (dentro del docker-in-docker)
$ docker version --format ...
cliente 29.6.2 · servidor 29.6.2

=================== A · El error: usuario normal, sin grupo docker ===================
$ id
uid=1000(ana) gid=1000(ana) groups=1000(ana)
$ docker ps; echo exit=$?
permission denied while trying to connect to the docker API at unix:///var/run/docker.sock
exit=1
--- ¿por qué? el socket es de root:docker, y ana no está en docker
$ ls -l /var/run/docker.sock
srw-rw----    1 root     docker           0 Oct 29 12:45 /var/run/docker.sock
$ getent group docker
docker:x:2375:
$ ls -l /var/run/docker.sock | cut -d" " -f1,3,4
srw-rw----  

=================== B · El atajo que NO es el arreglo: sudo ===================
$ sudo docker ps; echo exit=$?
CONTAINER ID   IMAGE     COMMAND   CREATED   STATUS    PORTS     NAMES
exit=0
(funciona, pero teclear sudo en cada comando no es la solución; y da TODO el poder de root)

=================== C · El arreglo bueno: meter al usuario en el grupo docker ===================
--- en la MISMA sesión en la que te añaden al grupo, el cambio todavía no cuenta
$ id | tr "," "\n" | grep -c docker
sudo addgroup ana docker >/dev/null && echo "(root: ana añadida al grupo docker)"
echo "en esta misma sesión, id sigue igual:"; id | tr "," "\n" | grep docker || echo "(sin docker todavia)"
echo "y por eso docker sigue fallando:"; docker ps 2>&1; echo exit=$?
0
(root: ana añadida al grupo docker)
en esta misma sesión, id sigue igual:
(sin docker todavia)
y por eso docker sigue fallando:
permission denied while trying to connect to the docker API at unix:///var/run/docker.sock
exit=1
--- el grupo entra al abrir una sesión NUEVA (cerrar sesión y volver a entrar; aquí, su - ana)
$ su - ana -c 'id | tr "," "\n" | grep docker; docker ps >/dev/null 2>&1 && echo "docker ps: OK"'
2375(docker)
docker ps: OK
(sesión nueva = el grupo ya cuenta y el socket se deja usar; newgrp docker hace lo mismo sin salir)

=================== D · El grupo docker ES root (demostración) ===================
--- ana, sin sudo, SOLO por estar en el grupo docker, lee un archivo 600 de root montando la raíz
$ echo "secreto-del-host" > /root/solo-root.txt && chmod 600 /root/solo-root.txt
$ echo "ana directamente:"; cat /root/solo-root.txt 2>&1; echo exit=$?
ana directamente:
cat: can't open '/root/solo-root.txt': Permission denied
exit=1
$ echo "ana con el socket de docker (su - ana):"; su - ana -c 'docker run --rm -v /:/host alpine:3.24.3 cat /host/root/solo-root.txt'
ana con el socket de docker (su - ana):
secreto-del-host
(ana no es root ni usó sudo: montó la raíz del host en un contenedor y la leyó. Por eso)
(la documentación de Docker avisa: el grupo docker concede privilegios equivalentes a root.)

=================== E · La alternativa sin ese riesgo: Docker rootless ===================
--- un daemon que corre como el usuario 'rootless', no como root
$ id
uid=1000(rootless) gid=1000(rootless) groups=1000(rootless)
$ docker info --format {{.SecurityOptions}}
[name=seccomp,profile=builtin name=rootless name=cgroupns]
--- 'root' dentro de un contenedor rootless NO es root del host: no puede tocar /etc/shadow montado
uid=0(root) gid=0(root) groups=0(root),0(root),1(bin),2(daemon),3(sys),4(adm),6(disk),10(wheel),11(floppy),20(dialout),26(tape),27(video)
cat: can't open '/host/etc/shadow': Permission denied
exit=1
(el root del contenedor es el usuario 'rootless' mapeado: no tiene permiso sobre los archivos del host)

=================== F · En Windows/Mac: Docker Desktop no da este error ===================
En Windows y Mac el cliente habla con el daemon por un named pipe / socket que gestiona
Docker Desktop para tu usuario; no hay grupo docker. El permission denied del socket Unix
es cosa de Linux (o de WSL con el engine nativo). Lo que sí verás en Windows si Docker
Desktop no está arrancado, con el mismo tono de 'no puedo conectar con el daemon':
$ docker ps   (Docker Desktop apagado)
error during connect: ... open //./pipe/dockerDesktopLinuxEngine:
El sistema no puede encontrar el archivo especificado.
```
