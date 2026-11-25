#!/bin/sh
# Instala el agente de Wazuh en la victima y lo apunta al manager del lab.
# Se ejecuta DENTRO del contenedor: docker exec -i lab-wazuh-victima sh < victima-instalar-agente.sh
set -e
export DEBIAN_FRONTEND=noninteractive
apt-get update -qq
apt-get install -y -qq curl gpg lsb-release apt-transport-https ca-certificates >/dev/null
curl -sS https://packages.wazuh.com/key/GPG-KEY-WAZUH \
  | gpg --no-default-keyring --keyring gnupg-ring:/usr/share/keyrings/wazuh.gpg --import
chmod 644 /usr/share/keyrings/wazuh.gpg
echo "deb [signed-by=/usr/share/keyrings/wazuh.gpg] https://packages.wazuh.com/4.x/apt/ stable main" \
  > /etc/apt/sources.list.d/wazuh.list
apt-get update -qq
# ⚠️ LA VERSION SE FIJA, y no es un detalle. `apt install wazuh-agent` a secas instala la ULTIMA
# del repositorio (4.14.7 el 2026-08-19) y el manager la RECHAZA con:
#     ERROR: Agent version must be lower or equal to manager version (from manager)
# Es un limite duro de Wazuh: el agente nunca puede ser mas nuevo que el manager. Comprobado.
VER=4.9.2-1
# WAZUH_MANAGER hace que el agente se enrole solo contra ese manager al instalarse.
WAZUH_MANAGER="wazuh.manager" WAZUH_AGENT_NAME="victima"   apt-get install -y -qq wazuh-agent="$VER" >/dev/null
/var/ossec/bin/wazuh-control start
sleep 5
/var/ossec/bin/wazuh-control status | head -4
