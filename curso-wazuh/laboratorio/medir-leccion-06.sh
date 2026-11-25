#!/bin/sh
# L06 · un decoder y una regla PROPIOS, para un log que Wazuh no entiende.
#
# ⛔ Todo dentro de los contenedores del laboratorio. Nada fuera.
#
# El encargo pide enseñar el ciclo entero, INCLUIDO el error de sintaxis que tira el manager,
# «porque es lo que va a pasar la primera vez». Así que aquí se provoca a propósito, en este orden:
#   1. la línea sin decoder                  -> No decoder matched
#   2. el decoder MAL escrito                -> qué dice wazuh-logtest / el manager
#   3. el decoder bien, sin regla            -> ya hay campos, pero sigue sin alerta
#   4. la regla                              -> alerta con su nivel
#   5. recargar de verdad y provocarlo en la víctima
export MSYS_NO_PATHCONV=1
cd "$(dirname "$0")"

M="docker exec lab-wazuh-manager"
Mi="docker exec -i lab-wazuh-manager"
V="docker exec lab-wazuh-victima"

LINEA='Aug 27 18:03:11 victima miapp[8123]: LOGIN_FAIL user=ana ip=10.0.0.7 reason=bad_password'

echo "══════════════════════════════════════════════════════════════"
echo " 0 · la línea, tal cual la escribe la app"
echo "══════════════════════════════════════════════════════════════"
echo "  $LINEA"

echo
echo "══════════════════════════════════════════════════════════════"
echo " 1 · sin decoder: hasta dónde llega"
echo "══════════════════════════════════════════════════════════════"
printf '%s\n' "$LINEA" | $Mi /var/ossec/bin/wazuh-logtest 2>&1 | tr -d '\r' | tail -12 | sed 's/^/  /'

echo
echo "══════════════════════════════════════════════════════════════"
echo " 2 · el decoder MAL (falta cerrar una etiqueta) — a propósito"
echo "══════════════════════════════════════════════════════════════"
$M sh -c 'cat > /var/ossec/etc/decoders/local_decoder.xml <<XML
<decoder name="miapp">
  <program_name>miapp</program_name>
</decoder>

<decoder name="miapp-login">
  <parent>miapp</parent>
  <regex>LOGIN_FAIL user=(\w+) ip=(\S+)</regex>
  <order>dstuser, srcip
</decoder>
XML'
echo "  guardado. Y esto dice al probarlo:"
printf '%s\n' "$LINEA" | $Mi /var/ossec/bin/wazuh-logtest 2>&1 | tr -d '\r' | head -14 | sed 's/^/  /'

echo
echo "  ── y esto dice el propio manager al verificar la configuración ──"
$M /var/ossec/bin/wazuh-logtest -t 2>&1 | tr -d '\r' | head -12 | sed 's/^/  /'

echo
echo "══════════════════════════════════════════════════════════════"
echo " 3 · el decoder BIEN, pero todavía sin regla"
echo "══════════════════════════════════════════════════════════════"
$M sh -c 'cat > /var/ossec/etc/decoders/local_decoder.xml <<XML
<decoder name="miapp">
  <program_name>miapp</program_name>
</decoder>

<decoder name="miapp-login">
  <parent>miapp</parent>
  <regex>LOGIN_FAIL user=(\w+) ip=(\S+)</regex>
  <order>dstuser, srcip</order>
</decoder>
XML'
printf '%s\n' "$LINEA" | $Mi /var/ossec/bin/wazuh-logtest 2>&1 | tr -d '\r' | tail -14 | sed 's/^/  /'

echo
echo "══════════════════════════════════════════════════════════════"
echo " 4 · con la regla: ahora sí hay alerta"
echo "══════════════════════════════════════════════════════════════"
$M sh -c 'cat > /var/ossec/etc/rules/local_rules.xml <<XML
<group name="local,miapp,">
  <rule id="100100" level="5">
    <decoded_as>miapp</decoded_as>
    <description>miapp: mensaje de la aplicacion propia</description>
  </rule>

  <rule id="100101" level="7">
    <if_sid>100100</if_sid>
    <regex>LOGIN_FAIL</regex>
    <description>miapp: login fallido de \$(dstuser) desde \$(srcip)</description>
  </rule>

  <rule id="100102" level="10" frequency="5" timeframe="60">
    <if_matched_sid>100101</if_matched_sid>
    <same_srcip />
    <description>miapp: 5 logins fallidos desde la misma IP en 60 s</description>
  </rule>
</group>
XML'
printf '%s\n' "$LINEA" | $Mi /var/ossec/bin/wazuh-logtest 2>&1 | tr -d '\r' | tail -16 | sed 's/^/  /'

echo
echo "══════════════════════════════════════════════════════════════"
echo " 5 · recargar el manager y provocarlo de verdad en la víctima"
echo "══════════════════════════════════════════════════════════════"
t0=$(date +%s)
$M /var/ossec/bin/wazuh-control restart >/dev/null 2>&1
echo "  wazuh-control restart del manager: $(($(date +%s)-t0)) s"
sleep 20
n0=$($M sh -c 'wc -l < /var/ossec/logs/alerts/alerts.log' | tr -d '\r')
echo "  alertas antes: $n0"
echo "  escribiendo 6 LOGIN_FAIL en el syslog de la víctima…"
$V sh -c 'for i in 1 2 3 4 5 6; do
    logger -t miapp "LOGIN_FAIL user=ana ip=10.0.0.7 reason=bad_password"
    sleep 1
  done' >/dev/null 2>&1
i=0
while [ $i -lt 180 ]; do
  if $M sh -c "tail -n +$((n0 + 1)) /var/ossec/logs/alerts/alerts.log | grep -q 'Rule: 1001'" 2>/dev/null; then
    break
  fi
  sleep 3; i=$((i + 3))
done
echo "  reglas propias que saltaron:"
$M sh -c "tail -n +$((n0 + 1)) /var/ossec/logs/alerts/alerts.log \
  | grep -oE \"Rule: 1001[0-9]+ \\(level [0-9]+\\) -> '[^']*'\" | sort | uniq -c" \
  2>&1 | tr -d '\r' | sed 's/^/    /'
echo
echo "  una alerta entera, literal:"
$M sh -c "tail -n +$((n0 + 1)) /var/ossec/logs/alerts/alerts.log | grep -A6 'Rule: 100101' | head -9" \
  2>&1 | tr -d '\r' | sed 's/^/    /'
echo
echo "  y la de correlación (100102), si llegó:"
$M sh -c "tail -n +$((n0 + 1)) /var/ossec/logs/alerts/alerts.log | grep -A6 'Rule: 100102' | head -9" \
  2>&1 | tr -d '\r' | sed 's/^/    /'
