#!/bin/sh
# Cronometra un arranque EN FRÍO del laboratorio, midiendo hasta que cada pieza CONTESTA,
# no hasta que Docker dice «Started».
#
# ⚠️ La diferencia no es cosmética: `docker compose up` vuelve en segundos y el indexer tarda
# minutos en aceptar una consulta. Medir lo primero y llamarlo «arranque» es el error clásico.
#
# ⛔ No borra el volumen de datos: `down` sin `-v`. Las alertas acumuladas son el dato de la
# lección 05 y no se tiran para cronometrar.
#
# ⚠️ Git Bash reescribe las rutas absolutas de los `docker exec`: `/var/ossec/bin/agent_control`
# le llega al contenedor como `C:/Program Files/Git/var/ossec/...` y el exec falla PARA SIEMPRE
# — el bucle de espera se queda dando vueltas sin marcar nada. `MSYS_NO_PATHCONV=1` lo apaga.
#
#   sh cronometrar-arranque.sh
export MSYS_NO_PATHCONV=1
export MSYS2_ARG_CONV_EXCL="*"
set -e
cd "$(dirname "$0")"

t0=$(date +%s)
marca() { echo "  $1: $(( $(date +%s) - t0 )) s"; }

echo "== parando (sin borrar datos) =="
docker compose down >/dev/null 2>&1

echo "== arranque en frío =="
t0=$(date +%s)
docker compose up -d >/dev/null 2>&1
marca "docker dice Started"

# 1) el indexer acepta una consulta autenticada
while ! docker exec lab-wazuh-indexer curl -sk -u admin:SecretPassword \
        https://localhost:9200/_cluster/health >/dev/null 2>&1; do sleep 2; done
marca "el indexer contesta"

# 2) el manager tiene su API en pie
while ! docker exec lab-wazuh-manager /var/ossec/bin/agent_control -l >/dev/null 2>&1; do sleep 2; done
marca "el manager contesta"

# 3) el dashboard sirve la página
# ⚠️ DENTRO del contenedor escucha en el 443, no en el 5601: lo dice su propio `server.port`.
# El 5601 es solo el puerto publicado hacia el anfitrión.
while [ "$(docker exec lab-wazuh-dashboard curl -sk -o /dev/null -w '%{http_code}' \
           https://localhost:443/app/login 2>/dev/null)" != "200" ]; do sleep 2; done
marca "el dashboard sirve la página (dentro, puerto 443)"

# 3b) y desde fuera, que es donde lo vas a abrir tú
while [ "$(curl -sk -o /dev/null -w '%{http_code}' -m 5 https://localhost:5601/app/login 2>/dev/null)" != "200" ]; do sleep 2; done
marca "se abre desde el navegador"

# 4) y lo que de verdad importa: que una alerta llegue al almacén
n0=$(docker exec lab-wazuh-indexer curl -sk -u admin:SecretPassword \
     "https://localhost:9200/wazuh-alerts-*/_count" 2>/dev/null | sed 's/.*"count":\([0-9]*\).*/\1/')
echo "  alertas en el almacén al arrancar: ${n0:-0}"
