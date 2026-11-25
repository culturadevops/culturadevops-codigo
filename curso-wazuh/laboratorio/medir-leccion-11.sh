#!/bin/sh
# L11 · SCA contra CIS. Segunda parte: hacer que la política se aplique de verdad.
#
# ⛔ Todo dentro de los contenedores del laboratorio.
#
# ⚠️ LO MEDIDO ANTES: el agente carga la ÚNICA política que trae (`cis_ubuntu22-04.yml`, 182
# comprobaciones), comprueba la versión del sistema, ve que la víctima es Ubuntu 24.04, y la
# descarta:
#     sca: INFO: Skipping policy '.../cis_ubuntu22-04.yml': 'Check Ubuntu version.'
#     sca: INFO: Security Configuration Assessment scan finished. Duration: 0 seconds.
# Cero comprobaciones, cero avisos, y en nivel INFO. Nadie te dice que tu evaluación de
# configuración no está evaluando nada.
#
# Aquí se hace lo que haría cualquiera: copiar la política y ajustar la condición de versión.
# ⚠️ Esto NO convierte la política del 22.04 en una del 24.04: son comprobaciones escritas para
# otra versión y algunas no aplican. Se hace para VER el mecanismo funcionando, y el vídeo lo dice
# con esas palabras. No se presenta como una auditoría CIS válida.
export MSYS_NO_PATHCONV=1
cd "$(dirname "$0")"

M="docker exec lab-wazuh-manager"
V="docker exec lab-wazuh-victima"

echo "══════════════════════════════════════════════════════════════"
echo " 1 · la condición que la descarta, tal cual está escrita"
echo "══════════════════════════════════════════════════════════════"
$V sh -c "sed -n '1,30p' /var/ossec/ruleset/sca/cis_ubuntu22-04.yml" 2>&1 | tr -d '\r' | sed 's/^/  /'

echo
echo "══════════════════════════════════════════════════════════════"
echo " 2 · copiarla y ajustar la condición de versión"
echo "══════════════════════════════════════════════════════════════"
$V sh -c "cp /var/ossec/ruleset/sca/cis_ubuntu22-04.yml /var/ossec/ruleset/sca/lab_ubuntu24-04.yml && \
  sed -i 's/22\\.04/24.04/g; s|cis_ubuntu22-04|lab_ubuntu24-04|g' /var/ossec/ruleset/sca/lab_ubuntu24-04.yml && \
  chown root:wazuh /var/ossec/ruleset/sca/lab_ubuntu24-04.yml && \
  ls -la /var/ossec/ruleset/sca/"
$V sh -c "sed -n '1,25p' /var/ossec/ruleset/sca/lab_ubuntu24-04.yml" 2>&1 | tr -d '\r' | sed 's/^/  /'

echo
echo "══════════════════════════════════════════════════════════════"
echo " 3 · reiniciar el agente (los 5 minutos de siempre)"
echo "══════════════════════════════════════════════════════════════"
t0=$(date +%s)
$V /var/ossec/bin/wazuh-control restart >/dev/null 2>&1
echo "  reinicio del agente: $(($(date +%s)-t0)) s"
sleep 30
echo "  qué dice ahora el módulo:"
$V sh -c "grep -i 'sca' /var/ossec/logs/ossec.log | tail -10" 2>&1 | tr -d '\r' | sed 's/^/    /'

echo
echo "══════════════════════════════════════════════════════════════"
echo " 4 · la nota: cuántas pasa y cuántas falla"
echo "══════════════════════════════════════════════════════════════"
n0=$($M sh -c 'wc -l < /var/ossec/logs/alerts/alerts.log' | tr -d '\r')
i=0
while [ $i -lt 240 ]; do
  if $V sh -c "grep -q 'Security Configuration Assessment scan finished' /var/ossec/logs/ossec.log" 2>/dev/null; then
    break
  fi
  sleep 10; i=$((i + 10))
done
echo "  resumen del escaneo, en el log del agente:"
$V sh -c "grep -iE 'sca:.*(finished|Starting Security|Skipping)' /var/ossec/logs/ossec.log | tail -4" \
  2>&1 | tr -d '\r' | sed 's/^/    /'
echo
echo "  alertas de SCA que llegaron al servidor:"
$M sh -c "grep -oE \"Rule: [0-9]+ \\(level [0-9]+\\) -> '[^']*'\" /var/ossec/logs/alerts/alerts.log \
  | grep -iE 'sca|configuration' | sort | uniq -c | head -8" 2>&1 | tr -d '\r' | sed 's/^/    /'
echo
echo "  y el resumen que manda el agente, si llegó:"
$M sh -c "grep -A10 'sca' /var/ossec/logs/alerts/alerts.log | grep -iE 'score|passed|failed|policy' | tail -8" \
  2>&1 | tr -d '\r' | sed 's/^/    /'
