#!/bin/bash
# Demo de «Cómo instalar Docker en Ubuntu» (cultura-devops, 2026-10-23). Corre desde Git Bash.
# Un Ubuntu 24.04 limpio dentro de un contenedor privilegiado hace de «servidor recién instalado»: se siguen los pasos
# de docs.docker.com/engine/install/ubuntu/ (repositorio apt) y de linux-postinstall (grupo docker). Nada toca tu máquina.
set -u
N=demo-instalar-docker-ubuntu
docker rm -fv $N >/dev/null 2>&1
docker run -d --privileged --name $N --label demo=cd-instalar-docker-ubuntu -v /var/lib/docker ubuntu:24.04 sleep infinity >/dev/null
U() { echo "\$ $*"; docker exec $N bash -c "$*" 2>&1; }

echo "### 0 · El Ubuntu de partida"
U ". /etc/os-release && echo \$PRETTY_NAME"
U "docker --version"

echo
echo "### 1 · Prerrequisitos y la llave GPG oficial"
docker exec $N bash -c "apt-get update -qq >/dev/null && DEBIAN_FRONTEND=noninteractive apt-get install -y -qq ca-certificates curl >/dev/null" 2>&1 | tail -2
echo "\$ apt update && apt install ca-certificates curl   (hecho)"
U "install -m 0755 -d /etc/apt/keyrings"
U "curl -fsSL https://download.docker.com/linux/ubuntu/gpg -o /etc/apt/keyrings/docker.asc"
U "chmod a+r /etc/apt/keyrings/docker.asc && ls -l /etc/apt/keyrings/docker.asc"

echo
echo "### 2 · El repositorio apt de Docker"
docker exec $N bash -c 'tee /etc/apt/sources.list.d/docker.sources >/dev/null <<EOF
Types: deb
URIs: https://download.docker.com/linux/ubuntu
Suites: $(. /etc/os-release && echo "${UBUNTU_CODENAME:-$VERSION_CODENAME}")
Components: stable
Architectures: $(dpkg --print-architecture)
Signed-By: /etc/apt/keyrings/docker.asc
EOF'
U "cat /etc/apt/sources.list.d/docker.sources"
U "apt-get update 2>&1 | grep -i docker"

echo
echo "### 3 · Instalar los paquetes"
echo "\$ apt install docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin"
docker exec $N bash -c "DEBIAN_FRONTEND=noninteractive apt-get install -y -qq docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin >/dev/null 2>&1; echo exit=\$?"
U "docker --version"
U "docker compose version"

echo
echo "### 4 · Arrancar el servicio y probar"
echo "# (en un Ubuntu normal lo arranca systemd solo: systemctl status docker. Aquí, sin systemd, lo lanzo a mano)"
docker exec -d $N bash -c "dockerd >/var/log/dockerd.log 2>&1"
sleep 6
U "docker run --rm hello-world | head -3"

echo
echo "### 5 · Un usuario normal: permission denied"
docker exec $N bash -c "useradd -m -s /bin/bash ana"
echo "ana\$ docker ps"
docker exec -u ana $N docker ps 2>&1
U "ls -l /var/run/docker.sock"

echo
echo "### 6 · El paso post-instalación: el grupo docker"
# una sesión de ana abierta ANTES de añadirla al grupo (como una terminal que ya tenías abierta)
docker exec -d $N su ana -c "sleep 6; (echo 'grupos:' \$(id -nG); docker ps) > /tmp/sesion_vieja.txt 2>&1"
U "groupadd docker"
U "getent group docker"
U "usermod -aG docker ana"
U "getent group docker"
sleep 8
echo "ana\$ docker ps   (la terminal que ya tenía abierta)"
docker exec $N cat /tmp/sesion_vieja.txt
echo "ana\$ newgrp docker   # o cerrar sesión y volver a entrar"
echo "ana\$ docker run --rm hello-world | head -3"
docker exec $N su - ana -c "echo grupos: \$(id -nG); docker run --rm hello-world | head -3" 2>&1

echo "### 7 · Versiones finales"
U "docker version --format 'cliente {{.Client.Version}} · servidor {{.Server.Version}}'"

echo
echo "### 8 · Las versiones disponibles (para fijar una)"
U "apt list --all-versions docker-ce 2>/dev/null | head -4"

echo
echo "### 9 · Dónde guarda Docker sus datos"
U "docker info --format '{{.DockerRootDir}}'"
U "docker images --format '{{.Repository}}:{{.Tag}} {{.Size}}'"
U "ls /var/lib/docker"

echo
echo "### 10 · Desinstalar: los datos se quedan"
docker exec $N bash -c "pkill dockerd; sleep 3"
echo "\$ apt purge docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin docker-ce-rootless-extras"
docker exec $N bash -c "DEBIAN_FRONTEND=noninteractive apt-get purge -y -qq docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin docker-ce-rootless-extras >/dev/null 2>&1; echo exit=\$?"
U "docker --version"
U "ls /var/lib/docker | head -5"
U "du -sh /var/lib/docker"
docker rm -fv $N >/dev/null && echo "(contenedor de la demo borrado)"
