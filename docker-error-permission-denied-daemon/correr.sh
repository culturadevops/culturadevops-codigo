#!/bin/bash
# Demos del vídeo 695 de cultura-devops:
#   «permission denied while trying to connect to the Docker daemon socket»
# El socket de Docker es de root y del grupo docker. Un usuario normal sin ese grupo no puede.
# Y estar en el grupo docker equivale a ser root: se demuestra.
# Todo dentro de un docker-in-docker (--privileged, --rm, nombre único) para tener un Linux
# con usuarios de verdad sin tocar la máquina.
#   bash canales/cultura-devops/recursos/docker-error-permission-denied-daemon/correr.sh
set -u
export MSYS_NO_PATHCONV=1
cd "$(dirname "$0")"
ALP=alpine:3.24.3
DIND=docker:29.6.2-dind
RL=docker:29.6.2-dind-rootless
DH=tcp://127.0.0.1:23751
RLH=tcp://127.0.0.1:23752

limpiar() {
  docker rm -f v695-dind v695-rl >/dev/null 2>&1
}
trap limpiar EXIT

# E: ejecuta algo DENTRO del dind como el usuario indicado y muestra el comando.
E() { local u=$1; shift; echo "\$ $*"; docker exec -u "$u" v695-dind sh -c "$*" 2>&1; }

demos() {
echo "### Versión (dentro del docker-in-docker)"
docker exec v695-dind sh -c 'echo "$ docker version --format ..."; docker version --format "cliente {{.Client.Version}} · servidor {{.Server.Version}}"'
echo

echo "=================== A · El error: usuario normal, sin grupo docker ==================="
docker exec v695-dind sh -c 'adduser -D ana 2>/dev/null; adduser -D beto 2>/dev/null'
E ana 'id'
E ana 'docker ps; echo exit=$?'
echo "--- ¿por qué? el socket es de root:docker, y ana no está en docker"
E ana 'ls -l /var/run/docker.sock'
E ana 'getent group docker'
E ana 'ls -l /var/run/docker.sock | cut -d" " -f1,3,4'
echo

echo "=================== B · El atajo que NO es el arreglo: sudo ==================="
docker exec v695-dind sh -c 'apk add -q sudo shadow 2>/dev/null; echo "ana ALL=(ALL) NOPASSWD:ALL" > /etc/sudoers.d/ana'
docker exec v695-dind sh -c 'deluser ana docker 2>/dev/null; true'
E ana 'sudo docker ps; echo exit=$?'
echo "(funciona, pero teclear sudo en cada comando no es la solución; y da TODO el poder de root)"
echo

echo "=================== C · El arreglo bueno: meter al usuario en el grupo docker ==================="
echo "--- en la MISMA sesión en la que te añaden al grupo, el cambio todavía no cuenta"
E ana 'id | tr "," "\n" | grep -c docker
sudo addgroup ana docker >/dev/null && echo "(root: ana añadida al grupo docker)"
echo "en esta misma sesión, id sigue igual:"; id | tr "," "\n" | grep docker || echo "(sin docker todavia)"
echo "y por eso docker sigue fallando:"; docker ps 2>&1; echo exit=$?'
echo "--- el grupo entra al abrir una sesión NUEVA (cerrar sesión y volver a entrar; aquí, su - ana)"
E root 'su - ana -c '\''id | tr "," "\n" | grep docker; docker ps >/dev/null 2>&1 && echo "docker ps: OK"'\'''
echo "(sesión nueva = el grupo ya cuenta y el socket se deja usar; newgrp docker hace lo mismo sin salir)"
echo

echo "=================== D · El grupo docker ES root (demostración) ==================="
echo "--- ana, sin sudo, SOLO por estar en el grupo docker, lee un archivo 600 de root montando la raíz"
E root 'echo "secreto-del-host" > /root/solo-root.txt && chmod 600 /root/solo-root.txt'
E ana 'echo "ana directamente:"; cat /root/solo-root.txt 2>&1; echo exit=$?'
E root 'echo "ana con el socket de docker (su - ana):"; su - ana -c '\''docker run --rm -v /:/host alpine:3.24.3 cat /host/root/solo-root.txt'\'''
echo "(ana no es root ni usó sudo: montó la raíz del host en un contenedor y la leyó. Por eso)"
echo "(la documentación de Docker avisa: el grupo docker concede privilegios equivalentes a root.)"
echo

echo "=================== E · La alternativa sin ese riesgo: Docker rootless ==================="
echo "--- un daemon que corre como el usuario 'rootless', no como root"
docker exec -e DOCKER_HOST=unix:///run/user/1000/docker.sock v695-rl sh -c 'echo "$ id"; id; echo "$ docker info --format {{.SecurityOptions}}"; docker info --format "{{.SecurityOptions}}"'
echo "--- 'root' dentro de un contenedor rootless NO es root del host: no puede tocar /etc/shadow montado"
docker exec -e DOCKER_HOST=unix:///run/user/1000/docker.sock v695-rl sh -c 'docker run --rm -v /:/host alpine:3.24.3 sh -c "id; cat /host/etc/shadow 2>&1; echo exit=\$?"'
echo "(el root del contenedor es el usuario 'rootless' mapeado: no tiene permiso sobre los archivos del host)"
echo

echo "=================== F · En Windows/Mac: Docker Desktop no da este error ==================="
echo "En Windows y Mac el cliente habla con el daemon por un named pipe / socket que gestiona"
echo "Docker Desktop para tu usuario; no hay grupo docker. El permission denied del socket Unix"
echo "es cosa de Linux (o de WSL con el engine nativo). Lo que sí verás en Windows si Docker"
echo "Desktop no está arrancado, con el mismo tono de 'no puedo conectar con el daemon':"
cat <<'EOF'
$ docker ps   (Docker Desktop apagado)
error during connect: ... open //./pipe/dockerDesktopLinuxEngine:
El sistema no puede encontrar el archivo especificado.
EOF
}

# --- preparar los dos daemons ---
docker rm -f v695-dind v695-rl >/dev/null 2>&1
docker run -d --privileged --rm --name v695-dind -e DOCKER_TLS_CERTDIR= -p 127.0.0.1:23751:2375 $DIND >/dev/null
docker run -d --privileged --rm --name v695-rl $RL >/dev/null
for i in $(seq 1 40); do docker exec v695-dind docker info >/dev/null 2>&1 && break; sleep 1; done
for i in $(seq 1 40); do docker exec -e DOCKER_HOST=unix:///run/user/1000/docker.sock v695-rl docker info >/dev/null 2>&1 && break; sleep 1; done
docker save $ALP | docker exec -i v695-dind docker load -q >/dev/null
docker save $ALP | docker exec -i -e DOCKER_HOST=unix:///run/user/1000/docker.sock v695-rl docker load -q >/dev/null

{
  echo "# SALIDA · docker-error-permission-denied-daemon (vídeo 695, cultura-devops)"
  echo
  echo "Ejecutado el $(date +%F) con \`bash correr.sh\` desde Git Bash en Windows 11 + Docker Desktop. Para tener un Linux con usuarios normales se usa un docker-in-docker (\`$DIND\`, \`--privileged --rm\`) y un rootless (\`$RL\`). Salida literal."
  echo
  echo '```'
  demos
  echo '```'
} > SALIDA.md
echo "SALIDA.md escrito"
