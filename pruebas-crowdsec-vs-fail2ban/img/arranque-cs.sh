#!/bin/sh
# Arranque del servidor con CrowdSec (sin systemd): sshd, el agente + API local, y el bloqueador de iptables.
/usr/sbin/sshd
crowdsec -c /etc/crowdsec/config.yaml >/var/log/crowdsec-proceso.log 2>&1 &
for i in $(seq 1 60); do cscli lapi status >/dev/null 2>&1 && break; sleep 1; done
exec crowdsec-firewall-bouncer -c /etc/crowdsec/bouncers/crowdsec-firewall-bouncer.yaml
