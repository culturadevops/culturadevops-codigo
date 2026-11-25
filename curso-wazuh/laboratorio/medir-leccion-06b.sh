#!/bin/sh
# L06 (segunda parte) · el eslabón que faltaba: NADIE ESTABA LEYENDO EL FICHERO.
#
# ⚠️ LO QUE PASÓ, y por eso existe este script: con el decoder bien, la regla bien y
# `wazuh-logtest` diciendo «Alert to be generated», al provocarlo de verdad en la víctima NO llegó
# ni una alerta. El motivo no estaba ni en el decoder ni en la regla: `logger` escribe en
# `/var/log/syslog`, y el agente solo vigilaba auth.log, dpkg.log y active-responses.log.
#
# Es el mismo tropiezo de la lección 03 (el agente vigila lo que existía al instalarlo) apareciendo
# en otro sitio, y va DENTRO del vídeo.
#
# ⛔ Todo dentro de los contenedores del laboratorio.
export MSYS_NO_PATHCONV=1
cd "$(dirname "$0")"

M="docker exec lab-wazuh-manager"
V="docker exec lab-wazuh-victima"

echo "══════════════════════════════════════════════════════════════"
echo " 0 · la prueba de que el problema NO era la regla"
echo "══════════════════════════════════════════════════════════════"
echo "  la línea SÍ se escribió, pero en syslog:"
$V sh -c 'grep miapp /var/log/syslog | tail -2' 2>&1 | tr -d '\r' | sed 's/^/    /'
echo "  y esto es todo lo que el agente vigilaba:"
$V sh -c "grep -oE '<location>[^<]*</location>' /var/ossec/etc/ossec.conf" 2>&1 | tr -d '\r' | sed 's/^/    /'

echo
echo "══════════════════════════════════════════════════════════════"
echo " 1 · añadir /var/log/syslog a lo que vigila el agente"
echo "══════════════════════════════════════════════════════════════"
# ⚠️ Se inserta antes del PRIMER </ossec_config>, no sustituyendo todos: ese fichero tiene más de
# un cierre de bloque y sustituirlos todos mete el bloque varias veces (tropiezo de la lección 03).
$V sh -c "grep -q '/var/log/syslog' /var/ossec/etc/ossec.conf || \
  sed -i '0,/<\\/ossec_config>/s||  <localfile>\\n    <log_format>syslog</log_format>\\n    <location>/var/log/syslog</location>\\n  </localfile>\\n</ossec_config>|' /var/ossec/etc/ossec.conf"
$V sh -c "grep -oE '<location>[^<]*</location>' /var/ossec/etc/ossec.conf" 2>&1 | tr -d '\r' | sed 's/^/    /'

echo
echo "══════════════════════════════════════════════════════════════"
echo " 2 · reiniciar el agente (esto tarda: medido en la lección 03)"
echo "══════════════════════════════════════════════════════════════"
t0=$(date +%s)
$V /var/ossec/bin/wazuh-control restart >/dev/null 2>&1
echo "  wazuh-control restart del agente: $(($(date +%s)-t0)) s"
echo "  y ahora sí lo tiene en su lista de análisis:"
$V sh -c "grep 'Analyzing file' /var/ossec/logs/ossec.log | tail -5" 2>&1 | tr -d '\r' | sed 's/^/    /'

echo
echo "══════════════════════════════════════════════════════════════"
echo " 3 · repetir los 6 LOGIN_FAIL, ahora que hay quien los lea"
echo "══════════════════════════════════════════════════════════════"
n0=$($M sh -c 'wc -l < /var/ossec/logs/alerts/alerts.log' | tr -d '\r')
echo "  alertas antes: $n0"
t0=$(date +%s)
$V sh -c 'for i in 1 2 3 4 5 6; do
    logger -t miapp "LOGIN_FAIL user=ana ip=10.0.0.7 reason=bad_password"
    sleep 1
  done' >/dev/null 2>&1
i=0
while [ $i -lt 240 ]; do
  if $M sh -c "tail -n +$((n0 + 1)) /var/ossec/logs/alerts/alerts.log | grep -q 'Rule: 1001'" 2>/dev/null; then
    break
  fi
  sleep 3; i=$((i + 3))
done
echo "  la primera alerta propia llegó a los: $(($(date +%s)-t0)) s"
echo
echo "  reglas propias que saltaron:"
$M sh -c "tail -n +$((n0 + 1)) /var/ossec/logs/alerts/alerts.log \
  | grep -oE \"Rule: 1001[0-9]+ \\(level [0-9]+\\) -> '[^']*'\" | sort | uniq -c" \
  2>&1 | tr -d '\r' | sed 's/^/    /'
echo
echo "  la alerta de login fallido, entera:"
$M sh -c "tail -n +$((n0 + 1)) /var/ossec/logs/alerts/alerts.log | grep -B2 -A6 'Rule: 100101' | head -11" \
  2>&1 | tr -d '\r' | sed 's/^/    /'
echo
echo "  y la de correlación, la 100102:"
$M sh -c "tail -n +$((n0 + 1)) /var/ossec/logs/alerts/alerts.log | grep -B2 -A6 'Rule: 100102' | head -11" \
  2>&1 | tr -d '\r' | sed 's/^/    /'
