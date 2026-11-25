#!/bin/sh
# L12 · vulnerabilidades y su ruido.
#
# ⛔ Todo dentro de los contenedores del laboratorio.
#
# ⚠️ LO QUE ENCONTRÉ ANTES DE PODER MEDIR NADA, y que es la mitad de la lección:
# el módulo llevaba días encendido, con 9,3 GB de catálogo descargado, y NO había producido ni un
# solo hallazgo. El motivo estaba en una línea del log del manager, en nivel WARNING, una sola vez
# por arranque:
#     indexer-connector: WARNING: IndexerConnector initialization failed for index
#     'wazuh-states-vulnerabilities-wazuh.manager', retrying until the connection is successful.
# Y la causa, en su ossec.conf:  <host>https://0.0.0.0:9200</host>
# Desde dentro del contenedor del manager, 0.0.0.0 es él mismo, y ahí no escucha nadie. El
# almacén está en `https://wazuh.indexer:9200` (comprobado con curl: contesta y da la versión).
#
# Es EXACTAMENTE el mismo fallo que la lección 02 enseñó con el panel: buscar el almacén en su
# propio localhost. Por eso va en el vídeo.
export MSYS_NO_PATHCONV=1
cd "$(dirname "$0")"

M="docker exec lab-wazuh-manager"

echo "══════════════════════════════════════════════════════════════"
echo " 1 · antes: el índice de vulnerabilidades no existe"
echo "══════════════════════════════════════════════════════════════"
docker exec lab-wazuh-indexer sh -c \
  'curl -s -k -u admin:SecretPassword "https://localhost:9200/_cat/indices?h=index" | grep -c vulnerabilit' \
  2>&1 | tr -d '\r' | sed 's/^/  índices de vulnerabilidades: /'

echo
echo "══════════════════════════════════════════════════════════════"
echo " 2 · arreglar el destino y reiniciar"
echo "══════════════════════════════════════════════════════════════"
$M sh -c "sed -i 's|<host>https://0.0.0.0:9200</host>|<host>https://wazuh.indexer:9200</host>|' /var/ossec/etc/ossec.conf"
$M sh -c "sed -n '/<indexer>/,/<\\/indexer>/p' /var/ossec/etc/ossec.conf | head -6" 2>&1 | tr -d '\r' | sed 's/^/  /'
t0=$(date +%s)
$M /var/ossec/bin/wazuh-control restart >/dev/null 2>&1
echo "  reinicio del manager: $(($(date +%s)-t0)) s"

echo
echo "══════════════════════════════════════════════════════════════"
echo " 3 · ¿sigue quejándose el conector?"
echo "══════════════════════════════════════════════════════════════"
sleep 60
$M sh -c "grep 'indexer-connector' /var/ossec/logs/ossec.log | tail -4" 2>&1 | tr -d '\r' | sed 's/^/  /'

echo
echo "══════════════════════════════════════════════════════════════"
echo " 4 · esperar al escaneo y contar CVE de verdad"
echo "══════════════════════════════════════════════════════════════"
i=0
while [ $i -lt 420 ]; do
  n=$(docker exec lab-wazuh-indexer sh -c \
    'curl -s -k -u admin:SecretPassword "https://localhost:9200/_cat/indices?h=index" | grep -c vulnerabilit' \
    2>/dev/null | tr -d '\r')
  if [ "${n:-0}" -gt 0 ]; then break; fi
  sleep 15; i=$((i + 15))
done
echo "  el índice aparece a los ~$i s"
docker exec lab-wazuh-indexer sh -c \
  'curl -s -k -u admin:SecretPassword "https://localhost:9200/_cat/indices?v&h=index,docs.count,store.size" | grep vulnerabilit' \
  2>&1 | tr -d '\r' | sed 's/^/  /'

echo
echo "  CVE por severidad:"
docker exec lab-wazuh-indexer sh -c \
  'curl -s -k -u admin:SecretPassword -H "Content-Type: application/json" \
   "https://localhost:9200/wazuh-states-vulnerabilities-*/_search?size=0" -d "{\"aggs\":{\"sev\":{\"terms\":{\"field\":\"vulnerability.severity\",\"size\":10}}}}"' \
  2>&1 | tr -d '\r' | sed 's/^/    /' | head -20

echo
echo "  cuántos son, en total:"
docker exec lab-wazuh-indexer sh -c \
  'curl -s -k -u admin:SecretPassword "https://localhost:9200/wazuh-states-vulnerabilities-*/_count"' \
  2>&1 | tr -d '\r' | sed 's/^/    /'

echo
echo "  tres ejemplos, para poder leerlos en pantalla:"
docker exec lab-wazuh-indexer sh -c \
  'curl -s -k -u admin:SecretPassword \
   "https://localhost:9200/wazuh-states-vulnerabilities-*/_search?size=3&_source=vulnerability.id,vulnerability.severity,package.name,package.version"' \
  2>&1 | tr -d '\r' | sed 's/^/    /' | head -20
