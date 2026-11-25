#!/bin/sh
# L10 · respuesta activa: que un ataque acabe con la IP bloqueada sin que nadie intervenga.
#
# ⛔⛔ SEGURIDAD, y aquí importa el doble: la respuesta activa BLOQUEA DIRECCIONES. Todo lo de
# este script ocurre dentro de `lab-wazuh-victima`, y la dirección que se bloquea es 127.0.0.1,
# que es la propia víctima atacándose a sí misma. No se toca ninguna dirección real, ni de la red
# de casa ni de internet. Esa es exactamente la razón por la que la lección avisa del peligro:
# una respuesta automática mal puesta bloquea a quien no debe.
#
# ⚠️ El encargo pide enseñar las DOS cosas: funcionando, y el peligro. Aquí se miden las dos.
export MSYS_NO_PATHCONV=1
cd "$(dirname "$0")"

M="docker exec lab-wazuh-manager"
V="docker exec lab-wazuh-victima"

echo "══════════════════════════════════════════════════════════════"
echo " 1 · qué respuestas activas trae de fábrica"
echo "══════════════════════════════════════════════════════════════"
$M sh -c "grep -A6 '<command>' /var/ossec/etc/ossec.conf | head -40" 2>&1 | tr -d '\r' | sed 's/^/  /'
echo
echo "  ¿hay alguna <active-response> ENCENDIDA de fábrica?"
$M sh -c "sed -n '/<active-response>/,/<\\/active-response>/p' /var/ossec/etc/ossec.conf | head -20" \
  2>&1 | tr -d '\r' | sed 's/^/    /'

echo
echo "  los scripts que puede ejecutar el agente:"
$V sh -c 'ls /var/ossec/active-response/bin/ 2>/dev/null' 2>&1 | tr -d '\r' | sed 's/^/    /'

echo
echo "══════════════════════════════════════════════════════════════"
echo " 2 · encenderla para la regla 5763 (fuerza bruta SSH)"
echo "══════════════════════════════════════════════════════════════"
$M sh -c "grep -q 'RESPUESTA-DEL-LABORATORIO' /var/ossec/etc/ossec.conf || \
  sed -i '0,/<\\/ossec_config>/s||  <!-- RESPUESTA-DEL-LABORATORIO -->\\n  <active-response>\\n    <command>firewall-drop</command>\\n    <location>local</location>\\n    <rules_id>5763</rules_id>\\n    <timeout>120</timeout>\\n  </active-response>\\n</ossec_config>|' /var/ossec/etc/ossec.conf"
$M sh -c "sed -n '/RESPUESTA-DEL-LABORATORIO/,/<\\/active-response>/p' /var/ossec/etc/ossec.conf" \
  2>&1 | tr -d '\r' | sed 's/^/  /'
t0=$(date +%s)
$M /var/ossec/bin/wazuh-control restart >/dev/null 2>&1
echo "  reinicio del manager: $(($(date +%s)-t0)) s"
sleep 15

echo
echo "══════════════════════════════════════════════════════════════"
echo " 3 · el estado del cortafuegos ANTES"
echo "══════════════════════════════════════════════════════════════"
$V sh -c 'iptables -L INPUT -n 2>/dev/null || echo "    iptables no disponible en la victima"' \
  2>&1 | tr -d '\r' | sed 's/^/  /'
$V sh -c 'wc -l < /var/ossec/logs/active-responses.log 2>/dev/null || echo 0' \
  2>&1 | tr -d '\r' | sed 's/^/  lineas en active-responses.log: /'

echo
echo "══════════════════════════════════════════════════════════════"
echo " 4 · provocar la fuerza bruta y ver si actúa solo"
echo "══════════════════════════════════════════════════════════════"
n0=$($M sh -c 'wc -l < /var/ossec/logs/alerts/alerts.log' | tr -d '\r')
echo "  alertas antes: $n0"
$V sh -c 'for i in 1 2 3 4 5 6 7 8 9 10; do
    (sleep 0.2; echo "malaclave$i") | timeout 8 ssh -o StrictHostKeyChecking=no \
       -o PreferredAuthentications=password -o PubkeyAuthentication=no \
       becario@127.0.0.1 exit >/dev/null 2>&1
  done; true' >/dev/null 2>&1
echo "  10 intentos lanzados. Esperando a la 5763 y a la respuesta…"
i=0
while [ $i -lt 200 ]; do
  if $M sh -c "tail -n +$((n0 + 1)) /var/ossec/logs/alerts/alerts.log | grep -q 'Rule: 5763'" 2>/dev/null; then
    break
  fi
  sleep 5; i=$((i + 5))
done
echo "  la 5763 saltó a los ~$i s"
sleep 20

echo
echo "  lo que escribió la respuesta activa:"
$V sh -c 'tail -6 /var/ossec/logs/active-responses.log 2>/dev/null || echo "    (nada)"' \
  2>&1 | tr -d '\r' | sed 's/^/    /'
echo
echo "  el cortafuegos DESPUÉS:"
$V sh -c 'iptables -L INPUT -n 2>/dev/null || echo "    iptables no disponible"' \
  2>&1 | tr -d '\r' | sed 's/^/    /'
echo
echo "  las alertas de respuesta activa que llegaron al servidor:"
$M sh -c "tail -n +$((n0 + 1)) /var/ossec/logs/alerts/alerts.log \
  | grep -oE \"Rule: [0-9]+ \\(level [0-9]+\\) -> '[^']*'\" | sort | uniq -c | head -10" \
  2>&1 | tr -d '\r' | sed 's/^/    /'

echo
echo "══════════════════════════════════════════════════════════════"
echo " 5 · EL PELIGRO, medido: se desbloquea solo a los 120 s"
echo "══════════════════════════════════════════════════════════════"
echo "  esperando al timeout que puse (120 s)…"
sleep 130
$V sh -c 'iptables -L INPUT -n 2>/dev/null | head -8' 2>&1 | tr -d '\r' | sed 's/^/    /'
$V sh -c 'tail -4 /var/ossec/logs/active-responses.log 2>/dev/null' 2>&1 | tr -d '\r' | sed 's/^/    /'
