#!/bin/sh
# Prepara la victima para que produzca logs de VERDAD.
#
# ⚠️ Un `ubuntu:24.04` pelado NO tiene syslog ni SSH: `logger` escribe al vacio y `/var/log/auth.log`
# no existe. Sin esto, las lecciones 07 y 08 (FIM y fuerza bruta SSH) no tienen de donde salir.
# Comprobado el 2026-08-19: los eventos provocados a mano no generaron ninguna alerta.
set -e
export DEBIAN_FRONTEND=noninteractive
apt-get update -qq
apt-get install -y -qq openssh-server rsyslog >/dev/null
mkdir -p /run/sshd
# Un usuario con contrasena floja, A PROPOSITO: es el objetivo de la demo de fuerza bruta.
id becario >/dev/null 2>&1 || useradd -m -s /bin/bash becario
echo 'becario:becario123' | chpasswd
sed -i 's/^#*PermitRootLogin.*/PermitRootLogin no/' /etc/ssh/sshd_config
service rsyslog start >/dev/null 2>&1 || rsyslogd
/usr/sbin/sshd
sleep 2
echo "sshd:   $(pgrep -c sshd) proceso(s)"
echo "rsyslog:$(pgrep -c rsyslogd) proceso(s)"
ls -l /var/log/auth.log 2>/dev/null || echo "auth.log todavia vacio (se crea al primer intento)"
