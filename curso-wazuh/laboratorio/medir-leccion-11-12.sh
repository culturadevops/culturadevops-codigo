#!/bin/sh
# L11 · SCA contra CIS   y   L12 · vulnerabilidades y su ruido.
#
# ⛔ Todo dentro de los contenedores del laboratorio.
#
# ⚠️ YA SÉ QUE HAY UN PROBLEMA CON EL SCA, y por eso este script lo mira de frente: en el log del
# agente salía «Skipping policy '/var/ossec/ruleset/sca/cis_ubuntu22-04.yml': 'Check Ubuntu
# version.'». La víctima es ubuntu:24.04 y la política que trae es para 22.04. O aparece una
# política válida, o la lección cuenta ESO, que es lo que le pasa a cualquiera.
export MSYS_NO_PATHCONV=1
cd "$(dirname "$0")"

M="docker exec lab-wazuh-manager"
V="docker exec lab-wazuh-victima"

echo "══════════════════════════════════════════════════════════════"
echo " L11 · qué políticas de SCA trae el agente"
echo "══════════════════════════════════════════════════════════════"
$V sh -c 'ls -la /var/ossec/ruleset/sca/ 2>/dev/null' 2>&1 | tr -d '\r' | sed 's/^/  /'
echo
echo "  la versión real de la víctima:"
$V sh -c 'cat /etc/os-release | head -3' 2>&1 | tr -d '\r' | sed 's/^/    /'
echo
echo "  qué dijo el agente al intentar pasarla:"
$V sh -c "grep -i 'sca' /var/ossec/logs/ossec.log | tail -8" 2>&1 | tr -d '\r' | sed 's/^/    /'

echo
echo "══════════════════════════════════════════════════════════════"
echo " L11 · cuántas comprobaciones tiene la política, y de qué van"
echo "══════════════════════════════════════════════════════════════"
$V sh -c 'p=$(ls /var/ossec/ruleset/sca/*.yml 2>/dev/null | head -1); \
  echo "  fichero: $p"; \
  echo "  comprobaciones: $(grep -c "^  - id:" "$p" 2>/dev/null)"; \
  echo "  ejemplos de título:"; \
  grep -A1 "^  - id:" "$p" 2>/dev/null | grep "title:" | head -5' \
  2>&1 | tr -d '\r' | sed 's/^/  /'

echo
echo "══════════════════════════════════════════════════════════════"
echo " L11 · resultados del SCA en la base del agente"
echo "══════════════════════════════════════════════════════════════"
$M sh -c "sqlite3 /var/ossec/queue/db/005.db \
  'SELECT result, COUNT(*) FROM sca_check GROUP BY result;' 2>/dev/null" \
  2>&1 | tr -d '\r' | sed 's/^/  /'
$M sh -c "sqlite3 /var/ossec/queue/db/005.db \
  'SELECT policy_id, pass, fail, invalid, score FROM sca_policy;' 2>/dev/null" \
  2>&1 | tr -d '\r' | sed 's/^/  /'
echo "  (si sqlite3 no está, se dice y punto: no se inventa la nota)"

echo
echo "══════════════════════════════════════════════════════════════"
echo " L12 · el módulo de vulnerabilidades: ¿está encendido?"
echo "══════════════════════════════════════════════════════════════"
$M sh -c "grep -A4 'vulnerability-detection' /var/ossec/etc/ossec.conf | head -8" \
  2>&1 | tr -d '\r' | sed 's/^/  /'

echo
echo "  lo que ocupa su catálogo (el dato de la lección 13):"
$M sh -c 'du -sh /var/ossec/queue/vd /var/ossec/queue/vd_updater 2>/dev/null' \
  2>&1 | tr -d '\r' | sed 's/^/    /'

echo
echo "  qué dice el manager sobre el módulo:"
$M sh -c "grep -iE 'vulnerability|vd_updater' /var/ossec/logs/ossec.log | tail -8" \
  2>&1 | tr -d '\r' | sed 's/^/    /'

echo
echo "══════════════════════════════════════════════════════════════"
echo " L12 · cuántos paquetes hay que analizar, y cuántos CVE salieron"
echo "══════════════════════════════════════════════════════════════"
$M sh -c "sqlite3 /var/ossec/queue/db/005.db \
  'SELECT COUNT(*) FROM sys_programs;' 2>/dev/null" 2>&1 | tr -d '\r' | sed 's/^/  paquetes inventariados: /'
$M sh -c "sqlite3 /var/ossec/queue/db/005.db \
  'SELECT severity, COUNT(*) FROM vuln_cves GROUP BY severity;' 2>/dev/null" \
  2>&1 | tr -d '\r' | sed 's/^/  CVE por severidad: /'
echo
echo "  alertas de vulnerabilidad que hayan llegado:"
$M sh -c "grep -oE \"Rule: [0-9]+ \\(level [0-9]+\\) -> '[^']*[Vv]ulnerab[^']*'\" \
  /var/ossec/logs/alerts/alerts.log | sort | uniq -c | head -8" 2>&1 | tr -d '\r' | sed 's/^/    /'
