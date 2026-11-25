#!/bin/bash
# Demo de «SSH: connection refused en el puerto 22» (cultura-devops, 2026-10-20). Corre desde Git Bash.
# Dos contenedores en una red propia: «cliente» y «servidor» (Debian + OpenSSH). Nada toca tu máquina.
set -u
C() { docker exec cliente "$@" 2>&1; }          # en el cliente, como ana
S() { docker exec servidor "$@" 2>&1; }         # en el servidor, como root
SSH="ssh -o BatchMode=yes -o ConnectTimeout=5 -o StrictHostKeyChecking=accept-new"
sshd_con() { S pkill -x sshd >/dev/null; sleep 1; S /usr/sbin/sshd "$@"; sleep 1; }

echo "### 1 · El error"
echo "\$ ssh ana@servidor"
docker exec -u ana cliente $SSH ana@servidor hostname 2>&1

echo
echo "### 2 · ¿Hay algo escuchando en el 22?"
echo "\$ nc -zv servidor 22"
C nc -zv -w 5 servidor 22
echo "servidor\$ ss -tlnp"
S ss -tlnp
echo "servidor\$ pgrep -a sshd"
S pgrep -a sshd || echo "(nada)"

echo
echo "### 3 · Arrancar el servicio"
echo "servidor\$ /usr/sbin/sshd   # en una máquina normal: sudo systemctl start ssh"
sshd_con
echo "servidor\$ ss -tlnp | grep sshd"
S ss -tlnp | grep sshd
echo "\$ ssh ana@servidor hostname"
docker exec -u ana cliente $SSH ana@servidor hostname 2>&1

echo
echo "### 4 · sshd escucha en otro puerto"
echo "servidor\$ grep ^Port /etc/ssh/sshd_config"
S sh -c "echo 'Port 2222' >> /etc/ssh/sshd_config"
S grep ^Port /etc/ssh/sshd_config
sshd_con
echo "servidor\$ ss -tlnp | grep sshd"
S ss -tlnp | grep sshd
echo "\$ ssh ana@servidor hostname"
docker exec -u ana cliente $SSH ana@servidor hostname 2>&1
echo "\$ ssh -p 2222 ana@servidor hostname"
docker exec -u ana cliente $SSH -p 2222 ana@servidor hostname 2>&1
S sed -i '/^Port 2222/d' /etc/ssh/sshd_config

echo
echo "### 5 · sshd solo escucha en localhost"
S sh -c "echo 'ListenAddress 127.0.0.1' >> /etc/ssh/sshd_config"
echo "servidor\$ grep ^ListenAddress /etc/ssh/sshd_config"
S grep ^ListenAddress /etc/ssh/sshd_config
sshd_con
echo "servidor\$ ss -tlnp | grep sshd"
S ss -tlnp | grep sshd
echo "\$ ssh ana@servidor hostname"
docker exec -u ana cliente $SSH ana@servidor hostname 2>&1
S sed -i '/^ListenAddress 127.0.0.1/d' /etc/ssh/sshd_config
sshd_con

echo
echo "### 6 · Un firewall que rechaza"
echo "servidor\$ iptables -A INPUT -p tcp --dport 22 -j REJECT --reject-with tcp-reset"
S iptables -A INPUT -p tcp --dport 22 -j REJECT --reject-with tcp-reset
echo "\$ ssh ana@servidor hostname"
docker exec -u ana cliente $SSH ana@servidor hostname 2>&1
echo "servidor\$ ss -tlnp | grep sshd   # sshd sí está escuchando"
S ss -tlnp | grep sshd

echo
echo "### 7 · Un firewall que descarta: otro error"
S iptables -F INPUT
echo "servidor\$ iptables -A INPUT -p tcp --dport 22 -j DROP"
S iptables -A INPUT -p tcp --dport 22 -j DROP
echo "\$ time ssh -o ConnectTimeout=5 ana@servidor hostname"
inicio=$(date +%s)
docker exec -u ana cliente $SSH ana@servidor hostname 2>&1
echo "(tardó $(( $(date +%s) - inicio )) s)"
S iptables -F INPUT

echo
echo "### 8 · Una IP donde no hay nadie"
echo "\$ ssh ana@$IP_VACIA hostname"
docker exec -u ana cliente $SSH ana@$IP_VACIA hostname 2>&1

echo
echo "### 9 · Todo en orden"
echo "\$ nc -zv servidor 22 && ssh ana@servidor hostname"
C nc -zv -w 5 servidor 22
docker exec -u ana cliente $SSH ana@servidor hostname 2>&1
